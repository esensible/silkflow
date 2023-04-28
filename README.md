# Silkflow

## A fine grained reactive Python framework - for Kindles

Silkflow is a lightweight, fine grained reactive web framework that brings the Kindle Paperwhite and Raspberry Pi together for a match made in heaven. Designed specifically for resource-constrained environments, Silkflow allows you to create interactive web applications in Python, similar to Plotly Dash or Streamlit, but with a focus on supporting the Kindle Paperwhite as a low-cost, IP67 rated, daylight readable display.

## Kindle Paperwhite and Raspberry Pi: A perfect match

Silkflow unlocks the potential of the Kindle Paperwhite as a versatile, low-cost, waterproof, daylight readable display, powered by a Raspberry Pi or similar embedded controllers. This framework is ideal for hobbyists and tinkerers who want to bring their creative ideas to life using the Kindle Paperwhite as a display for projects like home automation control panels, weather station displays, or real-time data dashboards.

## Features

* **Kindle Paperwhite Support:** Tailored for use with the Kindle Paperwhite, leveraging its unique features as a low-cost, IP67 rated, daylight readable display.
   * Does NOT require Jailbroken Kindle - works with Firmware version 5.15.1
* **Lightweight and Efficient:** Designed for resource-constrained environments, Silkflow ensures smooth performance on a wide range of devices, including the Kindle Paperwhite.
* **Reactive Web Framework:** Build interactive and dynamic applications with ease using Silkflow's Python-based reactive framework, embracing real-time updates without tedious page reloads.
* **Synchronized Multi-client Support:** Create applications that require real-time collaboration or shared state across multiple devices, taking full advantage of the Kindle Paperwhite as a display.
Getting Started

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

state = silkflow.Signal(False)


@silkflow.effect
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
@silkflow.effect(render=True, head_elems=head())
def index():
    return silkflow.html.div(
        silkflow.html.h1(button_pressed()),
        silkflow.html.button("Press me", onclick=toggle),
    )
```

In this example, we use FastAPI as our web framework and Silkflow to create a simple web application with a button that toggles between "On" and "Off". When the button is clicked, the **toggle** function is called, which updates the **state** value. The **button_pressed** function is used as a effect to display the current state of the button in an **\<h1>** element. The **index** function renders the application with the Silkflow HTML elements.

## Examples

* [ExtremeRacer](https://github.com/esensible/extremeracer) This project was developed for and split out from this sailing tactician application. It provides a pretty good example of more complex usage.

## Kindle Paperwhite

The Kindle Paperwhite is an awesome display for loads of projects, not to mention that the HW is subsidised

* **High-resolution e-ink display:** The Kindle Paperwhite's easily readable display works well under various lighting conditions.
* **IP67 rated:** The Paperwhite's durability and suitability for diverse environments make it a reliable display choice.
* **Low power consumption:** The device lasts weeks on a single charge, making it perfect for energy-efficient projects.

Silkflow was developed with the sole purpose of delivering IoT and other projects designed to rock the Kindle Paperwhite's capabilities, providing a visually appealing and functional user experience. Explore Silkflow and unlock the full potential of the Kindle Paperwhite for your projects.

### Hacks

There are a bunch of projects for jailbroken Kindles - this is not one of them. I wasn't initially aware of the tips below but with some rumaging about in the firmware I rediscovered them. I still haven't seen the first one discussed anywhere else.

As at Kindle 5.15.1 on an 11th Gen Paperwhite:
* **Disable screensaver:** Create empty file TESTD_PREVENT_SCREENSAVER
* **Local hotspot:** Create empty file WIFI_NO_NET_PROBE to support local hotspot with no internet connectivity. Without this, the Kindle will disable its wifi if it can't see the internet via your hotspot.
* **Factory reset:** Create empty file DO_FACTORY_RESTORE.
   * I was initially using demo mode to disable the screensaver and bricked the device a lot. With the TESTD tip above, this is no longer an issue.
   * Update: This now more widely [known](https://www.mobileread.com/forums/showthread.php?t=352392) even for later firmware versions

## Acknowledgements

Big thanks to the projects that inspired the creation of Silkflow, such as Dash and IDOM/ReactPy. The ideas and concepts from these projects have greatly influenced the development of Silkflow.

Shout out to SolidJS for the realisation that we'd successfully reinvented the wheel. Upon learning, terminology was updated to be consistent with other inventors of wheels.