import pywinctl as pwc


def get_active_window_name() -> str:
    win = pwc.getActiveWindow()
    if win:
        return win.title
    return ""


def get_all_opening_windows() -> list[str]:
    windows = pwc.getAllWindows()
    window_titles = [""]
    for window in windows:
        try:
            window_titles.append(window.title)
        except:
            pass

    return window_titles
