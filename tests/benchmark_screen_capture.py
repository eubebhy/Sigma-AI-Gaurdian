# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false
"""Benchmark FPS cho screen_capture.

File path: `tests/benchmark_screen_capture.py`
Input: CLI flags chọn số giây mỗi resolution và sharpness.
Output: FPS trung bình theo từng mốc resolution hợp lệ với màn hình hiện tại.
Nguyên lý: thêm `src/` vào `sys.path`, lấy kích thước màn hình bằng MSS, chỉ
benchmark các chuẩn resolution không vượt quá màn hình rồi tính FPS.
"""

from __future__ import annotations

import argparse
import pathlib
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from mss import mss

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from device_controler.screen_capture import capture


@dataclass(frozen=True)
class BenchmarkCase:
    width: int
    height: int


DEFAULT_RESOLUTIONS: tuple[BenchmarkCase, ...] = (
    BenchmarkCase(640, 360),
    BenchmarkCase(1280, 720),
    BenchmarkCase(1600, 900),
    BenchmarkCase(1920, 1080),
    BenchmarkCase(2560, 1440),
    BenchmarkCase(3440, 1440),
    BenchmarkCase(3840, 2160),
    BenchmarkCase(5120, 2880),
    BenchmarkCase(7680, 4320),
)


def _benchmark_case(case: BenchmarkCase, seconds: float, sharpness: float) -> float:
    started_at = time.perf_counter()
    frames = 0
    while time.perf_counter() - started_at < seconds:
        capture(
            top=0, left=0, width=case.width, height=case.height, sharpness=sharpness
        )
        frames += 1
    elapsed = time.perf_counter() - started_at
    return frames / elapsed if elapsed > 0.0 else 0.0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark screen capture FPS.")
    parser.add_argument("--seconds", type=float, default=3.0)
    parser.add_argument("--sharpness", type=float, default=1.0)
    return parser


def _screen_size() -> BenchmarkCase:
    with mss() as screen_capture:
        monitor = screen_capture.monitors[0]
    return BenchmarkCase(
        width=int(monitor["width"]),
        height=int(monitor["height"]),
    )


def _valid_cases(screen_size: BenchmarkCase) -> list[BenchmarkCase]:
    return [
        case
        for case in DEFAULT_RESOLUTIONS
        if case.width <= screen_size.width and case.height <= screen_size.height
    ]


def _run_benchmark(args: Any, cases: Sequence[BenchmarkCase]) -> None:
    for case in cases:
        fps = _benchmark_case(case, args.seconds, args.sharpness)
        print(f"{case.width}x{case.height} sharpness={args.sharpness}: {fps:.2f} FPS")


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    screen_size = _screen_size()
    cases = _valid_cases(screen_size)
    if not cases:
        print("No standard resolution is valid for the current screen. Skipping.")
        return 0
    _run_benchmark(args, cases)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
