import pyperclip


def get_clipboard_text() -> str:
    return pyperclip.paste()
