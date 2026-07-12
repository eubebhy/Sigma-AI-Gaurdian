"""Backend Windows cua input controller dung `pydirectinput-rgx`.

File path: `src/device_controler/input_controller/windows_backend.py`
Input: cung contract toa do, button va key voi public input controller.
Output: input Windows duoc gui bang DirectInput va khong co delay ngam.

Module thu vien co ten import la `pydirectinput`. No chi duoc import khi
`WindowsBackend` duoc tao lan dau. `PAUSE` va `MINIMUM_DURATION` duoc dat ve 0;
tat ca loi goi cung truyen `_pause=False`, `duration=0` hoac `interval=0` neu API
thu vien co tham so tuong ung.
"""

from __future__ import annotations

import importlib
import time
from typing import Protocol, cast


class _Point(Protocol):
    x: int
    y: int


class _DirectInput(Protocol):
    PAUSE: float
    MINIMUM_DURATION: float

    def click(self, **kwargs: object) -> None: ...

    def moveTo(self, x: int, y: int, **kwargs: object) -> None: ...

    def mouseDown(self, **kwargs: object) -> None: ...

    def mouseUp(self, **kwargs: object) -> None: ...

    def keyDown(self, key: str, **kwargs: object) -> None: ...

    def keyUp(self, key: str, **kwargs: object) -> None: ...

    def position(self) -> _Point: ...


class WindowsBackend:
    """Adapter giu public API SAG on dinh tren pydirectinput-rgx."""

    def __init__(self) -> None:
        direct_input = cast(_DirectInput, importlib.import_module("pydirectinput"))
        direct_input.PAUSE = 0
        direct_input.MINIMUM_DURATION = 0
        self._input = direct_input

    def click(self, x: int, y: int) -> None:
        self._input.click(x=x, y=y, duration=0, interval=0, _pause=False)

    def moveTo(self, x: int, y: int, steps: int, duration: float) -> None:
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
        self._input.mouseDown(button=button, duration=0, _pause=False)

    def mouseUp(self, button: str) -> None:
        self._input.mouseUp(button=button, duration=0, _pause=False)

    def keyDown(self, button: str) -> None:
        self._input.keyDown(button, _pause=False)

    def keyUp(self, button: str) -> None:
        self._input.keyUp(button, _pause=False)

    def position(self) -> tuple[int, int]:
        point = self._input.position()
        return int(point.x), int(point.y)


__all__ = ["WindowsBackend"]
