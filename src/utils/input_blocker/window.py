import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.BlockInput.argtypes = [wintypes.BOOL]
user32.BlockInput.restype = wintypes.BOOL


# Require admin
def _set_block_state(is_blocked: bool) -> None:
    if not user32.BlockInput(is_blocked):
        raise ctypes.WinError(ctypes.get_last_error())


def block() -> None:
    _set_block_state(True)


def unblock() -> None:
    _set_block_state(False)
