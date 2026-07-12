# Input Controller

`utils.input_controller` is the stable input API used by the application. It
hides OS-specific input libraries behind one public module so higher-level code
does not need to know whether the machine is running Linux or Windows.

## Public API

```python
from utils.input_controller import (
    KeyboardEvent,
    click,
    keyDown,
    keyUp,
    listen_keys,
    mouseDown,
    mouseUp,
    moveTo,
    position,
)

click(500, 300)
moveTo(900, 500, steps=20, duration=0.3)
mouseDown("left")
mouseUp("left")
keyDown("leftctrl")
keyUp("leftctrl")
print(position())


def on_key(event: KeyboardEvent) -> None:
    print(event.name, event.event_type, event.text)


listener = listen_keys(on_key, typeable_only=True)
listener.stop()
```

Mouse buttons: `left`, `right`, `middle`, `back`, `forward`.
Keyboard names are normalized by each backend. Common names such as `a`,
`enter`, `space`, `leftctrl`, and `rightshift` are intended to work through the
public API.

## File Map

- `__init__.py`: public facade and lazy backend selection.
- `linux_backend.py`: Linux mouse/keyboard control with `evdev.UInput`.
- `windows_backend.py`: Windows mouse/keyboard control with `pydirectinput-rgx`.
- `linux_listener.py`: Linux keyboard listener with `evdev`.
- `windows_listener.py`: Windows keyboard listener with `pynput`.
- `types.py`: shared callback types: `KeyboardEvent`, `KeyCallback`, `KeyListener`.

The Linux-specific files include `linux` in the file name so readers can tell
which modules touch `/dev/input` and `/dev/uinput`.

## Backend Selection

Importing `utils.input_controller` does not immediately create devices or start
keyboard hooks. Backends are loaded only when the matching public API is called.
This matters because Linux and Windows dependencies are not interchangeable:
`evdev` is Linux-only, while `pydirectinput-rgx` and `pynput` are only needed for
Windows behavior.

Control calls use this path:

```text
click/keyDown/moveTo/...
-> __init__._get_backend()
-> Linux: import linux_backend
-> Windows: create WindowsBackend from windows_backend
-> call the selected backend function
```

Listener calls use a separate but similar path:

```text
listen_keys(callback, typeable_only)
-> __init__._get_listener_backend()
-> Linux: import linux_listener
-> Windows: import windows_listener
-> call backend listen_keys(...)
-> return a KeyListener-compatible handle with stop()
```

`_backend_lock` protects the lazy selection step. It prevents two threads from
creating/importing the same backend at the same time during the first call.
The lock is not a global input-operation lock. After backend selection, threading
rules belong to the selected backend module.

## Threading Overview

There are three independent layers of threading concerns:

- Facade lazy loading: `__init__._backend_lock` protects first-time backend
  selection only.
- Linux control writes: `linux_backend._pointer_lock` protects multi-step pointer
  workflows, while `_LinuxInputBackend._lock` protects UInput file descriptors.
- Listener callbacks: Linux uses a daemon thread owned by `LinuxKeyListener`;
  Windows uses the hook thread owned by `pynput.keyboard.Listener`.

Application callbacks are called from listener threads. If a callback needs to
update UI state, database state, or shared AI-agent state, it should hand work to
the owning thread or a queue instead of doing long blocking work inside the
listener callback.

## Linux Control Backend

`linux_backend.py` creates two virtual devices with `evdev.UInput`:

- `SAG Virtual Mouse`
- `SAG Virtual Keyboard`

The virtual mouse uses absolute pointer coordinates, so the same control path is
usable on both X11 and Wayland. Wayland may not allow reading the real global
pointer position; in that case `position()` falls back to the last pointer
coordinate set by SAG.

Linux absolute input detail:

```text
desktop pixel x/y
-> clamp to current screen size
-> scale to UInput ABS_X/ABS_Y range 0..65535
-> write EV_ABS events
-> write SYN_REPORT via evdev's syn()
```

This conversion is why the backend needs both screen size and the `_ABS_MAX`
constant. Desktop code should not pass already-scaled evdev values; the public
API always expects pixels.

The backend keeps virtual devices open for long-running performance. If a write
fails with `OSError`, the backend closes the broken device, recreates it, and
retries the write once. This handles cases where a virtual input device is
removed or its descriptor becomes invalid.

Linux permission requirements:

- read `/dev/input/event*` for listening;
- write `/dev/uinput` for control;
- load the `uinput` kernel module.

Use group/udev permissions when possible instead of running the whole app as
root.

## Windows Control Backend

`windows_backend.py` imports `pydirectinput` from the `pydirectinput-rgx`
package only when Windows control is first used.

The backend disables implicit delays:

- sets `pydirectinput.PAUSE = 0`;
- passes `_pause=False` on calls;
- passes `duration=0` and `interval=0` when the underlying API has those
  parameters.

Only `moveTo(..., duration=...)` intentionally waits, because `duration` is part
of the public SAG API.

## Keyboard Listener

`listen_keys(callback, typeable_only=False)` is the one public listener API on
both supported operating systems.

The callback receives:

```python
KeyboardEvent(
    name="a",
    event_type="down",  # or "press" / "up"
    text="a",           # None for non-text keys
)
```

When `typeable_only=True`, listeners only emit keys that can produce text, such
as letters, digits, spaces, and punctuation. Control keys such as `esc`, `ctrl`,
`alt`, and `super` are filtered out.

Linux listener behavior:

- scans all `/dev/input/event*` keyboard devices;
- listens to all physical keyboards at the same time;
- does not grab devices, so input still reaches the desktop;
- rescans to handle keyboard hot-plug and removal;
- ignores SAG virtual devices by name to avoid callback loops.

Linux evdev key state detail:

```text
event.value == 1 -> key down
event.value == 0 -> key up
event.value == 2 -> repeat while held
```

The public API reports repeat events as `event_type="press"`.
`typeable_only=True` is implemented from a small US-style printable-key table in
`linux_listener.py`; it is intended for simple character monitoring, not full IME
or arbitrary layout reconstruction.

Windows listener behavior:

- uses `pynput.keyboard.Listener`;
- keeps the same `KeyboardEvent` contract as Linux;
- returns a handle with `stop()`.

Callback exceptions are caught inside listener backends so one bad callback call
does not kill long-running input monitoring.

## Maintenance Notes

When adding a new public input API:

1. Add the function to `__init__.py` first, with the public contract documented.
2. Add the same method to `_ControlBackend` if it is a control API.
3. Implement it in both `linux_backend.py` and `windows_backend.py`.
4. Keep OS-specific imports inside backend files or lazy selection functions.
5. Update this README with any new input/output formats or threading assumptions.

When changing listener event shape, update `types.py` first. That file is the
contract between OS-specific backends and the rest of the application.
