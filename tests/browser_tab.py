# pyright: reportPrivateUsage=false
"""Test browser_tab bang monkeypatch, khong mo browser that."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from device_controler import browser_tab


def test_open_tab_rejects_invalid_url() -> None:
    """URL sai scheme phai fail som."""

    assert not browser_tab.open_tab("file:///tmp/a.html")


def test_open_tab_uses_running_browser() -> None:
    """Browser dang chay duoc uu tien truoc fallback."""

    old_pick_browser = browser_tab._pick_browser
    old_run_open_command = browser_tab._run_open_command
    commands: list[list[str]] = []

    def fake_pick_browser(require_running: bool) -> list[browser_tab.BrowserState]:
        if not require_running:
            return []
        return [
            {
                "spec": browser_tab.BROWSERS[0],
                "executable": "/bin/browser",
                "pid": 123,
                "score": 1000,
            }
        ]

    def fake_run_open_command(command: list[str]) -> bool:
        commands.append(command)
        return True

    try:
        # thay backend mo browser bang recorder
        browser_tab._pick_browser = fake_pick_browser
        browser_tab._run_open_command = fake_run_open_command
        assert browser_tab.open_tab("https://example.com")
    finally:
        browser_tab._pick_browser = old_pick_browser
        browser_tab._run_open_command = old_run_open_command

    assert commands == [["/bin/browser", "https://example.com"]]


def _build_parser() -> argparse.ArgumentParser:
    """CLI nho de chon test case khi can."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=("all", "invalid", "open"), default="all")
    return parser


def main() -> None:
    """Chay test theo flag."""

    args = _build_parser().parse_args()
    if args.case in ("all", "invalid"):
        test_open_tab_rejects_invalid_url()
    if args.case in ("all", "open"):
        test_open_tab_uses_running_browser()


if __name__ == "__main__":
    main()
    print("PASS: browser_tab")
