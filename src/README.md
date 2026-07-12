# device_controller

All packages in this directory provide features for controlling the computer.
It gonna be used to control student computer.

# system_monitor

Provides APIs for collecting and monitoring system information.

# utils
Provide reuseable functionality for other packages, such as:
* Blocking all input devices

Packages in this directory are intended to be imported by other packages. They should not import feature packages or depend on higher-level project components.
Put new functionality here when more than one packages needs it.
# Rules

* The main APIs of all plugins and packages must not block the main thread.
* Long-running operations must run in daemon threads with `daemon=True`.
