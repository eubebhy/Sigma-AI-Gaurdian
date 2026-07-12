# pyright: reportPrivateUsage=false
"""Test input controller bang backend gia, khong phat input vao may that.

File path: `tests/input_controller.py`
Input: goi public API voi toa do, mouse button va keyboard key mau.
Output: xac nhan thu tu event, mapping va validation ma khong mo `/dev/uinput`.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from utils import input_controller
from utils.input_controller import linux_backend
from utils.input_controller.windows_backend import WindowsBackend
from utils.input_controller.windows_listener import WindowsKeyListener


class _FakeBackend:
    def __init__(self) -> None:
        self.events: list[tuple[str, int, int]] = []
        self.current_position: tuple[int, int] | None = None

    def move(self, x: int, y: int) -> None:
        self.current_position = (x, y)
        self.events.append(("move", x, y))

    def button(self, code: int, value: int) -> None:
        self.events.append(("button", code, value))

    def key(self, code: int, value: int) -> None:
        self.events.append(("key", code, value))

    def position(self) -> tuple[int, int] | None:
        return self.current_position


class _FakeUInput:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.closed = False
        self.writes: list[tuple[int, int, int]] = []

    def write(self, event_type: int, code: int, value: int) -> None:
        if self.fail:
            raise OSError("device removed")
        self.writes.append((event_type, code, value))

    def syn(self) -> None:
        return

    def close(self) -> None:
        self.closed = True


class _FakePublicBackend:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []

    def click(self, x: int, y: int) -> None:
        self.calls.append(("click", x, y))

    def moveTo(self, x: int, y: int, steps: int, duration: float) -> None:
        self.calls.append(("moveTo", x, y, steps, duration))

    def mouseDown(self, button: str) -> None:
        self.calls.append(("mouseDown", button))

    def mouseUp(self, button: str) -> None:
        self.calls.append(("mouseUp", button))

    def keyDown(self, button: str) -> None:
        self.calls.append(("keyDown", button))

    def keyUp(self, button: str) -> None:
        self.calls.append(("keyUp", button))

    def position(self) -> tuple[int, int]:
        return 12, 34


class _FakeDirectInput:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def click(self, *args: object, **kwargs: object) -> None:
        self.calls.append(("click", args, kwargs))

    def moveTo(self, *args: object, **kwargs: object) -> None:
        self.calls.append(("moveTo", args, kwargs))

    def mouseDown(self, *args: object, **kwargs: object) -> None:
        self.calls.append(("mouseDown", args, kwargs))

    def mouseUp(self, *args: object, **kwargs: object) -> None:
        self.calls.append(("mouseUp", args, kwargs))

    def keyDown(self, *args: object, **kwargs: object) -> bool:
        self.calls.append(("keyDown", args, kwargs))
        return True

    def keyUp(self, *args: object, **kwargs: object) -> bool:
        self.calls.append(("keyUp", args, kwargs))
        return True

    def position(self) -> tuple[int, int]:
        return 0, 0


class _FakeCharKey:
    char = "A"


class _FakeSpecialKey:
    name = "esc"


def test_public_events() -> None:
    """Public API phat dung trang thai va khong chen delay mac dinh."""

    backend = _FakeBackend()
    original_backend = linux_backend._backend
    linux_backend._backend = backend  # type: ignore[assignment]
    try:
        linux_backend.click(20, 30)
        linux_backend.mouseDown("back")
        linux_backend.mouseUp("forward")
        linux_backend.keyDown("a")
        linux_backend.keyUp("enter")
    finally:
        linux_backend._backend = original_backend

    assert backend.events[0] == ("move", 20, 30)
    assert backend.events[1][0::2] == ("button", 1)
    assert backend.events[2][0::2] == ("button", 0)
    assert backend.events[3][0::2] == ("button", 1)
    assert backend.events[4][0::2] == ("button", 0)
    assert backend.events[5][0::2] == ("key", 1)
    assert backend.events[6][0::2] == ("key", 0)


def test_move_steps() -> None:
    """moveTo noi suy dung so buoc va ket thuc chinh xac tai dich."""

    backend = _FakeBackend()
    backend.current_position = (0, 0)
    original_backend = linux_backend._backend
    linux_backend._backend = backend  # type: ignore[assignment]
    try:
        linux_backend.moveTo(30, 15, steps=3, duration=0)
    finally:
        linux_backend._backend = original_backend

    assert backend.events == [
        ("move", 10, 5),
        ("move", 20, 10),
        ("move", 30, 15),
    ]


def test_recreate_removed_virtual_device() -> None:
    """Descriptor hong duoc dong va event duoc thu lai tren device moi."""

    backend = linux_backend._LinuxInputBackend()
    removed_device = _FakeUInput(fail=True)
    replacement = _FakeUInput()
    backend._mouse = removed_device  # type: ignore[assignment]
    backend._create_mouse = lambda: replacement  # type: ignore[method-assign, assignment]

    backend.button(linux_backend.ecodes.BTN_LEFT, 1)

    assert removed_device.closed
    assert replacement.writes == [
        (linux_backend.ecodes.EV_KEY, linux_backend.ecodes.BTN_LEFT, 1)
    ]


def test_public_dispatcher() -> None:
    """Public API dung mot backend da lazy-load va expose position chung."""

    backend = _FakePublicBackend()
    original_backend = input_controller._control_backend
    input_controller._control_backend = backend
    try:
        input_controller.click(4, 5)
        assert input_controller.position() == (12, 34)
    finally:
        input_controller._control_backend = original_backend

    assert backend.calls == [("click", 4, 5)]


def test_windows_backend_has_no_implicit_delay() -> None:
    """Adapter Windows ep delay ve 0 va map hai nut chuot ben hong."""

    direct_input = _FakeDirectInput()
    backend = WindowsBackend.__new__(WindowsBackend)
    backend._input = direct_input  # type: ignore[assignment]

    backend.click(10, 20)
    backend.moveTo(20, 10, steps=2, duration=0)
    backend.mouseDown("back")
    backend.mouseUp("forward")
    backend.keyDown("leftctrl")
    backend.keyUp("leftctrl")

    for name, _, kwargs in direct_input.calls:
        if name != "position":
            assert kwargs.get("_pause") is False
    assert direct_input.calls[0][2]["duration"] == 0
    assert direct_input.calls[0][2]["interval"] == 0
    assert direct_input.calls[3][2]["button"] == "x1"
    assert direct_input.calls[4][2]["button"] == "x2"
    assert direct_input.calls[5][1] == ("ctrlleft",)
    assert direct_input.calls[6][1] == ("ctrlleft",)


def test_windows_listener_typeable_filter() -> None:
    """Windows listener bang pynput giu dung contract KeyboardEvent."""

    events: list[tuple[str, str, str | None]] = []

    def callback(event: input_controller.KeyboardEvent) -> None:
        events.append((event.name, event.event_type, event.text))

    listener = WindowsKeyListener.__new__(WindowsKeyListener)
    listener._callback = callback
    listener._typeable_only = True

    listener._on_press(_FakeCharKey())
    listener._on_press(_FakeSpecialKey())

    assert events == [("a", "down", "A")]


def main() -> None:
    test_public_events()
    test_move_steps()
    test_recreate_removed_virtual_device()
    test_public_dispatcher()
    test_windows_backend_has_no_implicit_delay()
    test_windows_listener_typeable_filter()


if __name__ == "__main__":
    main()
    print("PASS: input_controller")
