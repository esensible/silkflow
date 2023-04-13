from bs4 import BeautifulSoup
import weakref

from silkflow.core import _Hook, State, hook, router
from silkflow.html import *


def test_basic():
    html = div("there")
    assert "".join(html) == "<div>there</div>"

    html = div("hi", div("there"), blah="bongo")
    assert "".join(html) == '<div blah="bongo">hi<div>there</div></div>'

    html = div(div("hi", zzz=True), div("there"), blah="bongo")
    assert "".join(html) == '<div blah="bongo"><div zzz>hi</div><div>there</div></div>'

    result = _Hook(div("test"))
    assert result.html == "<div>test</div>"
    assert result.children == []
    assert result.key == None
    assert result.index == None


def test_img():
    html = img(src="/static/pissing.jpg")
    assert "".join(html) == '<img src="/static/pissing.jpg" />'

    html = img(src="/static/pissing.jpg", Class="pissing")
    assert "".join(html) == '<img Class="pissing" src="/static/pissing.jpg" />'

    # img in a _Hook
    result = _Hook(img(src="/static/pissing.jpg"))
    assert result.html == '<img src="/static/pissing.jpg" />'


def test_hooks():
    html = div(div("world"), _Hook(div("hi", zzz=True)))
    hooks = [h for h in html if isinstance(h, _Hook)]
    assert len(hooks) == 1
    assert (
        "".join(str(h) for h in html)
        == f'<div key="{hooks[0].key}"><div>world</div><div zzz>hi</div></div>'
    )
    assert hooks[0].html == "<div zzz>hi</div>"
    assert hooks[0].children == []
    assert hooks[0].index == 1

    result = _Hook(div(div("padding"), _Hook(div("world")), _Hook(div("hi", zzz=True))))
    assert result.key == None
    assert result.index == None
    assert len(result.children) == 2
    assert result.children[0].key == result.children[1].key
    assert (
        result.html
        == f'<div key="{result.children[0].key}"><div>padding</div><div>world</div><div zzz>hi</div></div>'
    )
    assert result.children[0].index == 1
    assert result.children[0].html == "<div>world</div>"
    assert result.children[1].index == 2
    assert result.children[1].html == "<div zzz>hi</div>"

    assert result.children[0].children == []

    assert result.children[1].children == []


def test_nested_hook():
    """Testing a specific bug where a nested hook was causing a key to be set on the outer div"""

    @hook
    def a_str():
        return "str"

    def nop():
        return div(a_str())

    result = "".join(str(e) for e in div(nop()))

    soup = BeautifulSoup(result, "html.parser")

    outer_div = soup.div
    inner_div = outer_div.div

    assert "key" not in outer_div.attrs
    assert "key" in inner_div.attrs


def test_context():
    c1 = State(0)
    c2 = State(0)

    @hook
    def _nested():
        return div(f"_nested {c2.value}, {c1.value}")

    @hook
    def test():
        return div(div(f"hi {c1.value}"), _nested())

    result = test()
    key = result.children[0].key
    assert (
        result.html
        == f'<div key="{result.children[0].key}"><div>hi 0</div><div>_nested 0, 0</div></div>'
    )
    assert weakref.ref(result) in c1.hooks
    assert len(result.children) == 1

    assert result.children[0].html == "<div>_nested 0, 0</div>"
    c2.value = 2
    stale = _Hook._stale_hooks
    _Hook._stale_hooks = set()
    assert len([s for s in stale if s() is not None]) == 1
    assert next(s() for s in stale).html == "<div>_nested 2, 0</div>"
    assert result.children[0].html == "<div>_nested 2, 0</div>"
    assert (
        result.html
        == f'<div key="{result.children[0].key}"><div>hi 0</div><div>_nested 2, 0</div></div>'
    )

    c1.value = 1
    c2.value = 2

    stale2 = _Hook._stale_hooks
    _Hook._stale_hooks = set()
    # probs have 1 dead hook in the stale list
    assert len([s for s in stale2 if s() is not None]) == 1
    # the original stale list only has dead hook refs now
    assert len([s for s in stale if s() is not None]) == 0

    assert (
        result.html
        == f'<div key="{result.children[0].key}"><div>hi 1</div><div>_nested 2, 1</div></div>'
    )
    assert result.children[0].html == "<div>_nested 2, 1</div>"


def test_str_hook():
    c1 = State("str")

    @hook
    def the_str():
        return c1.value

    @hook
    def test():
        return div(the_str())

    result = test()
    key = result.children[0].key
    assert result.html == f'<div key="{result.children[0].key}">str</div>'
    assert len(result.children) == 1
    assert weakref.ref(result.children[0]) in c1.hooks

    c1.value = "new str"
    stale = _Hook._stale_hooks
    _Hook._stale_hooks = set()
    assert len([s for s in stale if s() is not None]) == 1

    assert result.html == f'<div key="{key}">new str</div>'
    assert result.children[0].html == "new str"


def test_concat():
    # Hook._concat() was busted, so this is a test

    h1 = _Hook([])
    h2 = _Hook([])
    input = ["a", "b", h1, "c", "d", "e", h2, "f"]

    print(_Hook._concat(input))
    assert _Hook._concat(input) == ["ab", h1, "cde", h2, "f"]


def test_render():
    c1 = State("str")

    @hook
    def the_str():
        return c1.value

    @hook(render=True)
    def test():
        return div(the_str())

    result = test()
    soup = BeautifulSoup(result.body, "html.parser")
    body_key = soup.body["key"]

    # assert that pulling the same content doesn't re-render (ie change the key)
    result = test()
    soup = BeautifulSoup(result.body, "html.parser")
    assert body_key == soup.body["key"]
