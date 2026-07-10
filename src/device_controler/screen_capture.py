"""Wrapper chụp màn hình bằng MSS.

File path: `src/device_controler/screen_capture/capture.py`
Input: `top`, `left`, `width`, `height` giống monitor dict của MSS và
`sharpness` trong khoảng `(0.0, 1.0]`.
Output: `numpy.ndarray` BGRA, `dtype=uint8`, giống buffer MSS; khi `sharpness`
thấp hơn 1.0 thì output nhỏ hơn theo tỉ lệ để nhẹ dữ liệu và tăng FPS.
Nguyên lý: giữ một MSS instance dùng lại trong process để tránh tạo backend liên
tục; mỗi lần chụp lấy raw BGRA từ MSS rồi giảm mẫu bằng numpy slicing.
"""

from __future__ import annotations

import atexit
import threading
from dataclasses import dataclass
from typing import Any, TypeAlias

import numpy as np
from mss import MSS
from mss.exception import ScreenShotError

Frame: TypeAlias = Any


@dataclass(frozen=True)
class ScreenRegion:
    top: int
    left: int
    width: int
    height: int
    sharpness: float = 1.0


class ScreenCapture:
    def __init__(self) -> None:
        self._mss = MSS()
        self._lock = threading.Lock()

    def capture(
        self,
        top: int,
        left: int,
        width: int,
        height: int,
        sharpness: float = 1.0,
    ) -> Frame:

        region = ScreenRegion(top=top, left=left, width=width, height=height)

        # Hay de mss tu check
        if not 0.0 < sharpness <= 1.0:
            raise ValueError("sharpness must be in range (0.0, 1.0]")

        monitor = {
            "top": region.top,
            "left": region.left,
            "width": region.width,
            "height": region.height,
        }
        with self._lock:
            shot = self._mss.grab(monitor)
        frame = np.asarray(shot, dtype=np.uint8)
        return _apply_sharpness(frame, sharpness)

    def close(self) -> None:
        close = getattr(self._mss, "close", None)
        if callable(close):
            close()


def capture(
    top: int,
    left: int,
    width: int,
    height: int,
    sharpness: float = 1.0,
) -> Frame:
    global _capture_instance

    try:
        return _capture_instance.capture(
            top=top,
            left=left,
            width=width,
            height=height,
            sharpness=sharpness,
        )
    except ScreenShotError:
        _capture_instance = _create_capture_backend()
        return _capture_instance.capture(
            top=top,
            left=left,
            width=width,
            height=height,
            sharpness=sharpness,
        )


def _apply_sharpness(frame: Frame, sharpness: float) -> Frame:
    if sharpness == 1.0:
        return frame
    step = max(1, round(1.0 / sharpness))
    return np.ascontiguousarray(frame[::step, ::step, :])


def _create_capture_backend() -> ScreenCapture:
    """Ham nay se return backend dang ScreenCapture"""
    _capture_instance = ScreenCapture()
    atexit.register(_capture_instance.close)
    return _capture_instance


_capture_instance: ScreenCapture = _create_capture_backend()

__all__ = ["ScreenCapture", "ScreenRegion", "capture"]
