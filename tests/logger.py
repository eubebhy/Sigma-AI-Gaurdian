"""Test he thong logger trung tam bang thu muc tam.

File path: `tests/logger.py`
Input: chay truc tiep file nay, khong can tham so.
Output: in `PASS: logger` neu logger tao dung file module va critical log hien ra
console.

Note cho nguoi tap code:
Test nay khong ghi vao `logs/` that cua project. No tao mot thu muc tam, setup
config tro vao thu muc do, goi `get_logger(fake_file.py)`, roi kiem tra file
`fake_file.py.log` duoc tao. Cach nay giu test doc lap va khong lam ban log khi
dev dang tail log that.
"""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from config import setup_config
from logger import get_logger, setup_log


def test_module_logger_writes_py_log_file() -> None:
    """Module log giu nguyen ten file goc va them duoi `.log`."""

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config = setup_config(
            overrides={
                "project_root": PROJECT_ROOT,
                "logs_dir": temp_path / "logs",
                "log_to_console": False,
            }
        )
        setup_log(config)

        module_file = PROJECT_ROOT / "src" / "demo" / "fake_module.py"
        log = get_logger(module_file)
        log.debug("module log works")

        log_path = config.logs_dir / "src" / "demo" / "fake_module.py.log"
        assert log_path.exists()
        assert "module log works" in log_path.read_text(encoding="utf-8")


def test_critical_log_prints_to_console() -> None:
    """Critical log van hien ra console khi log_to_console bi tat."""

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config = setup_config(
            overrides={
                "project_root": PROJECT_ROOT,
                "logs_dir": temp_path / "logs",
                "log_to_console": False,
                "critical_log_to_console": True,
            }
        )
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            setup_log(config)
            log = get_logger(PROJECT_ROOT / "src" / "demo" / "critical.py")
            log.critical("critical visible")

        assert "critical visible" in stderr.getvalue()


def main() -> None:
    test_module_logger_writes_py_log_file()
    test_critical_log_prints_to_console()


if __name__ == "__main__":
    main()
    print("PASS: logger")
