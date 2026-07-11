"""Test screenlocker an toàn, mặc định không khóa màn hình thật."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
SCREENLOCKER_PATH = SRC_ROOT / "device_controler" / "screenlocker" / "__init__.py"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def test_unlock_shortcut_calls_unlock() -> None:
    """Shortcut thoát lock UI phải gọi đúng API unlock hiện có."""

    source = SCREENLOCKER_PATH.read_text(encoding="utf-8")
    assert "lambda _: unlock()" in source
    assert "lambda _: unblock()" not in source


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manual", action="store_true")
    parser.add_argument("--seconds", type=float, default=20.0)
    return parser


def _run_manual(seconds: float) -> None:
    from device_controler.screenlocker import lock, unlock

    print("Screen lock in 1s")
    time.sleep(1)
    print(f"Unlock in {seconds}")
    time.sleep(0.2)
    try:
        lock()
        time.sleep(seconds)
    finally:
        unlock()
    print("Screen unlocked")


def main() -> None:
    args = _build_parser().parse_args()
    if args.manual:
        _run_manual(args.seconds)
        return
    test_unlock_shortcut_calls_unlock()


if __name__ == "__main__":
    main()
    print("PASS: screen_locker")
