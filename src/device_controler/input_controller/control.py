# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
"""Phat input chuot va ban phim Linux bang evdev UInput.

File path: `src/device_controler/input_controller/control.py`
Input: toa do pixel, ten nut chuot, hoac ten phim Linux thong dung.
Output: su kien input duoc kernel phat cho desktop X11 hoac Wayland.

Hai thiet bi ao duoc giu lai de tranh chi phi khoi tao moi lan. Neu kernel xoa
thiet bi hoac descriptor hong, lan ghi dang loi se dong backend cu, tao lai va
thu dung mot lan. Tat ca write va recreate duoc khoa de an toan giua cac thread.
"""

from __future__ import annotations

import atexit
import threading
import time
import tkinter as tk
from typing import Any, cast

from evdev import AbsInfo, UInput, ecodes

_ABS_MAX = 65_535
_VIRTUAL_MOUSE_NAME = "SAG Virtual Mouse"
_VIRTUAL_KEYBOARD_NAME = "SAG Virtual Keyboard"

_BUTTON_CODES: dict[str, int] = {
    "left": ecodes.BTN_LEFT,
    "right": ecodes.BTN_RIGHT,
    "middle": ecodes.BTN_MIDDLE,
    "back": ecodes.BTN_SIDE,
    "side": ecodes.BTN_SIDE,
    "forward": ecodes.BTN_EXTRA,
    "extra": ecodes.BTN_EXTRA,
}

_KEY_ALIASES: dict[str, str] = {
    "alt": "LEFTALT",
    "backspace": "BACKSPACE",
    "ctrl": "LEFTCTRL",
    "delete": "DELETE",
    "down": "DOWN",
    "enter": "ENTER",
    "esc": "ESC",
    "escape": "ESC",
    "left": "LEFT",
    "return": "ENTER",
    "right": "RIGHT",
    "shift": "LEFTSHIFT",
    "space": "SPACE",
    "super": "LEFTMETA",
    "tab": "TAB",
    "up": "UP",
    "win": "LEFTMETA",
}


class _InputBackend:
    """Quan ly vong doi hai thiet bi ao va serialize moi lan ghi."""

    def __init__(self) -> None:
        self._mouse: UInput | None = None
        self._keyboard: UInput | None = None
        self._lock = threading.RLock()
        self._screen_size: tuple[int, int] | None = None
        self._position: tuple[int, int] | None = None

    def _create_mouse(self) -> UInput:
        axis = AbsInfo(0, 0, _ABS_MAX, 0, 0, 0)
        capabilities = cast(
            Any,
            {
                ecodes.EV_KEY: list(_BUTTON_CODES.values()),
                ecodes.EV_ABS: [(ecodes.ABS_X, axis), (ecodes.ABS_Y, axis)],
            },
        )
        return UInput(
            capabilities,
            name=_VIRTUAL_MOUSE_NAME,
            input_props=[ecodes.INPUT_PROP_POINTER],
        )

    def _create_keyboard(self) -> UInput:
        key_codes = [
            code
            for name, code in ecodes.ecodes.items()
            if name.startswith("KEY_")
        ]
        return UInput(
            {ecodes.EV_KEY: sorted(set(key_codes))},
            name=_VIRTUAL_KEYBOARD_NAME,
        )

    def _write(self, kind: str, event_type: int, code: int, value: int) -> None:
        with self._lock:
            for attempt in range(2):
                device = self._mouse if kind == "mouse" else self._keyboard
                if device is None:
                    device = self._create_mouse() if kind == "mouse" else self._create_keyboard()
                    if kind == "mouse":
                        self._mouse = device
                    else:
                        self._keyboard = device
                try:
                    device.write(event_type, code, value)
                    device.syn()
                    return
                except OSError:
                    self._close_kind(kind)
                    if attempt == 1:
                        raise

    def button(self, code: int, value: int) -> None:
        self._write("mouse", ecodes.EV_KEY, code, value)

    def key(self, code: int, value: int) -> None:
        self._write("keyboard", ecodes.EV_KEY, code, value)

    def move(self, x: int, y: int) -> None:
        width, height = self.screen_size()
        x = min(max(x, 0), width - 1)
        y = min(max(y, 0), height - 1)
        abs_x = round(x * _ABS_MAX / max(width - 1, 1))
        abs_y = round(y * _ABS_MAX / max(height - 1, 1))
        with self._lock:
            self._write("mouse", ecodes.EV_ABS, ecodes.ABS_X, abs_x)
            self._write("mouse", ecodes.EV_ABS, ecodes.ABS_Y, abs_y)
            self._position = (x, y)

    def screen_size(self) -> tuple[int, int]:
        if self._screen_size is not None:
            return self._screen_size
        root = tk.Tk()
        root.withdraw()
        try:
            width = root.winfo_vrootwidth() or root.winfo_screenwidth()
            height = root.winfo_vrootheight() or root.winfo_screenheight()
        finally:
            root.destroy()
        self._screen_size = (max(width, 1), max(height, 1))
        return self._screen_size

    def position(self) -> tuple[int, int] | None:
        return self._position

    def _close_kind(self, kind: str) -> None:
        device = self._mouse if kind == "mouse" else self._keyboard
        if device is not None:
            try:
                device.close()
            except OSError:
                pass
        if kind == "mouse":
            self._mouse = None
        else:
            self._keyboard = None

    def close(self) -> None:
        with self._lock:
            self._close_kind("mouse")
            self._close_kind("keyboard")


def _resolve_button(button: str) -> int:
    code = _BUTTON_CODES.get(button.strip().lower())
    if code is None:
        raise ValueError(f"Unsupported mouse button: {button}")
    return code


def _resolve_key(button: str) -> int:
    value = button.strip().upper().replace(" ", "_")
    value = _KEY_ALIASES.get(value.lower(), value)
    code = ecodes.ecodes.get(f"KEY_{value}")
    if not isinstance(code, int):
        raise ValueError(f"Unsupported keyboard key: {button}")
    return code


def click(x: int, y: int) -> None:
    """Di ngay den `(x, y)` roi click trai khong chen delay."""

    with _pointer_lock:
        _backend.move(x, y)
        _backend.button(ecodes.BTN_LEFT, 1)
        _backend.button(ecodes.BTN_LEFT, 0)


def moveTo(x: int, y: int, steps: int, duration: float) -> None:
    """Di den `(x, y)` qua `steps` moc trong tong `duration` giay.

    Wayland khong cho ung dung doc toa do con tro toan cuc. Vi vay lan goi dau
    tien di thang den dich; cac lan sau noi suy tu vi tri gan nhat do SAG dat.
    """

    if steps <= 0:
        raise ValueError("steps must be greater than zero")
    if duration < 0:
        raise ValueError("duration must not be negative")
    with _pointer_lock:
        start = _backend.position()
        if start is None or steps == 1:
            _backend.move(x, y)
            return
        started_at = time.monotonic()
        for index in range(1, steps + 1):
            progress = index / steps
            next_x = round(start[0] + (x - start[0]) * progress)
            next_y = round(start[1] + (y - start[1]) * progress)
            _backend.move(next_x, next_y)
            deadline = started_at + duration * progress
            remaining = deadline - time.monotonic()
            if remaining > 0:
                time.sleep(remaining)


def mouseDown(button: str) -> None:
    """Nhan va giu nut chuot ngay lap tuc."""

    _backend.button(_resolve_button(button), 1)


def mouseUp(button: str) -> None:
    """Nha nut chuot ngay lap tuc."""

    _backend.button(_resolve_button(button), 0)


def keyDown(button: str) -> None:
    """Nhan va giu phim ban phim ngay lap tuc."""

    _backend.key(_resolve_key(button), 1)


def keyUp(button: str) -> None:
    """Nha phim ban phim ngay lap tuc."""

    _backend.key(_resolve_key(button), 0)


def position() -> tuple[int, int]:
    """Tra toa do con tro ma desktop hien tai bao cao.

    X11 tra toa do con tro toan cuc. Wayland co the chi tra toa do qua lop
    XWayland; neu compositor khong cho doc thi dung vi tri gan nhat SAG da dat.
    """

    root = tk.Tk()
    root.withdraw()
    try:
        x, y = root.winfo_pointerxy()
        return int(x), int(y)
    except tk.TclError:
        tracked = _backend.position()
        if tracked is None:
            raise RuntimeError("Current pointer position is unavailable on this session")
        return tracked
    finally:
        root.destroy()


_backend = _InputBackend()
_pointer_lock = threading.RLock()
atexit.register(_backend.close)

__all__ = ["click", "keyDown", "keyUp", "mouseDown", "mouseUp", "moveTo", "position"]
