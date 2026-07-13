"""Đọc nội dung clipboard hiện tại.

File path: `src/system_monitor/clipboard_tracker/__init__.py`
Input: không nhận tham số; đọc clipboard của session người dùng qua `pyperclip`.
Output: chuỗi text mới nhất trong clipboard.

Nguyên lý hoạt động: module này là wrapper mỏng để phần giám sát hệ thống không
phụ thuộc trực tiếp vào tên thư viện clipboard. Nếu backend OS của `pyperclip`
không khả dụng, lỗi sẽ đi theo hành vi mặc định của thư viện đó.
"""

import pyperclip


def get_clipboard_text() -> str:
    """Trả về text clipboard mới nhất của người dùng hiện tại."""

    return pyperclip.paste()
