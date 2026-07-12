# Input Controller

Package nay cung cap API input on dinh cho Linux X11 va Wayland bang `evdev`.
Khong ham nao chen delay ngam; chi `moveTo()` cho theo `duration` duoc truyen vao.

## Quyen he thong

Process can doc `/dev/input/event*` de nghe keyboard va ghi `/dev/uinput` de phat
input. Nen cap quyen bang group/udev rule thay vi chay ca ung dung bang root.
Kernel module `uinput` phai duoc load.

## Dieu khien

```python
from device_controler.input_controller import (
    click,
    keyDown,
    keyUp,
    mouseDown,
    mouseUp,
    moveTo,
)

click(500, 300)
moveTo(900, 500, steps=20, duration=0.3)
mouseDown("left")
mouseUp("left")
keyDown("leftctrl")
keyUp("leftctrl")
```

Mouse button hop le: `left`, `right`, `middle`, `back`, `forward`. Keyboard
nhan ten `KEY_*` cua Linux sau khi bo prefix va khong phan biet hoa thuong.

Absolute pointer cua kernel duoc compositor xu ly tren ca X11 va Wayland. Do
Wayland khong cho doc toa do con tro toan cuc, lan `moveTo()` dau tien cua process
di thang den dich. Cac lan sau noi suy tu toa do gan nhat do package da dat.

## Lang nghe

```python
from device_controler.input_controller import KeyboardEvent, listen_keys


def on_key(event: KeyboardEvent) -> None:
    print(event.name, event.event_type, event.text)


listener = listen_keys(on_key, typeable_only=True)
# Khi app dung:
listener.stop()
```

Listener doc cung luc moi keyboard vat ly va tu quet lai khi thiet bi bi rut hoac
gan vao. No khong grab input va bo qua keyboard ao cua SAG. `typeable_only=True`
chi gui chu, so, khoang trang va dau cau; cac phim nhu Ctrl, Alt, Esc, Super bi
loc bo. Callback can xu ly nhanh; exception trong callback bi co lap de thread
lang nghe tiep tuc hoat dong.
