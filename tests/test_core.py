from bs4 import BeautifulSoup
import weakref

from silkflow.core import _Effect, Signal, effect
from silkflow.html import *


def test_basic():
    html = div("there")
    assert "".join(html) == "<div>there</div>"

    html = div("hi", div("there"), blah="bongo")
    assert "".join(html) == '<div blah="bongo">hi<div>there</div></div>'

    html = div(div("hi", zzz=True), div("there"), blah="bongo")
    assert "".join(html) == '<div blah="bongo"><div zzz>hi</div><div>there</div></div>'

    result = _Effect(div("test"))
    assert result.html == "<div>test</div>"
    assert result.children == []
    assert result.key == None
    assert result.index == None


def test_img():
    html = img(src="/static/an_image.jpg")
    assert "".join(html) == '<img src="/static/an_image.jpg"/>'

    html = img(src="/static/an_image.jpg", Class="yay")
    assert "".join(html) == '<img Class="yay" src="/static/an_image.jpg"/>'

    # img in a _Effect
    result = _Effect(img(src="/static/an_image.jpg"))
    assert result.html == '<img src="/static/an_image.jpg"/>'


def test_effects():
    html = div(div("world"), _Effect(div("hi", zzz=True)))
    effects = [h for h in html if isinstance(h, _Effect)]
    assert len(effects) == 1
    assert (
        "".join(str(h) for h in html)
        == f'<div key="{effects[0].key}"><div>world</div><div zzz>hi</div></div>'
    )
    assert effects[0].html == "<div zzz>hi</div>"
    assert effects[0].children == []
    assert effects[0].index == 1

    result = _Effect(
        div(div("padding"), _Effect(div("world")), _Effect(div("hi", zzz=True)))
    )
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


def test_nested_effect():
    """Testing a specific bug where a nested effect was causing a key to be set on the outer div"""

    @effect
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
    c1 = Signal(0)
    c2 = Signal(0)

    @effect
    def _nested():
        return div(f"_nested {c2.value}, {c1.value}")

    @effect
    def test():
        return div(div(f"hi {c1.value}"), _nested())

    result = test()
    key = result.children[0].key
    assert (
        result.html
        == f'<div key="{result.children[0].key}"><div>hi 0</div><div>_nested 0, 0</div></div>'
    )
    assert weakref.ref(result) in c1.effects
    assert len(result.children) == 1

    assert result.children[0].html == "<div>_nested 0, 0</div>"
    c2.value = 2
    stale = _Effect._stale_effects
    _Effect._stale_effects = set()
    assert len([s for s in stale if s() is not None]) == 1
    assert next(s() for s in stale).html == "<div>_nested 2, 0</div>"
    assert result.children[0].html == "<div>_nested 2, 0</div>"
    assert (
        result.html
        == f'<div key="{result.children[0].key}"><div>hi 0</div><div>_nested 2, 0</div></div>'
    )

    c1.value = 1
    c2.value = 2

    stale2 = _Effect._stale_effects
    _Effect._stale_effects = set()
    # probs have 1 dead effect in the stale list
    assert len([s for s in stale2 if s() is not None]) == 1
    # the original stale list only has dead effect refs now
    assert len([s for s in stale if s() is not None]) == 0

    assert (
        result.html
        == f'<div key="{result.children[0].key}"><div>hi 1</div><div>_nested 2, 1</div></div>'
    )
    assert result.children[0].html == "<div>_nested 2, 1</div>"


def test_str_effect():
    c1 = Signal("str")

    @effect
    def the_str():
        return c1.value

    @effect
    def test():
        return div(the_str())

    result = test()
    key = result.children[0].key
    assert result.html == f'<div key="{result.children[0].key}">str</div>'
    assert len(result.children) == 1
    assert weakref.ref(result.children[0]) in c1.effects

    c1.value = "new str"
    stale = _Effect._stale_effects
    _Effect._stale_effects = set()
    assert len([s for s in stale if s() is not None]) == 1

    assert result.html == f'<div key="{key}">new str</div>'
    assert result.children[0].html == "new str"


def test_concat():
    # Effect._concat() was busted, so this is a test

    h1 = _Effect([])
    h2 = _Effect([])
    input = ["a", "b", h1, "c", "d", "e", h2, "f"]

    print(_Effect._concat(input))
    assert _Effect._concat(input) == ["ab", h1, "cde", h2, "f"]


def test_render():
    c1 = Signal("str")

    @effect
    def the_str():
        return c1.value

    @effect(render=True)
    def test():
        return div(the_str())

    result = test()
    soup = BeautifulSoup(result.body, "html.parser")
    body_key = soup.body["key"]

    # assert that pulling the same content doesn't re-render (ie change the key)
    result = test()
    soup = BeautifulSoup(result.body, "html.parser")
    assert body_key == soup.body["key"]


def test_attribute():
    klass = Signal("")

    @effect
    def the_class():
        return klass.value

    @effect(render=True)
    def test():
        return div("hi", Class=the_class())

    result = test()
    soup = BeautifulSoup(result.body, "html.parser")
    the_div = list(soup.body.children)[0]
    assert list(the_div.children) == ["hi"]
    assert the_div["class"] == []

    klass.value = "new class"
    result = test()
    soup = BeautifulSoup(result.body, "html.parser")
    the_div = list(soup.body.children)[0]
    assert the_div["class"] == ["new", "class"]
