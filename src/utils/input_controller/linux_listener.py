# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
"""Listen to all Linux keyboards through evdev.

File path: `src/utils/input_controller/linux_listener.py`

Role:
- Implements the key-listening side of `utils.input_controller` on Linux.
- It should be reached through `utils.input_controller.listen_keys()`.

Input contract:
- `callback` receives `KeyboardEvent(name, event_type, text)`.
- `typeable_only=True` removes keys that cannot produce text.

Output contract:
- Returns `LinuxKeyListener`, a handle with `stop()`.
- Callback runs on this module's daemon thread.

The listener never grabs devices, so input still reaches the desktop. Each loop
closes removed device descriptors and opens newly attached keyboards. SAG virtual
devices are ignored by name so injected input does not loop back into callbacks.

Important assumptions:
- The process can read `/dev/input/event*`.
- Keyboard events follow Linux evdev semantics: `event.value == 1` means key
  down, `0` means key up, and `2` means repeat while held.
"""

from __future__ import annotations

import select
import threading
from typing import cast

from evdev import InputDevice, ecodes, list_devices
from evdev.events import InputEvent
from utils.input_controller.types import EventType, KeyCallback, KeyboardEvent

_VIRTUAL_DEVICE_PREFIX = "SAG Virtual"
_MODIFIERS = {
    ecodes.KEY_LEFTSHIFT,
    ecodes.KEY_RIGHTSHIFT,
}
_TYPEABLE: dict[int, tuple[str, str]] = {
    **{
        getattr(ecodes, f"KEY_{letter}"): (letter.lower(), letter)
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    },
    ecodes.KEY_1: ("1", "!"),
    ecodes.KEY_2: ("2", "@"),
    ecodes.KEY_3: ("3", "#"),
    ecodes.KEY_4: ("4", "$"),
    ecodes.KEY_5: ("5", "%"),
    ecodes.KEY_6: ("6", "^"),
    ecodes.KEY_7: ("7", "&"),
    ecodes.KEY_8: ("8", "*"),
    ecodes.KEY_9: ("9", "("),
    ecodes.KEY_0: ("0", ")"),
    ecodes.KEY_SPACE: (" ", " "),
    ecodes.KEY_MINUS: ("-", "_"),
    ecodes.KEY_EQUAL: ("=", "+"),
    ecodes.KEY_LEFTBRACE: ("[", "{"),
    ecodes.KEY_RIGHTBRACE: ("]", "}"),
    ecodes.KEY_BACKSLASH: ("\\", "|"),
    ecodes.KEY_SEMICOLON: (";", ":"),
    ecodes.KEY_APOSTROPHE: ("'", '"'),
    ecodes.KEY_GRAVE: ("`", "~"),
    ecodes.KEY_COMMA: (",", "<"),
    ecodes.KEY_DOT: (".", ">"),
    ecodes.KEY_SLASH: ("/", "?"),
}

class LinuxKeyListener:
    """Manage a daemon thread and all open physical keyboard descriptors."""

    def __init__(self, callback: KeyCallback, typeable_only: bool) -> None:
        self._callback = callback
        self._typeable_only = typeable_only
        self._stop_event = threading.Event()
        self._devices: dict[str, InputDevice] = {}
        self._shift_codes: dict[str, set[int]] = {}
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the listener thread and close every open keyboard descriptor."""

        self._stop_event.set()
        if self._thread is not threading.current_thread():
            self._thread.join()

    def _run(self) -> None:
        """Poll known keyboards and periodically rescan for hot-plug changes."""

        try:
            while not self._stop_event.is_set():
                self._refresh_devices()
                devices = list(self._devices.values())
                if not devices:
                    self._stop_event.wait(0.5)
                    continue
                try:
                    readable, _, _ = select.select(devices, [], [], 0.5)
                except (OSError, ValueError):
                    self._refresh_devices(force=True)
                    continue
                for device in readable:
                    self._read_device(device)
        finally:
            self._close_all()

    def _refresh_devices(self, force: bool = False) -> None:
        """Synchronize open descriptors with current `/dev/input` devices.

        `force=True` closes all known devices first. This is used after select
        errors because at least one descriptor is likely invalid, but evdev does
        not directly tell us which one.
        """

        paths = set(list_devices())
        for path in set(self._devices) - paths:
            self._close_device(path)
        if force:
            for path in list(self._devices):
                self._close_device(path)
        for path in paths - set(self._devices):
            device: InputDevice | None = None
            try:
                device = InputDevice(path)
                capabilities = device.capabilities(absinfo=False)
                keys = capabilities.get(ecodes.EV_KEY, [])
                # A real keyboard should expose both alphabetic and space keys.
                # This avoids opening mice, touchpads, power buttons, and the
                # SAG virtual devices created by the control backend.
                is_keyboard = ecodes.KEY_A in keys and ecodes.KEY_SPACE in keys
                if is_keyboard and not device.name.startswith(_VIRTUAL_DEVICE_PREFIX):
                    self._devices[path] = device
                else:
                    device.close()
            except OSError:
                if device is not None:
                    device.close()
                continue

    def _read_device(self, device: InputDevice) -> None:
        """Read pending evdev events from one keyboard and emit callbacks."""

        try:
            events = device.read()
        except OSError:
            self._close_device(cast(str, device.path))
            return
        for event in cast(list[InputEvent], events):
            if event.type != ecodes.EV_KEY or event.value not in (0, 1, 2):
                continue
            if event.code in _MODIFIERS:
                path = cast(str, device.path)
                pressed_modifiers = self._shift_codes.setdefault(path, set())
                if event.value == 1:
                    pressed_modifiers.add(event.code)
                elif event.value == 0:
                    pressed_modifiers.discard(event.code)
            text_pair = _TYPEABLE.get(event.code)
            if self._typeable_only and text_pair is None:
                continue
            name = _key_name(event.code)
            shift_active = any(self._shift_codes.values())
            text = text_pair[shift_active] if text_pair is not None else None
            if event.value == 1:
                event_type: EventType = "down"
            elif event.value == 2:
                event_type = "press"
            else:
                event_type = "up"
            try:
                self._callback(KeyboardEvent(name, event_type, text))
            except Exception:
                # Application callback failures must not kill monitoring.
                continue

    def _close_device(self, path: str) -> None:
        self._shift_codes.pop(path, None)
        device = self._devices.pop(path, None)
        if device is not None:
            try:
                device.close()
            except OSError:
                pass

    def _close_all(self) -> None:
        for path in list(self._devices):
            self._close_device(path)


def _key_name(code: int) -> str:
    """Convert a Linux key code to the public lowercase key name."""

    raw_name = ecodes.KEY.get(code, f"KEY_{code}")
    if isinstance(raw_name, list):
        raw_name = raw_name[0]
    return str(raw_name).removeprefix("KEY_").lower()


def listen_keys(callback: KeyCallback, typeable_only: bool = False) -> LinuxKeyListener:
    """Start listening to current and future Linux keyboards."""

    return LinuxKeyListener(callback, typeable_only)


__all__ = ["LinuxKeyListener", "listen_keys"]
