# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
"""Send mouse and keyboard input on Linux with evdev UInput.

File path: `src/utils/input_controller/linux_backend.py`

Role:
- Implements the control side of `utils.input_controller` on Linux.
- Use through the public facade in `utils.input_controller`, not by importing
  this module directly from application code.

Input contract:
- Mouse coordinates are desktop pixels. They are converted to Linux absolute
  axis values in the range `0..65535` before being written to UInput.
- Mouse buttons use Linux `BTN_*` codes.
- Keyboard keys use Linux `KEY_*` codes.

Output contract:
- Events are written to two virtual kernel devices: one mouse and one keyboard.
- Functions return after the kernel write succeeds or raises the final error.

Important assumptions:
- The process can write `/dev/uinput` and the `uinput` kernel module is loaded.
- Absolute pointer events are handled by the active desktop compositor. This is
  the portable path used for both X11 and Wayland.
- Wayland often blocks reading true global pointer position. The module stores
  the last position that SAG set and uses it as a fallback.

Threading model:
- `_pointer_lock` serializes high-level pointer workflows such as `click()` and
  `moveTo()` so another thread cannot move the cursor between a move and click.
- `_LinuxInputBackend._lock` serializes low-level UInput device creation, writes,
  close, and recreate operations.

Failure model:
- A virtual input device can disappear or its file descriptor can become invalid
  in long-running sessions. On `OSError`, `_write()` closes the broken device,
  recreates it, and retries the same event once.
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


class _LinuxInputBackend:
    """Own the Linux virtual mouse and keyboard devices.

    The object is process-global because UInput device creation is relatively
    expensive and creating many virtual devices makes desktop input harder to
    reason about. Public functions call this object to emit individual events.
    """

    def __init__(self) -> None:
        self._mouse: UInput | None = None
        self._keyboard: UInput | None = None
        self._lock = threading.RLock()
        self._screen_size: tuple[int, int] | None = None
        self._position: tuple[int, int] | None = None

    def _create_mouse(self) -> UInput:
        """Create the virtual absolute-position mouse device.

        Linux absolute axes do not use desktop pixels directly. They use a device
        range declared at creation time; this backend declares `0..65535` and
        converts pixel coordinates in `move()`.
        """

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
        """Create a virtual keyboard that can emit Linux `KEY_*` codes.

        The capability list is intentionally broad so public key names can be
        added without recreating this device definition for each key.
        """

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
        """Write one input event to a virtual device and retry once on failure.

        `kind` selects the virtual mouse or keyboard. Each successful event is
        followed by `syn()` so the kernel reports it immediately. If the device
        descriptor is stale, closing and recreating the selected device is safer
        than trying to reuse unknown kernel state.
        """

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
                    # Long-running Linux sessions may lose the virtual device;
                    # recreate only the failed device type and replay the event.
                    self._close_kind(kind)
                    if attempt == 1:
                        raise

    def button(self, code: int, value: int) -> None:
        self._write("mouse", ecodes.EV_KEY, code, value)

    def key(self, code: int, value: int) -> None:
        self._write("keyboard", ecodes.EV_KEY, code, value)

    def move(self, x: int, y: int) -> None:
        """Move the virtual pointer to desktop pixel coordinates.

        Input pixels are clamped to the current desktop size, then converted to
        the absolute UInput axis range. The final pixel position is remembered so
        `moveTo()` can interpolate even when Wayland hides the real pointer.
        """

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
    """Translate a public mouse button name to a Linux `BTN_*` code."""

    code = _BUTTON_CODES.get(button.strip().lower())
    if code is None:
        raise ValueError(f"Unsupported mouse button: {button}")
    return code


def _resolve_key(button: str) -> int:
    """Translate a public key name to a Linux `KEY_*` code.

    Public callers use readable names such as `leftctrl`; evdev requires numeric
    Linux key codes such as `KEY_LEFTCTRL`. `_KEY_ALIASES` bridges common names
    that do not match the Linux suffix exactly.
    """

    value = button.strip().upper().replace(" ", "_")
    value = _KEY_ALIASES.get(value.lower(), value)
    code = ecodes.ecodes.get(f"KEY_{value}")
    if not isinstance(code, int):
        raise ValueError(f"Unsupported keyboard key: {button}")
    return code


def click(x: int, y: int) -> None:
    """Move to `(x, y)` and emit left-button down/up without delay."""

    with _pointer_lock:
        _backend.move(x, y)
        _backend.button(ecodes.BTN_LEFT, 1)
        _backend.button(ecodes.BTN_LEFT, 0)


def moveTo(x: int, y: int, steps: int, duration: float) -> None:
    """Move to `(x, y)` through `steps` points over `duration` seconds.

    Wayland does not reliably expose the current global pointer location. The
    first call in a process may jump directly to the destination; later calls use
    the last coordinate set by this backend as the interpolation start.
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
    """Press and hold a mouse button immediately."""

    _backend.button(_resolve_button(button), 1)


def mouseUp(button: str) -> None:
    """Release a mouse button immediately."""

    _backend.button(_resolve_button(button), 0)


def keyDown(button: str) -> None:
    """Press and hold a keyboard key immediately."""

    _backend.key(_resolve_key(button), 1)


def keyUp(button: str) -> None:
    """Release a keyboard key immediately."""

    _backend.key(_resolve_key(button), 0)


def position() -> tuple[int, int]:
    """Return current pointer coordinates when the desktop exposes them.

    X11 commonly reports the real global pointer. Wayland may return no usable
    coordinates, so this falls back to the last coordinate set by SAG. If neither
    source exists, the function raises because there is no truthful value to
    return.
    """

    root: tk.Tk | None = None
    try:
        root = tk.Tk()
        root.withdraw()
        x, y = root.winfo_pointerxy()
        if x >= 0 and y >= 0:
            return int(x), int(y)
    except tk.TclError:
        pass
    finally:
        if root is not None:
            root.destroy()
    tracked = _backend.position()
    if tracked is None:
        raise RuntimeError("Current pointer position is unavailable on this session")
    return tracked


_backend = _LinuxInputBackend()
_pointer_lock = threading.RLock()
atexit.register(_backend.close)

__all__ = ["click", "keyDown", "keyUp", "mouseDown", "mouseUp", "moveTo", "position"]
