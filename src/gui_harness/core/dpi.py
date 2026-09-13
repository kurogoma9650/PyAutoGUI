from __future__ import annotations

import ctypes
import sys


def enable_per_monitor_v2() -> str:
    if sys.platform != "win32":
        return "unsupported"

    user32 = ctypes.windll.user32
    try:
        # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 == (HANDLE)-4
        if user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
            return "Per Monitor V2"
    except (AttributeError, OSError):
        pass

    try:
        if user32.SetProcessDPIAware():
            return "System DPI aware"
    except (AttributeError, OSError):
        pass

    return "unchanged"
