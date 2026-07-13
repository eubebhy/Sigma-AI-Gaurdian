"""Mo tab browser theo browser dang co tren may.

File path: `src/device_controler/browser_tab/__init__.py`
Input contract:
- open_tab(url): nhan url bat dau bang http:// hoac https://.
Output contract:
- Tra ve True neu goi duoc browser hop le.
- Tra ve False neu url sai, khong co browser hop le hoac mo browser that bai.
Operating principle:
- Lay process browser dang chay va executable co trong PATH.
- Uu tien browser dang chay, roi fallback sang browser co executable.
- Cuoi cung dung default browser cua OS.
"""

from __future__ import annotations

import csv
import os
import shutil
import subprocess
import webbrowser
from typing import TypedDict


class BrowserSpec(TypedDict):
    name: str
    executables: tuple[str, ...]
    processes: tuple[str, ...]


class BrowserState(TypedDict):
    spec: BrowserSpec
    executable: str | None
    pid: int | None
    score: int


BROWSERS: tuple[BrowserSpec, ...] = (
    {
        "name": "chrome",
        "executables": ("google-chrome", "chrome", "chrome.exe"),
        "processes": ("chrome", "chrome.exe", "google-chrome"),
    },
    {
        "name": "edge",
        "executables": ("msedge", "msedge.exe"),
        "processes": ("msedge", "msedge.exe"),
    },
    {
        "name": "firefox",
        "executables": ("firefox", "firefox.exe"),
        "processes": ("firefox", "firefox.exe"),
    },
    {
        "name": "brave",
        "executables": ("brave-browser", "brave", "brave.exe"),
        "processes": ("brave", "brave.exe", "brave-browser"),
    },
    {
        "name": "opera",
        "executables": ("opera", "opera.exe"),
        "processes": ("opera", "opera.exe"),
    },
    {
        "name": "chromium",
        "executables": ("chromium", "chromium-browser", "chromium.exe"),
        "processes": ("chromium", "chromium-browser", "chromium.exe"),
    },
    {
        "name": "vivaldi",
        "executables": ("vivaldi", "vivaldi.exe"),
        "processes": ("vivaldi", "vivaldi.exe"),
    },
    {
        "name": "coccoc",
        "executables": ("coccoc", "coccoc.exe"),
        "processes": ("coccoc", "coccoc.exe"),
    },
    {
        "name": "tor",
        "executables": ("tor-browser", "tor.exe"),
        "processes": ("tor", "tor-browser", "tor.exe"),
    },
    {
        "name": "yandex",
        "executables": ("yandex-browser", "yandex.exe"),
        "processes": ("yandex-browser", "yandex.exe"),
    },
    {
        "name": "waterfox",
        "executables": ("waterfox", "waterfox.exe"),
        "processes": ("waterfox", "waterfox.exe"),
    },
)


def _linux_processes() -> dict[str, int]:
    try:
        output = subprocess.check_output(["ps", "-eo", "pid=,comm="], text=True)
    except (OSError, subprocess.SubprocessError):
        return {}
    processes: dict[str, int] = {}
    for line in output.splitlines():
        pid_text, name = line.strip().split(maxsplit=1)
        processes[name.lower()] = int(pid_text)
    return processes


def _windows_processes() -> dict[str, int]:
    try:
        output = subprocess.check_output(
            ["tasklist", "/fo", "csv", "/nh"],
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
    except (OSError, subprocess.SubprocessError):
        return {}
    processes: dict[str, int] = {}
    for row in csv.reader(output.splitlines()):
        if len(row) < 2:
            continue
        processes[row[0].strip().lower()] = int(row[1])
    return processes


def _find_pid(spec: BrowserSpec, processes: dict[str, int]) -> int | None:
    for process_name in spec["processes"]:
        if process_name.lower() in processes:
            return processes[process_name.lower()]
    return None


def _find_executable(spec: BrowserSpec) -> str | None:
    for executable in spec["executables"]:
        resolved = shutil.which(executable)
        if resolved:
            return resolved
    return None


def _score_browser(pid: int | None, index: int) -> int:
    score = 10 - index
    if pid is not None:
        score += 1000
    return score


def _browser_states() -> list[BrowserState]:
    processes = _windows_processes() if os.name == "nt" else _linux_processes()
    states: list[BrowserState] = []
    for index, spec in enumerate(BROWSERS):
        pid = _find_pid(spec, processes)
        executable = _find_executable(spec)
        score = _score_browser(pid, index)
        states.append(
            {"spec": spec, "executable": executable, "pid": pid, "score": score}
        )
    return states


def _pick_browser(require_running: bool) -> list[BrowserState]:
    states = _browser_states()
    if require_running:
        states = [state for state in states if state["pid"] is not None]
    states = [state for state in states if state["executable"] is not None]
    states.sort(key=lambda state: state["score"], reverse=True)
    return states


def _run_open_command(command: list[str]) -> bool:
    try:
        # tach process browser, open_tab khong day loi ra ngoai
        if os.name == "nt":
            subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            return True
        with open(os.devnull, "wb") as devnull:
            subprocess.Popen(
                command,
                stdout=devnull,
                stderr=devnull,
                start_new_session=True,
            )
        return True
    except OSError:
        return False


def open_tab(url: str) -> bool:
    """Mở URL bằng browser phù hợp nhất trên máy hiện tại.

    URL phải bắt đầu bằng `http://` hoặc `https://`. Hàm ưu tiên browser đang chạy
    để tab mới xuất hiện đúng phiên người dùng, sau đó mới fallback sang browser
    có executable trong PATH và cuối cùng là default browser của OS.
    """

    if not url.startswith(("http://", "https://")):
        return False
    for browser in _pick_browser(require_running=True):
        if browser["executable"] and _run_open_command([browser["executable"], url]):
            return True
    for browser in _pick_browser(require_running=False):
        if browser["executable"] and _run_open_command([browser["executable"], url]):
            return True
    return webbrowser.open(url, new=2)


__all__ = ["open_tab"]
