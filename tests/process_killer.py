# pyright: reportPrivateUsage=false
"""Test process_killer bang state noi bo, khong kill process that."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from device_controler.process_killer import ProcessKiller


def test_blacklist_matches_exact_name() -> None:
    """Blacklist exact name moi duoc kill."""

    killer = ProcessKiller()
    killer.set_blacklist(["Game.exe"])

    assert killer._should_kill("game.exe")
    assert not killer._should_kill("game-helper.exe")


def test_whitelist_wins_over_blacklist() -> None:
    """Whitelist chan kill ke ca trung blacklist."""

    killer = ProcessKiller()
    killer.blocked = ["game.exe"]
    killer.set_whitelist(["Game.exe"])

    assert not killer._should_kill("game.exe")


def _build_parser() -> argparse.ArgumentParser:
    """CLI nho de chon test case khi can."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=("all", "blacklist", "whitelist"), default="all")
    return parser


def main() -> None:
    """Chay test theo flag."""

    args = _build_parser().parse_args()
    if args.case in ("all", "blacklist"):
        test_blacklist_matches_exact_name()
    if args.case in ("all", "whitelist"):
        test_whitelist_wins_over_blacklist()


if __name__ == "__main__":
    main()
    print("PASS: process_killer")
