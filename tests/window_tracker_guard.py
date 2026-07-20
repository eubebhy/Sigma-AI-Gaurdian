"""Quét cửa sổ đang mở và khóa màn hình khi phát hiện nội dung không an toàn.

File path: `tests/window_game_guard.py`
Input: chạy trực tiếp file này, tùy chọn `--interval` để đổi chu kỳ quét.
Output:
- Mỗi chu kỳ luôn in toàn bộ cửa sổ đang mở và kết quả phân loại.
- Nếu classifier trả về bất kỳ category nào khác `Unknown` thì khóa màn hình
  trong 10 giây.

Nguyên lý: thêm `src/` vào `sys.path`, lấy danh sách cửa sổ qua
`system_monitor.windows_tracker`, phân loại tiêu đề kết hợp với tên process,
sau đó lock/unlock qua screenlocker.
"""

from __future__ import annotations

import argparse
import signal
import sys
import time
from collections.abc import Sequence
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from content_classifier import content_classifier
from content_classifier.tags import ContentCategory
from device_controler.screenlocker import lock, unlock
from system_monitor.windows_tracker import get_all_opening_windows

LOCK_SECONDS = 10.0
_should_stop = False


def _scan_once() -> tuple[str, str, ContentCategory] | None:
    """In mọi cửa sổ và trả về cửa sổ đầu tiên không thuộc Unknown."""

    windows = get_all_opening_windows()
    matched_window: tuple[str, str, ContentCategory] | None = None

    print("\n=== Open windows ===")

    if not windows:
        print("No open windows.")

    for title, process_name in windows.items():
        content = f"{process_name} - {title}"
        category = content_classifier(content)

        print(f"process={process_name!r} title={title!r} category={category.name}")

        if matched_window is None and category != ContentCategory.Unknown:
            matched_window = title, process_name, category

    return matched_window


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Lock 10 seconds when non-Unknown content appears."
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Thời gian giữa mỗi lần quét, tính bằng giây.",
    )
    return parser


def _request_stop(signum: int, frame: object | None) -> None:
    """Dừng chương trình và mở khóa màn hình."""

    global _should_stop
    _should_stop = True
    unlock()


def _sleep_or_stop(seconds: float) -> None:
    """Chờ nhưng vẫn cho phép signal dừng chương trình sớm."""

    deadline = time.monotonic() + seconds

    while not _should_stop:
        remaining = deadline - time.monotonic()

        if remaining <= 0:
            return

        time.sleep(min(0.2, remaining))


def main(argv: Sequence[str] | None = None) -> int:
    signal.signal(signal.SIGINT, _request_stop)
    signal.signal(signal.SIGTERM, _request_stop)

    args = _build_parser().parse_args(argv)

    if args.interval <= 0:
        raise ValueError("--interval must be greater than 0")

    try:
        while not _should_stop:
            matched_window = _scan_once()

            if matched_window is not None:
                title, process_name, category = matched_window

                print(
                    f"Blocked: process={process_name!r}, "
                    f"title={title!r}, "
                    f"category={category.name}"
                )

                lock()
                _sleep_or_stop(LOCK_SECONDS)
                unlock()

            _sleep_or_stop(args.interval)
    finally:
        unlock()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
