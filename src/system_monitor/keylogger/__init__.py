"""Theo dõi phím đã gõ để gom thành chuỗi text tạm thời.

File path: `src/system_monitor/keylogger/__init__.py`
Input: tên phím và event type từ `utils.input_controller.listen_keys()`.
Output: cập nhật state module `typing_string` và `typed_strings` trong bộ nhớ.

Nguyên lý hoạt động: chỉ xử lý event `down` và `press`, nối tên phím vào chuỗi
đang gõ, rồi đẩy chuỗi cũ vào `typed_strings` khi khoảng cách thời gian vượt quá
ngưỡng. Đây là state tạm trong process, chưa phải storage bền vững.
"""

from utils import input_controller as dinput  # Direct input


# Config
# TODO: After finish config system, add this:
max_typed_word_length = 50
max_pressed_keys_length = 50
max_typing_time_gap = 3  # Seconds
last_press_time: float = 0


typing_string: str = ""  # Used to temp processing pressing character
typed_strings: list[str] = []  # Used to storage typed words

# User pressing key
# Add key to pressed_keys
# if user press space bar or do something that mean type new words
# Remove all key pressed_keys and add new words to typed_words


def keylogger(name: str, event_type: str):
    """Nhận một keyboard event đã normalize và cập nhật buffer đang gõ."""

    global max_typing_time_gap
    global last_press_time
    global typed_strings
    global typed_strings

    if not event_type in ["down", "press"]:
        return

    last_press_time = time.time()

    if last_press_time > max_typing_time_gap:
        typed_strings.append(typing_string)
        typing_string = ""
        return

    typing_string += name
