#!/usr/bin/env python

import asyncio
from datetime import datetime, timedelta
import fastapi

import silkflow

app = fastapi.FastAPI()
app.include_router(silkflow.router)


#
# Time of day clock. The sync_effects() call will sync the client(s) on
# 1s boundaries.
#
_clock = silkflow.Signal(datetime.now().strftime("%I:%M:%S").lstrip("0"))


async def clock_task():
    while True:
        now = datetime.now()
        next_minute = now + timedelta(seconds=1)
        next_minute = next_minute.replace(microsecond=0)
        remaining_seconds = (next_minute - now).total_seconds()
        # just chill if we wake a little early
        if remaining_seconds < 0.01:
            next_minute += timedelta(seconds=1)
            remaining_seconds = (next_minute - now).total_seconds()
        await asyncio.sleep(remaining_seconds)
        _clock.value = next_minute.strftime("%I:%M:%S").lstrip("0")
        # causes the long poll to return and the UI to refresh
        await silkflow.sync_effects()


@silkflow.effect
def clock():
    return _clock.value


#
# Asynchronous timer to demonstrate /effects synchronisation
#
_counter = silkflow.Signal(0)


async def counter_task():
    while True:
        await asyncio.sleep(0.2)
        _counter.value += 1


@silkflow.effect
def counter():
    return str(_counter.value)


@app.on_event("startup")
async def startup():
    asyncio.create_task(clock_task())
    asyncio.create_task(counter_task())


_title = silkflow.html.title("Clock example")


@app.get("/")
@silkflow.effect(render=True, head_elems=[_title])
def index():
    return silkflow.html.div(
        silkflow.html.h1(silkflow.html.span("Clock: "), clock()),
        silkflow.html.h1(silkflow.html.span("Counter: "), counter()),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("clock:app", host="127.0.0.1", port=8000, reload=True)
