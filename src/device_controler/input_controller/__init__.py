"""API dieu khien input chung cho Linux va Windows.

File path: `src/device_controler/input_controller/__init__.py`
Input:
- Toa do `x`, `y` la pixel tren desktop ao.
- `button` nhan `left`, `right`, `middle`, `back`, hoac `forward`.
- `key` nhan ten phim Linux thong dung, vi du `a`, `enter`, `leftctrl`.
Output:
- Linux phat input qua `evdev`; Windows dung `pydirectinput-rgx`.
- `listen_keys()` tra ve listener chay nen; goi `stop()` de dung sach.

Backend chi duoc import khi API dieu khien duoc goi lan dau. Moi delay ngam cua
backend Windows duoc tat; chi `moveTo()` cho theo `duration` public.
"""

from __future__ import annotations

import os
import threading
from typing import Protocol


class _ControlBackend(Protocol):
    def click(self, x: int, y: int) -> None: ...

    def moveTo(self, x: int, y: int, steps: int, duration: float) -> None: ...

    def mouseDown(self, button: str) -> None: ...

    def mouseUp(self, button: str) -> None: ...

    def keyDown(self, button: str) -> None: ...

    def keyUp(self, button: str) -> None: ...

    def position(self) -> tuple[int, int]: ...


_control_backend: _ControlBackend | None = None
_backend_lock = threading.Lock()


def _get_backend() -> _ControlBackend:
    global _control_backend

    if _control_backend is not None:
        return _control_backend
    with _backend_lock:
        if _control_backend is None:
            if os.name == "nt":
                from device_controler.input_controller.windows_backend import (
                    WindowsBackend,
                )

                _control_backend = WindowsBackend()
            elif os.name == "posix":
                from device_controler.input_controller import control

                _control_backend = control
            else:
                raise NotImplementedError(f"Unsupported operating system: {os.name}")
    return _control_backend


def click(x: int, y: int) -> None:
    _get_backend().click(x, y)


def moveTo(x: int, y: int, steps: int, duration: float) -> None:
    _get_backend().moveTo(x, y, steps, duration)


def mouseDown(button: str) -> None:
    _get_backend().mouseDown(button)


def mouseUp(button: str) -> None:
    _get_backend().mouseUp(button)


def keyDown(button: str) -> None:
    _get_backend().keyDown(button)


def keyUp(button: str) -> None:
    _get_backend().keyUp(button)


def position() -> tuple[int, int]:
    return _get_backend().position()


if os.name == "posix":
    from device_controler.input_controller.listener import (
        KeyCallback,
        KeyboardEvent,
        KeyListener,
        listen_keys,
    )
else:
    def listen_keys(*_args: object, **_kwargs: object) -> None:
        raise NotImplementedError("Keyboard listening currently supports Linux only")

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
