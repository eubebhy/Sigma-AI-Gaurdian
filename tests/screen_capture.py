"""Test screen_capture bang MSS fake, khong chup man hinh that."""

from __future__ import annotations

import argparse
import importlib
import sys
import types
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


class FakeScreenShotError(Exception):
    pass


class FakeMSS:
    def __init__(self) -> None:
        self.closed = False

    def grab(self, monitor: dict[str, int]) -> np.ndarray[Any, np.dtype[np.uint8]]:
        height = monitor["height"]
        width = monitor["width"]
        return np.zeros((height, width, 4), dtype=np.uint8)

    def close(self) -> None:
        self.closed = True


def _install_fake_mss() -> None:
    """Nap MSS fake truoc khi import module capture."""

    fake_mss = types.ModuleType("mss")
    fake_exception = types.ModuleType("mss.exception")
    setattr(fake_mss, "MSS", FakeMSS)
    setattr(fake_exception, "ScreenShotError", FakeScreenShotError)
    sys.modules["mss"] = fake_mss
    sys.modules["mss.exception"] = fake_exception


def _capture_module() -> Any:
    """Import lai capture sau khi MSS da fake."""

    _install_fake_mss()
    return importlib.import_module("device_controler.screen_capture.capture")


def test_capture_returns_frame() -> None:
    """Capture dung size voi backend fake."""

    capture_module = _capture_module()
    frame = capture_module.capture(top=0, left=0, width=4, height=2)

    assert frame.shape == (2, 4, 4)


def test_capture_applies_sharpness() -> None:
    """Sharpness giam mau frame theo step."""

    capture_module = _capture_module()
    frame = capture_module.capture(top=0, left=0, width=4, height=4, sharpness=0.5)

    assert frame.shape == (2, 2, 4)


def _build_parser() -> argparse.ArgumentParser:
    """CLI nho de chon test case khi can."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=("all", "capture", "sharpness"), default="all")
    return parser


def main() -> None:
    """Chay test theo flag."""

    args = _build_parser().parse_args()
    if args.case in ("all", "capture"):
        test_capture_returns_frame()
    if args.case in ("all", "sharpness"):
        test_capture_applies_sharpness()


if __name__ == "__main__":
    main()
    print("PASS: screen_capture")
