"""Windows control backend for `utils.input_controller`.

File path: `src/utils/input_controller/windows_backend.py`
Input: same coordinates, mouse button names, and key names as the public facade.
Output: Windows input sent through `pydirectinput-rgx` without implicit delay.

`pydirectinput-rgx` imports as `pydirectinput`. This module imports it only when
`WindowsBackend` is constructed, so Linux users can import the public package
without installing Windows-only dependencies.

Important assumption:
- The public API owns timing. Therefore this backend sets `PAUSE = 0` and passes
  `_pause=False`, `duration=0`, and `interval=0` where supported. Only the
  public `moveTo(..., duration=...)` argument may intentionally wait.
"""

from __future__ import annotations

import importlib
import time
from typing import Protocol, cast


class _DirectInput(Protocol):
    PAUSE: float

    def click(self, **kwargs: object) -> None: ...

    def moveTo(self, x: int, y: int, **kwargs: object) -> None: ...

    def mouseDown(self, **kwargs: object) -> None: ...

    def mouseUp(self, **kwargs: object) -> None: ...

    def keyDown(self, key: str, **kwargs: object) -> bool: ...

    def keyUp(self, key: str, **kwargs: object) -> bool: ...

    def position(self) -> tuple[int, int]: ...


class WindowsBackend:
    """Adapter that maps the public SAG API to pydirectinput-rgx."""

    def __init__(self) -> None:
        direct_input = cast(_DirectInput, importlib.import_module("pydirectinput"))
        direct_input.PAUSE = 0
        self._input = direct_input

    def click(self, x: int, y: int) -> None:
        self._input.click(x=x, y=y, duration=0, interval=0, _pause=False)

    def moveTo(self, x: int, y: int, steps: int, duration: float) -> None:
        """Move using SAG's explicit step/duration contract.

        pydirectinput can perform its own timed movement, but this wrapper keeps
        timing in this project so Linux and Windows behavior stay comparable.
        """

        if steps <= 0:
            raise ValueError("steps must be greater than zero")
        if duration < 0:
            raise ValueError("duration must not be negative")
        start_x, start_y = self.position()
        started_at = time.monotonic()
        for index in range(1, steps + 1):
            progress = index / steps
            next_x = round(start_x + (x - start_x) * progress)
            next_y = round(start_y + (y - start_y) * progress)
            self._input.moveTo(next_x, next_y, duration=0, _pause=False)
            remaining = started_at + duration * progress - time.monotonic()
            if remaining > 0:
                time.sleep(remaining)

    def mouseDown(self, button: str) -> None:
        self._input.mouseDown(button=_mouse_button(button), duration=0, _pause=False)

    def mouseUp(self, button: str) -> None:
        self._input.mouseUp(button=_mouse_button(button), duration=0, _pause=False)

    def keyDown(self, button: str) -> None:
        key = _keyboard_key(button)
        if not self._input.keyDown(key, _pause=False):
            raise ValueError(f"Unsupported keyboard key: {button}")

    def keyUp(self, button: str) -> None:
        key = _keyboard_key(button)
        if not self._input.keyUp(key, _pause=False):
            raise ValueError(f"Unsupported keyboard key: {button}")

    def position(self) -> tuple[int, int]:
        x, y = self._input.position()
        return int(x), int(y)


def _mouse_button(button: str) -> str:
    """Map public mouse button names to pydirectinput-rgx button names."""

    normalized = button.strip().lower()
    aliases = {"back": "x1", "side": "x1", "forward": "x2", "extra": "x2"}
    resolved = aliases.get(normalized, normalized)
    if resolved not in {"left", "right", "middle", "primary", "secondary", "x1", "x2"}:
        raise ValueError(f"Unsupported mouse button: {button}")
    return resolved


def _keyboard_key(button: str) -> str:
    """Map public key names to pydirectinput-rgx key names.

    Example: Linux-style `leftctrl` becomes pydirectinput's `ctrlleft`.
    """

    normalized = button.strip().lower().replace(" ", "")
    aliases = {
        "leftalt": "altleft",
        "rightalt": "altright",
        "leftctrl": "ctrlleft",
        "rightctrl": "ctrlright",
        "leftshift": "shiftleft",
        "rightshift": "shiftright",
        "leftmeta": "winleft",
        "rightmeta": "winright",
        "super": "win",
    }
    return aliases.get(normalized, normalized)


__all__ = ["WindowsBackend"]
