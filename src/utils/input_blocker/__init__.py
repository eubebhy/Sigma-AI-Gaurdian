"""Facade chặn/mở chặn input theo hệ điều hành hiện tại.

File path: `src/utils/input_blocker/__init__.py`
Input: `block()` và `unblock()` không nhận tham số.
Output: gọi backend OS để chặn hoặc mở chặn bàn phím/chuột hiện tại.

Nguyên lý hoạt động: chọn backend một lần khi import package. Linux dùng evdev để
grab thiết bị input, Windows dùng `BlockInput` từ user32. Caller chỉ nên import
`utils.input_blocker`, không import trực tiếp backend OS nếu không cần test riêng.
"""

import platform

_current_os = platform.system().lower()
if _current_os == "linux":
    from utils.input_blocker.linux import block, unblock
elif _current_os == "windows":
    from utils.input_blocker.window import block, unblock
else:
    raise NotImplementedError(f"Unsupported OS: {_current_os}")

__all__ = ["block", "unblock"]
