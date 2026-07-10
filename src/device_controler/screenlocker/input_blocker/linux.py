#!/usr/bin/env python3
# input_blocker.py

from evdev import InputDevice, list_devices
from pathlib import Path
import threading

_grabbed_devices: dict[str, InputDevice] = {}


def block() -> None:
    """
    Block all current /dev/input/event* devices.
    No parameter needed.
    """
    global _grabbed_devices

    for dev_path in list_devices():
        path = str(Path(dev_path))  # normalize path key

        if path in _grabbed_devices:  # already grabbed
            continue

        try:
            dev = InputDevice(path)  # open device
            dev.grab()  # take exclusive input
            _grabbed_devices[path] = dev  # keep handle for release
        except Exception:
            try:
                dev.close()  # cleanup half-open device
            except Exception:
                pass


def unblock() -> None:
    """
    Unblock all devices previously blocked by block().
    No parameter needed.
    """
    global _grabbed_devices

    for path, dev in list(_grabbed_devices.items()):
        try:
            dev.ungrab()  # release input
        except Exception:
            pass

        try:
            dev.close()  # close handle
        except Exception:
            pass

        _grabbed_devices.pop(path, None)  # forget released device
