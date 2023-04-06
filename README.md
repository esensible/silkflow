# Silkflow - Lightweight Reactive Web Framework

Silkflow is a lightweight reactive web framework for Python, designed to target lower power devices (e.g. pi zero) for the backend. Silkflow specifically targets the Silk browser in the kindle paperwhite. 
Silkflow is inspired by projects like [Screedle](https://github.com/janhapke/screendle), [ReactPy](https://github.com/reactive-python/reactpy) and [Plotly Dash](https://github.com/plotly/dash). This framework is intentionally smaller and lighter weight than other the other python frameworks as its targetting resource-constrained environments. 
Note that while initial versions maintained a full vdom with reconcilliation, the current implementation is faster and simpler. 

## Designing for the Silk Browser

The Silk browser has specific limitations that influenced the design choices made for Silkflow:

- **ES5 only:** Silkflow is designed to work with ES5 JavaScript, which helps ensure compatibility with a wide range of devices, including older or lower-powered devices that may not support newer JavaScript features.
- **No Websockets:** The Silk browser does not support Websockets, so Silkflow relies on alternative communication methods like HTTP long-polling to provide a reactive user experience.

By focusing on these design constraints, Silkflow offers a lightweight and efficient framework that can run smoothly on a variety of devices and browsers, including the Silk browser and other resource-limited environments.

## Multihead

Silkflow is designed to support multiple synchronized clients, making it a great choice for applications that require real-time collaboration or shared state to be displayed across multiple devices. My specific use case is supporting multiple Paperwhites on my boat displaying speed, heading etc.

## Features

- Lightweight and efficient design optimized for lower-power devices and the Silk browser
- Reactive web framework with support for ES5 JavaScript
- Alternative communication methods to Websockets, using HTTP long-polling
- Designed for synchronized, multi-head clients for real-time collaboration and shared experiences

## Acknowledgements

We would like to acknowledge the projects that inspired the creation of Silkflow, such as Dash and IDOM. The ideas and concepts from these projects have greatly influenced the development of Silkflow, and we appreciate their contributions to the web development ecosystem.
