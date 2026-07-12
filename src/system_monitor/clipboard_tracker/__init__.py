import pyperclip


def get_clipboard_text() -> str:
    """Return newest cli board text"""
    return pyperclip.paste()
