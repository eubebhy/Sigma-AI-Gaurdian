from __future__ import annotations

import csv
import os
import subprocess
import threading
import time


"""
File path: process_killer.py
Input contract:
- ProcessKiller.blocked: danh sach ten process can kill theo exact name
- set_blacklist(values): bo sung exact process names can kill
- set_whitelist(values): danh sach exact process names khong duoc kill
- start(): bat dau vong quet nen
- stop(): dung vong quet nen
Output contract:
- khong tra ve gia tri tu cac ham dieu khien
- process trung blacklist va khong nam trong whitelist se bi kill
Operating principle:
- detect danh sach process theo OS hien tai
- chuan hoa process name ve lowercase de so sanh on dinh
- chay background thread, quet theo interval, gap process trung rule thi kill
"""


def _linux_processes() -> list[tuple[int, str]]:
    try:
        output = subprocess.check_output(["ps", "-eo", "pid=,comm="], text=True)
    except (OSError, subprocess.SubprocessError):
        return []
    items: list[tuple[int, str]] = []
    for line in output.splitlines():
        pid_str, name = line.strip().split(maxsplit=1)
        items.append((int(pid_str), name.lower()))
    return items


def _windows_processes() -> list[tuple[int, str]]:
    try:
        output = subprocess.check_output(
            ["tasklist", "/fo", "csv", "/nh"],
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
    except (OSError, subprocess.SubprocessError):
        return []
    items: list[tuple[int, str]] = []
    for row in csv.reader(output.splitlines()):
        if len(row) < 2:
            continue
        name = row[0].strip().lower()
        pid = int(row[1])
        items.append((pid, name))
    return items


def _kill_pid(pid: int) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=False)
        return
    os.kill(pid, 9)


class ProcessKiller:
    # Contract:
    # - blocked: exact process names to kill.
    # - whitelist: optional exact process names that must never be killed.
    # - interval: seconds between background scan loops.
    # - start(): spawn one daemon thread and keep scanning until stop().
    def __init__(self) -> None:
        self.blocked: list[str] = []
        self.whitelist: set[str] | None = None
        self.running: bool = False
        self.interval: float = 0.67
        self._thread: threading.Thread | None = None
        self._extra_exact: set[str] = set()

    def set_whitelist(self, values: list[str] | None) -> None:
        self.whitelist = {value.strip().lower() for value in values} if values else None

    def set_blacklist(self, values: list[str]) -> None:
        cleaned = {value.strip().lower() for value in values}
        self._extra_exact = cleaned

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.running = False

    def _run(self) -> None:
        while self.running:
            self._scan_and_kill()
            time.sleep(self.interval)

    def _scan_and_kill(self) -> None:
        list_processes = _windows_processes() if os.name == "nt" else _linux_processes()
        for pid, name in list_processes:
            if self._should_kill(name):
                _kill_pid(pid)

    def _should_kill(self, name: str) -> bool:
        if self.whitelist and name in self.whitelist:
            return False
        if name in set(self.blocked) | self._extra_exact:
            return True
        return False


__all__ = ["ProcessKiller"]
