# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
"""Lang nghe dong thoi tat ca ban phim Linux qua evdev.

File path: `src/device_controler/input_controller/listener.py`
Input: callback nhan `KeyboardEvent`; `typeable_only=True` loc bo phim dieu khien.
Output: callback duoc goi real-time cho trang thai `down` va `up`.

Listener khong grab thiet bi, nen input van den desktop binh thuong. Moi vong quet
se dong descriptor da bi rut va mo keyboard moi gan vao. Thiet bi ao cua SAG bi
loai theo ten de input do chinh ung dung phat khong quay nguoc vao callback.
"""

from __future__ import annotations

import select
import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, TypeAlias, cast

from evdev import InputDevice, ecodes, list_devices
from evdev.events import InputEvent

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

EventType: TypeAlias = Literal["down", "up"]


@dataclass(frozen=True)
class KeyboardEvent:
    """Mot thay doi trang thai phim vat ly.

    `name` la ten Linux da ha chu, `event_type` la `down` hoac `up`, va `text`
    la ky tu tuong ung neu phim co the go duoc. Repeat cua kernel khong duoc gui.
    """

    name: str
    event_type: EventType
    text: str | None


KeyCallback: TypeAlias = Callable[[KeyboardEvent], None]


class KeyListener:
    """Quan ly background thread va cac descriptor cua keyboard vat ly."""

    def __init__(self, callback: KeyCallback, typeable_only: bool) -> None:
        self._callback = callback
        self._typeable_only = typeable_only
        self._stop_event = threading.Event()
        self._devices: dict[str, InputDevice] = {}
        self._shift_codes: dict[str, set[int]] = {}
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Dung thread va dong tat ca keyboard descriptor dang mo."""

        self._stop_event.set()
        if self._thread is not threading.current_thread():
            self._thread.join()

    def _run(self) -> None:
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
        try:
            events = device.read()
        except OSError:
            self._close_device(cast(str, device.path))
            return
        for event in cast(list[InputEvent], events):
            if event.type != ecodes.EV_KEY or event.value not in (0, 1):
                continue
            if event.code in _MODIFIERS:
                path = cast(str, device.path)
                pressed_modifiers = self._shift_codes.setdefault(path, set())
                if event.value == 1:
                    pressed_modifiers.add(event.code)
                else:
                    pressed_modifiers.discard(event.code)
            text_pair = _TYPEABLE.get(event.code)
            if self._typeable_only and text_pair is None:
                continue
            name = _key_name(event.code)
            shift_active = any(self._shift_codes.values())
            text = text_pair[shift_active] if text_pair is not None else None
            event_type: EventType = "down" if event.value == 1 else "up"
            try:
                self._callback(KeyboardEvent(name, event_type, text))
            except Exception:
                # Loi cua app khong duoc lam mat listener input lau dai.
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
    raw_name = ecodes.KEY.get(code, f"KEY_{code}")
    if isinstance(raw_name, list):
        raw_name = raw_name[0]
    return str(raw_name).removeprefix("KEY_").lower()


def listen_keys(callback: KeyCallback, typeable_only: bool = False) -> KeyListener:
    """Bat dau lang nghe moi keyboard hien tai va keyboard gan vao sau do."""

    return KeyListener(callback, typeable_only)


__all__ = ["KeyCallback", "KeyboardEvent", "KeyListener", "listen_keys"]
