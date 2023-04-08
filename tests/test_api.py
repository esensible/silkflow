from bs4 import BeautifulSoup
import fastapi
from fastapi.testclient import TestClient


def test_get():
    app = fastapi.FastAPI()
    app.include_router(router)

    c1 = State("str")

    @hook
    def the_str():
        return c1.value

    @app.get("/")
    @hook(render=True)
    def test():
        return div(the_str())

    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200

    soup = BeautifulSoup(response.text, "html.parser")
    container = soup.find("div")
    assert container is not None
    assert container.text == "str"
    key = container["key"]

    response = client.get("/poll?state=0")
    assert response.status_code == 200
    assert response.json() == {"state": 0, "updates": []}

    c1.value = "new str"

    response = client.get("/poll?state=0")
    assert response.status_code == 200
    assert response.json() == {"state": 1, "updates": [[key, 0, "new str"]]}

    # idempotent poll
    response = client.get("/poll?state=0")
    assert response.status_code == 200
    assert response.json() == {"state": 1, "updates": [[key, 0, "new str"]]}

    response = client.get("/poll?state=1")
    assert response.status_code == 200
    assert response.json() == {"state": 1, "updates": []}

    # blow out core.MAX_UPDATES
    for i in range(1, 10):
        c1.value = f"new str {i}"
        response = client.get(f"/poll?state={i}")
        assert response.status_code == 200
        assert response.json() == {
            "state": i + 1,
            "updates": [[key, 0, f"new str {i}"]],
        }
