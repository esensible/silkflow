# Silkflow - Reactive Python Framework for the Kindle Paperwhite

Silkflow is a lightweight, reactive web framework for Python, specifically designed for Kindle devices like the Kindle Paperwhite. With its e-ink display, long battery life, and IP67 rating, the Kindle Paperwhite is an excellent choice for hobbyist projects such as home automation, weather station displays, and other IoT applications. Silkflow simplifies the development, testing, and deployment of applications on Kindle devices, allowing you to create engaging and interactive user interfaces tailored for your projects.

Silkflow is designed to work with ES5 JavaScript and uses HTTP long-polling as an alternative to Websockets for providing a reactive user experience. This design choice ensures compatibility with a wide range of devices, including older or lower-powered devices that may not support newer JavaScript features.

Silkflow is also designed to support multiple synchronized clients, making it a great choice for applications that require real-time collaboration or shared state to be displayed across multiple devices.

## Features

- Lightweight and efficient design optimized for lower-power devices and the Silk browser
- Reactive web framework with support for ES5 JavaScript
- Alternative communication methods to Websockets, using HTTP long-polling
- Designed for synchronized, multi-head clients for real-time collaboration and shared experiences

## Kindle Paperwhite

The Kindle Paperwhite is an awesome display for loads of projects, not to mention that the HW is subsidised

* **High-resolution e-ink display**: The Kindle Paperwhite's easily readable display works well under various lighting conditions.
* **IP67 rated**: The Paperwhite's durability and suitability for diverse environments make it a reliable display choice.
* **Low power consumption**: The device lasts weeks on a single charge, making it perfect for energy-efficient projects.

Silkflow was developed with the sole purpose of delivering IoT and other projects designed to rock the Kindle Paperwhite's capabilities, providing a visually appealing and functional user experience. Explore Silkflow and unlock the full potential of the Kindle Paperwhite for your projects.

## Getting Started

To install Silkflow, use pip:

```bash
pip install git+https://github.com/esensible/silkflow.git#egg=silkflow
```

To create a Silkflow application, you'll need to import Silkflow and a web framework like FastAPI:

```
import silkflow
import fastapi

app = fastapi.FastAPI()
app.include_router(silkflow.router)

# Your application code goes here
```

Silkflow supports creating HTML elements and managing state. Here is a simple example:
```
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
```


## Examples

* [ExtremeRacer](https://github.com/esensible/extremeracer) This project was developed for and split out from this sailing tactician application. It provides a pretty good example of more complex usage.

## Acknowledgements

We would like to acknowledge the projects that inspired the creation of Silkflow, such as Dash and IDOM. The ideas and concepts from these projects have greatly influenced the development of Silkflow, and we appreciate their contributions to the web development ecosystem.
