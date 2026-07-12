# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
"""Listen to Windows keyboard events through pynput.

File path: `src/utils/input_controller/windows_listener.py`
Input: callback that receives `KeyboardEvent`; `typeable_only=True` emits only
keys with typed characters.
Output: callback is called in real time for `down`, `press`, and `up` key states.

`pynput` is imported only when a Windows listener is created. This keeps the
public package importable on Linux without Windows listener dependencies.

Threading model:
- pynput owns the OS keyboard hook thread.
- This wrapper converts pynput key objects into the shared `KeyboardEvent`
  contract before invoking the application callback.
"""

from __future__ import annotations

import importlib
from typing import Protocol, cast

from utils.input_controller.types import EventType, KeyCallback, KeyboardEvent


class _PynputListener(Protocol):
    def start(self) -> None: ...

    def stop(self) -> None: ...

    def join(self, timeout: float | None = None) -> None: ...


class _KeyboardModule(Protocol):
    def Listener(self, **kwargs: object) -> _PynputListener: ...


class WindowsKeyListener:
    """Manage the pynput listener object returned to public callers."""

    def __init__(self, callback: KeyCallback, typeable_only: bool) -> None:
        self._callback = callback
        self._typeable_only = typeable_only
        self._pressed_names: set[str] = set()
        keyboard = cast(_KeyboardModule, importlib.import_module("pynput.keyboard"))
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.start()

    def stop(self) -> None:
        """Stop pynput's hook thread and wait briefly for it to exit."""

        self._listener.stop()
        self._listener.join(timeout=2.0)

    def _on_press(self, key: object) -> None:
        name, text = _key_parts(key)
        if not hasattr(self, "_pressed_names"):
            self._pressed_names = set()
        event_type: EventType = "press" if name in self._pressed_names else "down"
        self._pressed_names.add(name)
        self._emit(name, text, event_type)

    def _on_release(self, key: object) -> None:
        name, text = _key_parts(key)
        if not hasattr(self, "_pressed_names"):
            self._pressed_names = set()
        self._pressed_names.discard(name)
        self._emit(name, text, "up")

    def _emit(self, name: str, text: str | None, event_type: EventType) -> None:
        """Emit one normalized key event through the shared callback contract."""

        if self._typeable_only and text is None:
            return
        try:
            self._callback(KeyboardEvent(name, event_type, text))
        except Exception:
            # Application callback failures must not kill the keyboard hook.
            return


def _key_parts(key: object) -> tuple[str, str | None]:
    """Return `(name, text)` from a pynput key object.

    Printable keys usually have `.char`; special keys usually have `.name` or a
    string form such as `Key.esc`. `text` is only set for printable characters.
    """

    char = cast(str | None, getattr(key, "char", None))
    if char:
        return char.lower(), char
    name = cast(str | None, getattr(key, "name", None))
    if name:
        return name.lower(), None
    raw = str(key)
    return raw.removeprefix("Key.").lower(), None


def listen_keys(callback: KeyCallback, typeable_only: bool = False) -> WindowsKeyListener:
    """Start listening to Windows keyboard events through pynput."""

    return WindowsKeyListener(callback, typeable_only)


__all__ = ["WindowsKeyListener", "listen_keys"]
