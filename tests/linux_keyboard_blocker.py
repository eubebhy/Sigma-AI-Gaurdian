import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from device_controler.screenlocker.input_blocker import linux
import time

"""
File path: tests/test_linux_keyboard_blocker_manual.py
Input contract:
- chay truc tiep file nay tren Linux co quyen doc /dev/input/event*
- file tu them src/ vao sys.path truoc khi import source
Output contract:
- khoa toan bo GUI input tam thoi roi tu mo lai sau linux.BLOCK_SECONDS giay
Operating principle:
- goi API linux.block() va join thread de giu tien trinh test song
"""

print("Blocking keyboard")
linux.block()
for i in range(20, -1, -1):
    print(i)
    time.sleep(1)
print("Unblocked!")
linux.unblock()
