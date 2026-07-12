"""Stable public input-control API for Linux and Windows.

File path: `src/utils/input_controller/__init__.py`

Role:
- This package is the only input-controller surface application code should
  import. It hides Linux/Windows differences behind one API.

Input contract:
- `x`, `y` are desktop pixel coordinates.
- `button` is a mouse button name: `left`, `right`, `middle`, `back`, `forward`.
- `button` in keyboard APIs is a key name such as `a`, `enter`, `leftctrl`.
- Listener callbacks receive `KeyboardEvent(name, event_type, text)`.

Output contract:
- Control APIs emit real OS input events and return `None`.
- `position()` returns `(x, y)` as integers.
- `listen_keys()` starts background monitoring and returns a handle with `stop()`.

Architecture:
- Linux control: `linux_backend.py` with evdev `/dev/uinput`.
- Windows control: `windows_backend.py` with `pydirectinput-rgx`.
- Linux listener: `linux_listener.py` with evdev `/dev/input/event*`.
- Windows listener: `windows_listener.py` with `pynput`.
- Shared listener data types: `types.py`.

Important assumptions:
- Importing this module must be cheap and side-effect-light. It must not create
  Linux virtual input devices, import Windows-only modules on Linux, or start
  keyboard listener threads.
- Backends are selected lazily on first use. `_backend_lock` protects only this
  first selection step so two application threads cannot initialize the same
  backend twice.

See `src/utils/input_controller/README.md` for the module map, threading model,
OS permissions, and backend behavior.
"""

from __future__ import annotations

import os
import threading
from typing import Protocol

from utils.input_controller.types import KeyCallback, KeyboardEvent, KeyListener


class _ControlBackend(Protocol):
    def click(self, x: int, y: int) -> None: ...

    def moveTo(self, x: int, y: int, steps: int, duration: float) -> None: ...

    def mouseDown(self, button: str) -> None: ...

    def mouseUp(self, button: str) -> None: ...

    def keyDown(self, button: str) -> None: ...

    def keyUp(self, button: str) -> None: ...

    def position(self) -> tuple[int, int]: ...


class _ListenerBackend(Protocol):
    def listen_keys(
        self,
        callback: KeyCallback,
        typeable_only: bool = False,
    ) -> KeyListener: ...


_control_backend: _ControlBackend | None = None
_listener_backend: _ListenerBackend | None = None
_backend_lock = threading.Lock()


def _get_backend() -> _ControlBackend:
    """Return the OS-specific control backend, creating it on first use.

    Backend imports stay inside this function because some dependencies only
    exist on one OS. Lazy import keeps `import utils.input_controller` safe in
    tests, documentation tools, and non-interactive contexts.
    """

    global _control_backend

    if _control_backend is not None:
        return _control_backend
    # Double-check under the lock so concurrent first calls share one backend.
    with _backend_lock:
        if _control_backend is None:
            if os.name == "nt":
                from utils.input_controller.windows_backend import WindowsBackend

                _control_backend = WindowsBackend()
            elif os.name == "posix":
                from utils.input_controller import linux_backend

                _control_backend = linux_backend
            else:
                raise NotImplementedError(f"Unsupported operating system: {os.name}")
    return _control_backend


def _get_listener_backend() -> _ListenerBackend:
    """Return the OS-specific keyboard listener backend.

    Listener backend selection is separate from control backend selection. A
    caller may only send input, only listen to input, or do both, so each side is
    loaded independently.
    """

    global _listener_backend

    if _listener_backend is not None:
        return _listener_backend
    # The same lock is enough because backend selection is quick and rare.
    with _backend_lock:
        if _listener_backend is None:
            if os.name == "nt":
                from utils.input_controller import windows_listener

                _listener_backend = windows_listener
            elif os.name == "posix":
                from utils.input_controller import linux_listener

                _listener_backend = linux_listener
            else:
                raise NotImplementedError(f"Unsupported operating system: {os.name}")
    return _listener_backend


def click(x: int, y: int) -> None:
    """Move to `(x, y)` and immediately perform a left click.

    No implicit delay is added. The Windows backend explicitly disables
    pydirectinput's pause behavior; the Linux backend writes events directly to
    the virtual mouse device.
    """

    _get_backend().click(x, y)


def moveTo(x: int, y: int, steps: int, duration: float) -> None:
    """Move to `(x, y)` using `steps` points over `duration` seconds.

    `steps` must be positive. `duration` is the only public control argument
    that intentionally waits; other control functions should be immediate.
    """

    _get_backend().moveTo(x, y, steps, duration)


def mouseDown(button: str) -> None:
    """Press and hold a mouse button immediately."""

    _get_backend().mouseDown(button)


def mouseUp(button: str) -> None:
    """Release a mouse button immediately."""

    _get_backend().mouseUp(button)


def keyDown(button: str) -> None:
    """Press and hold a keyboard key immediately."""

    _get_backend().keyDown(button)


def keyUp(button: str) -> None:
    """Release a keyboard key immediately."""

    _get_backend().keyUp(button)


def position() -> tuple[int, int]:
    """Return current pointer coordinates as `(x, y)`.

    Linux/Wayland may not expose the true global pointer location. In that case
    the Linux backend falls back to the last coordinate that SAG set itself.
    """

    return _get_backend().position()


def listen_keys(callback: KeyCallback, typeable_only: bool = False) -> KeyListener:
    """Listen to keyboard events through the current OS backend.

    The callback receives `KeyboardEvent(name, event_type, text)`. `event_type`
    is `down`, `press`, or `up`; `text` is a typed character when available. When
    `typeable_only=True`, control keys such as `esc`, `ctrl`, and `alt` are not
    passed to the callback.

    The callback runs on a backend listener thread, not necessarily the caller's
    thread. Keep callback work short or hand off to an application queue.
    """

    return _get_listener_backend().listen_keys(callback, typeable_only)


__all__ = [
    "KeyCallback",
    "KeyboardEvent",
    "KeyListener",
    "click",
    "keyDown",
    "keyUp",
    "listen_keys",
    "mouseDown",
    "mouseUp",
    "moveTo",
    "position",
]
