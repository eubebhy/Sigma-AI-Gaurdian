"""Shared listener data contracts for input controller backends.

File path: `src/utils/input_controller/types.py`

Role:
- Defines the public data shape shared by Linux and Windows listener backends.
- Keeps OS-specific event objects out of application code.

Input: Linux/Windows listener backends create `KeyboardEvent` from OS events.
Output: application callbacks receive the same event contract on every OS.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, Protocol, TypeAlias

EventType: TypeAlias = Literal["press", "down", "up"]


@dataclass(frozen=True)
class KeyboardEvent:
    """One physical keyboard state change.

    `name` is a normalized lowercase key name. `event_type` is `down`, `press`,
    or `up`. `text` is the typed character when the key produces text; it is
    `None` for control keys such as escape, ctrl, alt, arrows, and function keys.
    """

    name: str
    event_type: EventType
    text: str | None


KeyCallback: TypeAlias = Callable[[KeyboardEvent], None]


class KeyListener(Protocol):
    """Public handle returned by `listen_keys()`.

    OS-specific implementations may use evdev or pynput internally, but callers
    only need `stop()` to release background listener resources.
    """

    def stop(self) -> None: ...


__all__ = ["EventType", "KeyCallback", "KeyboardEvent", "KeyListener"]
