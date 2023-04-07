import asyncio
import functools
import itertools
import uuid
import weakref
from collections import deque
from html import escape
from typing import Callable, List, Tuple, Set, Optional, Union

import fastapi
from fastapi import APIRouter
from fastapi.responses import RedirectResponse, HTMLResponse

from . import js


router = APIRouter()

CALLBACK_URL = "/callback"
POLL_URL = "/poll"

# Maximum number of updates that are retained. A client falling befhind by more
# than this will be forced to reload the page.
MAX_UPDATES = 3


class _Hook:
    # note: __weakref__ required to support weak references with __slots__
    __slots__ = ["index", "key", "_html", "render_func", "__weakref__"]
    _stale_hooks = set()
    _updates = deque()
    _update_offs: int = 0

    @staticmethod
    def push_updates() -> None:
        if len(_Hook._stale_hooks) > 0:
            _Hook._updates.append(
                tuple(
                    (h().key, h().index, h().html)
                    for h in _Hook._stale_hooks
                    if h() is not None
                )
            )

            _Hook._stale_hooks = set()

            if len(_Hook._updates) > MAX_UPDATES:
                _Hook._updates.popleft()
                _Hook._update_offs += 1

    @staticmethod
    def _concat(html: List[Union[str, "_Hook"]]) -> List[Union[str, "_Hook"]]:
        # Group consecutive elements by their type
        groups = itertools.groupby(html, key=type)

        return [
            "".join(group) if key == str else element
            for key, group in groups
            for element in (group if key != str else [group])
        ]

    def __init__(
        self,
        html: List[Union[str, "_Hook"]],
        render_func: Optional[Callable[[], List[Union[str, "_Hook"]]]] = None,
    ) -> None:
        self.render_func = render_func

        self._html: List[Union[str, "_Hook"]] = _Hook._concat(html)

        self.index: Optional[int] = None
        self.key: Optional[str] = None

    def flush(self) -> None:
        self._html = []
        _Hook._stale_hooks.add(weakref.ref(self))

    def __str__(self) -> str:
        if len(self._html) == 0 and self.render_func is not None:
            result = self.render_func()
            self._html = _Hook._concat(result)

        return "".join(str(h) for h in self._html)

    @property
    def html(self) -> str:
        return str(self)

    @property
    def children(self) -> List["_Hook"]:
        return [c for c in self._html if isinstance(c, _Hook)]


def _factory(tag_name, allow_children=True):
    def _impl(*children, **attributes):
        if "children" in attributes:
            if len(children) != 0:
                raise ValueError(
                    f"<{tag_name} /> Cannot pass children as both a positional argument and a keyword argument"
                )
            children = attributes.pop("children")
        elif len(children) == 1 and isinstance(children[0], list):
            children = children[0]
        if not allow_children and children:
            raise ValueError(f"<{tag_name} /> cannot have children")

        if allow_children:
            result = []
            # pre-allocated key for just in case
            key = uuid.uuid4().hex[:8]
            have_hook = False
            for idx, c in enumerate(children):
                if type(c) == _Hook and c.key is None:
                    c.index = idx
                    c.key = key
                    result.append(c)
                    have_hook = True
                elif isinstance(c, list):
                    result += c
                else:
                    result.append(c)

            if have_hook:
                attributes["key"] = str(key)

            attributes = [
                f"{k}" if isinstance(v, bool) and v else f'{k}="{escape(v)}"'
                for k, v in sorted(attributes.items())
            ]
            return (
                [f"<{tag_name} " if attributes else f"<{tag_name}"]
                + [" ".join(attributes)]
                + [">"]
                + result
                + [f"</{tag_name}>"]
            )
        else:
            attributes = [
                f"{k}" if isinstance(v, bool) and v else f'{k}="{escape(v)}"'
                for k, v in sorted(attributes.items())
            ]
            return (
                [f"<{tag_name} " if attributes else f"<{tag_name}"]
                + [" ".join(attributes)]
                + [" />"]
            )

    return _impl


_hook_stack = []


def hook(*dec_args, **dec_kwargs):
    if len(dec_args) == 1 and callable(dec_args[0]):

        @functools.wraps(dec_args[0])
        def _impl(*args, **kwargs):
            _hook_stack.append(set())
            value = dec_args[0](*args, **kwargs)
            func = functools.partial(dec_args[0], *args, **kwargs)
            result = _Hook(value, render_func=func)
            for c in _hook_stack.pop():
                c.hooks.add(weakref.ref(result))
            return result

        return _impl
    elif "render" in dec_kwargs and dec_kwargs["render"]:

        def _dec_impl(fn):
            @functools.wraps(fn)
            def _impl2():
                # _impl has a hook attribute so we maintain a reference
                if not hasattr(_impl2, "body"):
                    _impl2.body = _Hook._concat(_factory("body")(fn()))
                result = js.render(
                    CALLBACK_URL,
                    POLL_URL,
                    _Hook._update_offs + len(_Hook._updates),
                    "".join((str(b) for b in _impl2.body)),
                )

                return HTMLResponse(content=result, status_code=200)

            fn = hook(fn)

            return _impl2

        return _dec_impl
    else:
        raise ValueError("Invalid hook decorator")


class State(object):
    __slots__ = ["_value", "hooks", "_lock"]

    def __init__(self, initial_value):
        self._value = initial_value
        self.hooks = set()
        self._lock = asyncio.Lock()

    @property
    def value(self):
        if len(_hook_stack) > 0:
            _hook_stack[-1].add(self)
        return self._value

    @value.setter
    def value(self, value):
        # assert (
        #     len(_hook_stack) == 0
        # ), "Don't update context values from within render hooks"
        for h in self.hooks:
            if h() is not None:
                h().flush()
        self._value = value


_callback_map = {}


def callback(*dec_args, **dec_kwargs):
    if len(dec_args) == 1 and callable(dec_args[0]):
        id = uuid.uuid4().hex[:8]
        _callback_map[id] = dec_args[0]
        return f'return python("{id}")(arguments[0])'
    elif "confirm" in dec_kwargs:
        confirm = dec_kwargs["confirm"]
        confirm = 1 if isinstance(confirm, bool) and confirm else confirm

        def _dec_impl(fn):
            id = uuid.uuid4().hex[:8]
            _callback_map[id] = fn
            return f'return confirm("{id}", {confirm})(arguments[0])'

        return _dec_impl
    else:
        raise ValueError("Invalid callback decorator")


@router.post(CALLBACK_URL)
async def _callback(
    id: str = fastapi.Body(embed=True),
    event: dict = fastapi.Body(embed=True),
):
    if id in _callback_map:
        _callback_map[id](event)
        _Hook.push_updates()

        return dict(
            state=_Hook._update_offs + len(_Hook._updates), updates=_Hook._updates[-1]
        )

    root = "/"
    response = RedirectResponse(url=root)
    response.status_code = 302
    return response


@router.get(POLL_URL)
async def _poll(state: int):
    _Hook.push_updates()

    if state >= _Hook._update_offs + len(_Hook._updates):
        return dict(state=state, updates=[])

    if state < _Hook._update_offs:
        root = "/"
        response = RedirectResponse(url=root)
        response.status_code = 302
        return response

    flat_updates = [
        u
        for updates in itertools.islice(
            _Hook._updates, state - _Hook._update_offs, None
        )
        for u in updates
    ]

    return dict(state=_Hook._update_offs + len(_Hook._updates), updates=flat_updates)
