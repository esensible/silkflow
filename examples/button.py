#!/usr/bin/env python

import silkflow
import fastapi

app = fastapi.FastAPI()
app.include_router(silkflow.router)

state = silkflow.State(False)


@silkflow.hook
def button_pressed():
    return "On" if state.value else "Off"


@silkflow.callback
def toggle(_):
    state.value = not state.value


def head():
    return [
        silkflow.html.title("Button example"),
    ]


@app.get("/")
@silkflow.hook(render=True, head_elems=head())
def index():
    return silkflow.html.div(
        silkflow.html.h1(button_pressed()),
        silkflow.html.button("Press me", onclick=toggle),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("button:app", host="127.0.0.1", port=8000, reload=True)
