# pyright: reportMissingImports=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
"""
File path: src/device_controler/screenlocker/__init__.py
Input contract:
- block(): khong nhan tham so.
- unlock(): khong nhan tham so.
Output contract:
- block() chan input va hien thi lock UI fullscreen bang daemon thread.
- unlock() mo input va tat lock UI neu dang chay.
Operating principle:
- chup man hinh, ghep lock banner, tao Tkinter fullscreen trong thread rieng.
"""

from pathlib import Path
from typing import Any
import threading
import tkinter as tk

from PIL import Image, ImageGrab, ImageTk

from utils import input_blocker

IMAGE_PATH = Path(__file__).resolve().parents[3] / "assets" / "lock_banner.png"


_root: tk.Tk | None = None
_thread: threading.Thread | None = None
_lock = threading.Lock()


class App:
    def __init__(self, root: tk.Tk, lock_image: Any) -> None:
        self.root = root
        self.root.configure(bg="black")
        # self.root.bind("<Control-Shift-Q>", lambda _: unlock())
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)

        self.tk_img = ImageTk.PhotoImage(lock_image)
        self.label = tk.Label(root, bg="black", image=self.tk_img)
        self.label.pack(expand=True, fill="both")
        self.force_fullscreen()
        self.root.bind("<Configure>", self.force_fullscreen)

    def force_fullscreen(self, event: Any | None = None) -> None:
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.geometry(f"{w}x{h}+0+0")


def _create_lock_image() -> Any:
    screenshot = ImageGrab.grab().convert("RGB")
    banner = Image.open(IMAGE_PATH).convert("RGBA")
    scale = min(screenshot.width / banner.width, screenshot.height / banner.height)
    size = (int(banner.width * scale), int(banner.height * scale))
    banner = banner.resize(size, Image.Resampling.LANCZOS)

    # Ghép banner vào giữa ảnh chụp màn hình để tạo hiệu ứng lock.
    lock_image = screenshot.convert("RGBA")
    position = (
        (screenshot.width - banner.width) // 2,
        (screenshot.height - banner.height) // 2,
    )
    lock_image.alpha_composite(banner, position)
    return lock_image.convert("RGB")


def _run_ui(lock_image: Any) -> None:
    global _root
    root = tk.Tk()
    with _lock:
        _root = root
    App(root, lock_image)
    root.mainloop()


def lock() -> None:
    global _thread
    with _lock:
        if _thread is not None and _thread.is_alive():
            return
        lock_image = _create_lock_image()
        _thread = threading.Thread(target=_run_ui, args=(lock_image,), daemon=True)
        _thread.start()
    input_blocker.block()


def unlock() -> None:
    global _root
    input_blocker.unblock()
    with _lock:
        root = _root
        _root = None
    if root is not None:
        root.after(0, root.destroy)


__all__ = ["lock", "unlock"]
