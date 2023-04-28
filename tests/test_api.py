import asyncio
from bs4 import BeautifulSoup
from collections import deque
import fastapi
import httpx
import pytest

import silkflow


async def _test_effects(client, state, expected_state, expected_updates):
    response, _ = await asyncio.gather(
        client.get(f"/effects?session={silkflow.core._session_id}&state={state}"), silkflow.sync_effects()
    )
    assert response.status_code == 200
    result = response.json()
    assert result == {
        "state": expected_state,
        "updates": expected_updates,
        "time": result["time"],
    }


def _init_core():
    silkflow.core._Effect._stale_effects = set()
    silkflow.core._Effect._backlog = deque()
    silkflow.core._Effect._backlog_offs = 0
    silkflow.core._sync_condition = None


@pytest.mark.asyncio
async def test_get():
    _init_core()

    app = fastapi.FastAPI()
    app.include_router(silkflow.router)

    c1 = silkflow.Signal("str")

    @silkflow.effect
    def the_str():
        return c1.value

    @app.get("/")
    @silkflow.effect(render=True)
    def test():
        return silkflow.html.div(the_str())

    async with httpx.AsyncClient(app=app, base_url="http://test.me") as client:
        response = await client.get("/")
        assert response.status_code == 200

        soup = BeautifulSoup(response.text, "html.parser")
        container = soup.find("div")
        assert container is not None
        assert container.text == "str"
        key = container["key"]

        await _test_effects(client, 0, 0, [])

        c1.value = "new str"

        c1.value = "new str"
        await _test_effects(client, 0, 1, [[key, 0, "new str"]])
        # idempotent poll
        await _test_effects(client, 0, 1, [[key, 0, "new str"]])
        await _test_effects(client, 1, 1, [])

        # Confirm updates are chained - yes, this overwrites the same element
        c1.value = "str2"
        # need an explicit sync here or effects?state=0 returns immediately
        # without picking up "str2" update.
        # This is typical of async loops updating state as opposed to via callbacks
        await silkflow.sync_effects()

        await _test_effects(client, 0, 2, [[key, 0, "new str"], [key, 0, "str2"]])
        await _test_effects(client, 1, 2, [[key, 0, "str2"]])
        await _test_effects(client, 2, 2, [])

        # blow out core.MAX_UPDATES
        for i in range(2, silkflow.core.BACKLOG_LEN + 3):
            c1.value = f"new str {i}"
            await _test_effects(client, i, i + 1, [[key, 0, f"new str {i}"]])

        # if we've fallen off the cached effects, we expect a redirect
        response = await client.get(f"/effects?session={silkflow.core._session_id}&state=0")
        assert response.status_code == 200
        x_redirect_url = response.headers.get("X-Redirect-URL")
        assert x_redirect_url == "/"
        result = response.json()
        assert result == {}


@pytest.mark.asyncio
async def test_attribute():
    _init_core()

    app = fastapi.FastAPI()
    app.include_router(silkflow.router)

    _attr = silkflow.Signal("value")

    @silkflow.effect
    def attr():
        return _attr.value

    @app.get("/")
    @silkflow.effect(render=True)
    def test():
        return silkflow.html.div("str", attr=attr(), blah="bongo")

    async with httpx.AsyncClient(app=app, base_url="http://test.me") as client:
        response = await client.get("/")
        assert response.status_code == 200

        soup = BeautifulSoup(response.text, "html.parser")
        container = soup.find("div")
        assert container is not None
        assert container["blah"] == "bongo"
        assert container["attr"] == "value"
        assert container.text == "str"
        key = container["key"]

        await _test_effects(client, 0, 0, [])

        _attr.value = "new_value"

        await _test_effects(client, 0, 1, [[key, "attr", "new_value"]])

        # # idempotent poll
        await _test_effects(client, 0, 1, [[key, "attr", "new_value"]])
        await _test_effects(client, 1, 1, [])

        response = await client.get("/")
        assert response.status_code == 200

        soup = BeautifulSoup(response.text, "html.parser")
        container = soup.find("div")
        assert container is not None
        assert container["blah"] == "bongo"
        assert container["attr"] == "new_value"
        assert container.text == "str"
        assert container["key"] == key

        await _test_effects(client, 0, 1, [[key, "attr", "new_value"]])
        await _test_effects(client, 1, 1, [])
