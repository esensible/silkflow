# Silkflow - Lightweight Reactive Web Framework

Silkflow is a lightweight reactive web framework for Python, designed to target lower power devices for the backend and the Silk browser for the front-end. Silkflow is inspired by projects like Dash and IDOM, but the main motivation behind its development is to create a smaller, lighter weight framework that is well-suited for resource-constrained environments.

## Designing for the Silk Browser

The Silk browser has specific limitations that influenced the design choices made for Silkflow:

- **ES5 only:** Silkflow is designed to work with ES5 JavaScript, which helps ensure compatibility with a wide range of devices, including older or lower-powered devices that may not support newer JavaScript features.
- **No Websockets:** The Silk browser does not support Websockets, so Silkflow relies on alternative communication methods like HTTP long-polling to provide a reactive user experience.
- **Synchronized, multi-head clients:** Silkflow is designed to work well with synchronized, multi-head clients, making it a great choice for applications that require real-time collaboration or shared experiences across multiple devices.

By focusing on these design constraints, Silkflow offers a lightweight and efficient framework that can run smoothly on a variety of devices and browsers, including the Silk browser and other resource-limited environments.

## Features

- Lightweight and efficient design optimized for lower-power devices and the Silk browser
- Reactive web framework with support for ES5 JavaScript
- Alternative communication methods to Websockets, using HTTP long-polling
- Designed for synchronized, multi-head clients for real-time collaboration and shared experiences

## Acknowledgements

We would like to acknowledge the projects that inspired the creation of Silkflow, such as Dash and IDOM. The ideas and concepts from these projects have greatly influenced the development of Silkflow, and we appreciate their contributions to the web development ecosystem.
