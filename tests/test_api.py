import asyncio
from bs4 import BeautifulSoup
import fastapi
import httpx
import pytest

import silkflow


async def _test_poll(client, state, expected_state, expected_updates):
    response, _ = await asyncio.gather(
        client.get(f"/poll?state={state}"), silkflow.sync_poll()
    )
    assert response.status_code == 200
    result = response.json()
    assert result == {
        "state": expected_state,
        "updates": expected_updates,
        "time": result["time"],
    }


@pytest.mark.asyncio
async def test_get():
    app = fastapi.FastAPI()
    app.include_router(silkflow.router)

    c1 = silkflow.State("str")

    @silkflow.hook
    def the_str():
        return c1.value

    @app.get("/")
    @silkflow.hook(render=True)
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

        await _test_poll(client, 0, 0, [])

        c1.value = "new str"

        c1.value = "new str"
        await _test_poll(client, 0, 1, [[key, 0, "new str"]])
        # idempotent poll
        await _test_poll(client, 0, 1, [[key, 0, "new str"]])
        await _test_poll(client, 1, 1, [])

        # Confirm updates are chained - yes, this overwrites the same element
        c1.value = "str2"
        # need an explicit sync here or poll?state=0 returns immediately
        # without picking up "str2" update.
        # This is typical of async loops updating state as opposed to via callbacks
        await silkflow.sync_poll()

        await _test_poll(client, 0, 2, [[key, 0, "new str"], [key, 0, "str2"]])
        await _test_poll(client, 1, 2, [[key, 0, "str2"]])
        await _test_poll(client, 2, 2, [])

        # blow out core.MAX_UPDATES
        for i in range(2, silkflow.core.MAX_UPDATES + 3):
            c1.value = f"new str {i}"
            await _test_poll(client, i, i + 1, [[key, 0, f"new str {i}"]])

        # if we've fallen off the cached updates, we expect a redirect
        response = await client.get(f"/poll?state=0")
        assert response.status_code == 200
        x_redirect_url = response.headers.get("X-Redirect-URL")
        assert x_redirect_url == "/"
        result = response.json()
        assert result == {}
