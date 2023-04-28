import asyncio
import functools
import itertools
import uuid
import weakref
from collections import deque
from html import escape
from typing import Callable, List, Optional, Union
import time

import fastapi
from fastapi import APIRouter
from fastapi.responses import JSONResponse, HTMLResponse

from . import js


router = APIRouter()

CALLBACK_URL = "/callback"
EFFECTS_URL = "/effects"
LOG_URL = "/log"

# Maximum number of updates that are retained. A client falling befhind by more
# than this will be forced to reload the page.
BACKLOG_LEN = 5


_sync_condition = None
_session_id = uuid.uuid4().hex[:8]

async def sync_effects() -> None:
    global _sync_condition

    if _sync_condition is None:
        _sync_condition = asyncio.Condition()

    async with _sync_condition:
        _Effect.push_updates()
        _sync_condition.notify_all()


class _Effect:
    # note: __weakref__ required to support weak references with __slots__
    __slots__ = ["index", "key", "_html", "render_func", "__weakref__"]
    _stale_effects = set()
    # backlog of consolidated effects - limited to BACKLOG_LEN
    _backlog = deque()
    _backlog_offs: int = 0

    @staticmethod
    def push_updates() -> None:
        if len(_Effect._stale_effects) > 0:
            _Effect._backlog.append(
                tuple(
                    (h().key, h().index, h().html)
                    for h in _Effect._stale_effects
                    if h() is not None
                )
            )

            _Effect._stale_effects = set()

            if len(_Effect._backlog) > BACKLOG_LEN:
                _Effect._backlog.popleft()
                _Effect._backlog_offs += 1

    @staticmethod
    def _concat(html: List[Union[str, "_Effect"]]) -> List[Union[str, "_Effect"]]:
        # Group consecutive elements by their type
        groups = itertools.groupby(html, key=type)

        return [
            "".join(group) if key == str else element
            for key, group in groups
            for element in (group if key != str else [group])
        ]

    def __init__(
        self,
        html: List[Union[str, "_Effect"]],
        render_func: Optional[Callable[[], List[Union[str, "_Effect"]]]] = None,
    ) -> None:
        self.render_func = render_func

        self._html: List[Union[str, "_Effect"]] = _Effect._concat(html)

        self.index = None
        self.key = None

    def flush(self) -> None:
        self._html = []
        _Effect._stale_effects.add(weakref.ref(self))

    def __str__(self) -> str:
        if len(self._html) == 0 and self.render_func is not None:
            result = self.render_func()
            self._html = _Effect._concat(result)

        return "".join(str(h) for h in self._html)

    @property
    def html(self) -> str:
        return str(self)

    @property
    def children(self) -> List["_Effect"]:
        return [c for c in self._html if isinstance(c, _Effect)]


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

        # pre-allocated key for just in case
        key = uuid.uuid4().hex[:8]
        owns_effect = False
        # render the children first so we know if a effect is present
        if allow_children:
            result = [">"]
            for idx, c in enumerate(children):
                if isinstance(c, _Effect) and c.key is None:
                    c.index = idx
                    c.key = key
                    result.append(c)
                    owns_effect = True
                elif isinstance(c, list):
                    result += c
                else:
                    result.append(c)
            result.append(f"</{tag_name}>")
        else:
            result = ["/>"]

        # now go back and build the tag and attributes
        preface = [f"<{tag_name}"]
        if attributes or owns_effect:
            for k, v in sorted(attributes.items()):
                if isinstance(v, _Effect) and v.key is None:
                    v.index = k
                    v.key = key
                    preface += [f' {k}="', v, '"']
                    owns_effect = True
                # elif iscallable(v):
                # TODO: support callbacks more cleanly
                elif isinstance(v, bool) and v:
                    preface.append(f" {k}")
                else:
                    preface.append(f' {k}="{escape(v)}"')

            if owns_effect:
                preface.append(f' key="{key}"')

        return preface + result

    return _impl


_effect_stack = []


def effect(*dec_args, **dec_kwargs):
    """
    Decorator to mark a function as a effect. A effect is a special function that can
    be used to update parts of the Silkflow application in response to signal changes.

    If a single callable is provided as an argument, it is assumed to be a effect function.
    In this case, the decorator wraps the function and manages the associated effects.

    If the "render" keyword argument is set to True, the decorator assumes the function
    is a render function. It creates a FastAPI-compatible function that returns an
    HTMLResponse with the rendered content of the Silkflow application.

    Usage:
        @effect
        def some_effect():
            ...

        @effect(render=True, head_elems=[...], body_attrs={...})
        def render_function():
            ...

    Args:
        *dec_args: Arguments for the decorator. If a single callable is provided,
            it is assumed to be a effect function.
        **dec_kwargs: Keyword arguments for the decorator. Can contain the following keys:
            - render (bool): If True, the decorator assumes the function is a render function.
            - head_elems (List[HTMLElement]): Optional list of head elements to include in the
                rendered HTML when render=True.
            - body_attrs (Dict[str, Any]): Optional dictionary of body attributes to include
                in the rendered HTML when render=True.

    Raises:
        ValueError: If an invalid combination of arguments or keyword arguments is provided.

    Returns:
        Union[Callable, _Effect]: The wrapped function or a _Effect instance depending on the use case.
    """

    if len(dec_args) == 1 and callable(dec_args[0]):

        @functools.wraps(dec_args[0])
        def _impl(*args, **kwargs):
            _effect_stack.append(set())
            value = dec_args[0](*args, **kwargs)
            func = functools.partial(dec_args[0], *args, **kwargs)
            result = _Effect(value, render_func=func)
            for c in _effect_stack.pop():
                c.effects.add(weakref.ref(result))
            return result

        return _impl
    elif "render" in dec_kwargs and dec_kwargs["render"]:

        def _dec_impl(fn):
            @functools.wraps(fn)
            def _impl2():
                # _impl has a effect attribute so we maintain a reference
                if not hasattr(_impl2, "body"):
                    _impl2.body = _factory("body")(
                        fn(), **dec_kwargs.get("body_attrs", {})
                    )
                response = _Effect(
                    js.render(
                        _impl2.body,
                        _session_id,
                        CALLBACK_URL,
                        EFFECTS_URL,
                        LOG_URL,
                        _Effect._backlog_offs + len(_Effect._backlog),
                        head_elems=dec_kwargs.get("head_elems", []),
                    )
                )
                return HTMLResponse(
                    content="<!DOCTYPE html>" + response.html, status_code=200
                )

            fn = effect(fn)

            return _impl2

        return _dec_impl
    else:
        raise ValueError("Invalid effect decorator")


class Signal(object):
    """
    Signal represents a mutable signal value in a Silkflow application.
    When the signal value changes, it triggers updates to the associated effects.

    Attributes:
        value: Property having get/set methods that manage effects.
        effects: The set of effects to be updated when the signal value changes.
    """

    __slots__ = ["_value", "effects"]

    def __init__(self, initial_value):
        """
        Initializes the Signal with an initial value.

        Args:
            initial_value: The initial value of the signal.
        """
        self._value = initial_value
        self.effects = set()

    @property
    def value(self):
        """
        The current value of the signal.

        Returns:
            The current value of the signal.
        """
        if len(_effect_stack) > 0:
            _effect_stack[-1].add(self)
        return self._value

    @value.setter
    def value(self, value):
        """
        Sets a new value for the signal and triggers updates to the associated effects.

        Args:
            value: The new value to be set for the signal.
        """
        try:
            # only update if the value hasn't changed
            # but don't barf if the type doesn't support __eq__ operator
            if self._value == value:
                return
        except:
            pass

        for o in self.effects:
            if o() is not None:
                o().flush()
        self._value = value


_callback_map = {}


def callback(*dec_args, **dec_kwargs):
    """
    Decorator for callback functions in a Silkflow application.
    When used, it assigns a unique ID to the callback function and
    stores it in the _callback_map.

    Args:
        dec_args: Positional arguments for the decorator.
        dec_kwargs: Keyword arguments for the decorator.

    Returns:
        A string that triggers the appropriate JavaScript function
        with the associated callback ID and event object.

    Raises:
        ValueError: If the decorator is used improperly.
    """
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

        current_time = int(time.time() * 1000)
        # Don't yield here
        asyncio.create_task(sync_effects())
        return dict(time=current_time)

    response = JSONResponse(content={})
    response.status_code = 200
    response.headers["X-Redirect-URL"] = "/"
    return response


@router.get(EFFECTS_URL)
async def _effects(session: str, state: int):
    global _sync_condition

    if session != _session_id or state < _Effect._backlog_offs:
        response = JSONResponse(content={})
        response.status_code = 200
        response.headers["X-Redirect-URL"] = "/"
        return response

    if _sync_condition is None:
        _sync_condition = asyncio.Condition()

    async with _sync_condition:
        if state >= _Effect._backlog_offs + len(_Effect._backlog):
            await _sync_condition.wait()

    if state >= _Effect._backlog_offs + len(_Effect._backlog):
        updates = []
    else:
        updates = [
            u
            for updates in itertools.islice(
                _Effect._backlog, state - _Effect._backlog_offs, None
            )
            for u in updates
        ]

    current_time = int(time.time() * 1000)
    data = dict(
        state=_Effect._backlog_offs + len(_Effect._backlog),
        updates=updates,
        time=current_time,
    )
    response = JSONResponse(content=data)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = "0"

    return response


@router.post(LOG_URL)
async def log_endpoint(log: str = fastapi.Body(embed=True)):
    print(log)
    return {"status": "success"}
