import platform

_current_os = platform.system().lower()
if _current_os == "linux":
    from device_controler.screenlocker.input_blocker.linux import block, unblock
elif _current_os == "windows":
    from device_controler.screenlocker.input_blocker.window import block, unblock
else:
    raise NotImplementedError(f"Unsupported OS: {_current_os}")

__all__ = ["block", "unblock"]
