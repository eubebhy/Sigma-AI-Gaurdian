"""Đọc thông tin cửa sổ đang mở trên desktop.

File path: `src/system_monitor/windows_tracker/__init__.py`
Input: không nhận tham số; đọc state cửa sổ hiện tại qua `pywinctl`.
Output: tiêu đề cửa sổ active hoặc danh sách tiêu đề cửa sổ đang mở.

Nguyên lý hoạt động: module này bọc `pywinctl` để code giám sát không gọi trực
tiếp thư viện ngoài. Một số window object có thể lỗi khi đọc title, nên danh sách
cửa sổ bỏ qua object lỗi và tiếp tục trả về phần còn lại.
"""

import pywinctl as pwc


def get_active_window_name() -> str:
    """Trả về tiêu đề cửa sổ đang active, hoặc chuỗi rỗng nếu không có."""

    win = pwc.getActiveWindow()
    if win:
        return win.title
    return ""


def get_all_opening_windows() -> list[str]:
    """Trả về danh sách tiêu đề các cửa sổ hiện đang mở."""

    windows = pwc.getAllWindows()
    window_titles = [""]
    for window in windows:
        try:
            window_titles.append(window.title)
        except:
            pass

    return window_titles
