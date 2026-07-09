"""Quet ten cua so dang mo va khoa man hinh khi phat hien game.

File path: `tests/window_game_guard.py`
Input: chay truc tiep file nay, tuy chon `--interval` de doi chu ky quet.
Output: neu content classifier tra ve `Game` thi goi screenlocker lock 10 giay.
Nguyen ly: them `src/` vao `sys.path`, lay title cua so bang cong cu he dieu
hanh co san, phan loai tung title, roi lock/unlock qua screenlocker.
"""

from __future__ import annotations

import argparse
import platform
import signal
import subprocess
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

LOCK_SECONDS = 10.0
_should_stop = False


def _read_command(command: Sequence[str]) -> list[str]:
    try:
        output = subprocess.check_output(command, stderr=subprocess.DEVNULL, text=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []

    lines: list[str] = []
    for line in output.splitlines():
        clean_line = line.strip()
        if clean_line:
            lines.append(clean_line)
    return lines


def _get_linux_titles() -> list[str]:
    titles: list[str] = []
    for line in _read_command(["wmctrl", "-l"]):
        parts = line.split(maxsplit=3)
        if len(parts) == 4:
            titles.append(parts[3])
    if titles:
        return titles

    window_ids = _read_command(["xdotool", "search", "--name", "."])
    for window_id in window_ids:
        titles.extend(_read_command(["xdotool", "getwindowname", window_id]))
    return titles


def _get_windows_titles() -> list[str]:
    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        "Get-Process | Where-Object {$_.MainWindowTitle} | "
        "ForEach-Object {$_.MainWindowTitle}",
    ]
    return _read_command(command)


def _get_window_titles() -> list[str]:
    current_os = platform.system().lower()
    if current_os == "linux":
        return _get_linux_titles()
    if current_os == "windows":
        return _get_windows_titles()
    return []


def _scan_once() -> str | None:
    for title in _get_window_titles():
        category = content_classifier(title)
        if category == ContentCategory.Game:
            return title
    return None


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lock 10s when a game window appears.")
    parser.add_argument("--interval", type=float, default=1.0)
    return parser


def _request_stop(signum: int, frame: object | None) -> None:
    global _should_stop
    _should_stop = True
    unlock()


def _sleep_or_stop(seconds: float) -> None:
    deadline = time.monotonic() + seconds
    while not _should_stop and time.monotonic() < deadline:
        time.sleep(min(0.2, deadline - time.monotonic()))


def main(argv: Sequence[str] | None = None) -> int:
    signal.signal(signal.SIGINT, _request_stop)
    signal.signal(signal.SIGTERM, _request_stop)
    args = _build_parser().parse_args(argv)
    try:
        while not _should_stop:
            matched_title = _scan_once()
            if matched_title is not None:
                print(f"Game detected: {matched_title}")
                lock()
                _sleep_or_stop(LOCK_SECONDS)
                unlock()
            _sleep_or_stop(args.interval)
    finally:
        unlock()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
