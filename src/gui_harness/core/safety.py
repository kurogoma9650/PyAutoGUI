from __future__ import annotations

from ..errors import SafetyError
from ..models import ScreenPoint, WindowInfo
from ..backends.window_win32 import Win32WindowBackend


class SafetyGuard:
    def __init__(self, windows: Win32WindowBackend, target: WindowInfo) -> None:
        self.windows = windows
        self.target = target

    def refresh(self) -> WindowInfo:
        self.target = self.windows.info(self.target.hwnd)
        if not self.target.visible:
            raise SafetyError("Target window is not visible.")
        if self.target.minimized:
            raise SafetyError("Target window is minimized.")
        return self.target

    def require_same_session(self) -> None:
        current = self.windows.current_session_id()
        if current != self.target.session_id:
            raise SafetyError(
                f"Session mismatch: harness={current}, target={self.target.session_id}"
            )

    def require_foreground(self) -> None:
        current_pid = self.windows.foreground_pid()
        if current_pid != self.target.pid:
            raise SafetyError(
                f"Foreground PID mismatch: expected={self.target.pid}, actual={current_pid}"
            )

    def require_point_in_client(self, point: ScreenPoint) -> None:
        target = self.refresh()
        if not target.client_rect.contains(point.x, point.y):
            raise SafetyError(
                f"Input point ({point.x},{point.y}) is outside target client area "
                f"{target.client_rect}."
            )

    def before_pointer_input(self, point: ScreenPoint) -> None:
        self.require_same_session()
        self.require_foreground()
        self.require_point_in_client(point)

    def before_keyboard_input(self) -> None:
        self.require_same_session()
        self.refresh()
        self.require_foreground()
