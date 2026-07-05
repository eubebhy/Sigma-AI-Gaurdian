import argparse
import time
import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
SCR_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SCR_DIR))

from device_control.screenlockerV2.screenlocker import (
    lock_student_screen,
    unlock_student_screen,
)


def main():
    parser = argparse.ArgumentParser(
        description="Lock the student screen for a specified duration."
    )
    parser.add_argument(
        "delay",
        type=float,
        help="Duration to keep the screen locked (in seconds).",
    )

    args = parser.parse_args()

    print("Locking...")
    lock_student_screen()

    try:
        time.sleep(args.delay)
    finally:
        print("Unlocking...")
        unlock_student_screen()


if __name__ == "__main__":
    main()
