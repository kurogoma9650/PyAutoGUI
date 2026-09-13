from __future__ import annotations

import ctypes
import os
import re
import sys
from ctypes import wintypes

import psutil

from ..errors import BlockedError
from ..models import Rect, WindowInfo

SW_RESTORE = 9


class Win32WindowBackend:
    def __init__(self) -> None:
        if sys.platform != "win32":
            raise BlockedError("Win32 window backend requires Windows.")
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self.user32.GetForegroundWindow.restype = wintypes.HWND
        self.user32.OpenInputDesktop.restype = wintypes.HANDLE

    def current_session_id(self) -> int:
        value = wintypes.DWORD()
        if not self.kernel32.ProcessIdToSessionId(os.getpid(), ctypes.byref(value)):
            raise BlockedError("Could not resolve harness Windows session.")
        return int(value.value)

    def process_session_id(self, pid: int) -> int:
        value = wintypes.DWORD()
        if not self.kernel32.ProcessIdToSessionId(pid, ctypes.byref(value)):
            raise BlockedError(f"Could not resolve target session for PID {pid}.")
        return int(value.value)

    def _title(self, hwnd: int) -> str:
        length = self.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        self.user32.GetWindowTextW(hwnd, buf, len(buf))
        return buf.value

    def _pid(self, hwnd: int) -> int:
        pid = wintypes.DWORD()
        self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return int(pid.value)

    def _window_rect(self, hwnd: int) -> Rect:
        rect = wintypes.RECT()
        if not self.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            raise BlockedError(f"GetWindowRect failed for HWND {hwnd}.")
        return Rect(rect.left, rect.top, rect.right, rect.bottom)

    def _client_rect_screen(self, hwnd: int) -> Rect:
        rect = wintypes.RECT()
        if not self.user32.GetClientRect(hwnd, ctypes.byref(rect)):
            raise BlockedError(f"GetClientRect failed for HWND {hwnd}.")
        origin = wintypes.POINT(0, 0)
        if not self.user32.ClientToScreen(hwnd, ctypes.byref(origin)):
            raise BlockedError(f"ClientToScreen failed for HWND {hwnd}.")
        return Rect(
            origin.x,
            origin.y,
            origin.x + (rect.right - rect.left),
            origin.y + (rect.bottom - rect.top),
        )

    def info(self, hwnd: int) -> WindowInfo:
        if not self.user32.IsWindow(hwnd):
            raise BlockedError(f"Target HWND no longer exists: {hwnd}")
        pid = self._pid(hwnd)
        try:
            process_name = psutil.Process(pid).name()
        except psutil.Error as exc:
            raise BlockedError(f"Could not resolve target process for PID {pid}: {exc}") from exc
        return WindowInfo(
            hwnd=hwnd,
            pid=pid,
            process_name=process_name,
            title=self._title(hwnd),
            window_rect=self._window_rect(hwnd),
            client_rect=self._client_rect_screen(hwnd),
            visible=bool(self.user32.IsWindowVisible(hwnd)),
            minimized=bool(self.user32.IsIconic(hwnd)),
            session_id=self.process_session_id(pid),
        )

    def find(self, process_name: str, title_regex: str | None = None) -> WindowInfo:
        candidates: list[int] = []
        pattern = re.compile(title_regex) if title_regex else None

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def callback(hwnd: int, _lparam: int) -> bool:
            if not self.user32.IsWindowVisible(hwnd):
                return True
            pid = self._pid(hwnd)
            try:
                if psutil.Process(pid).name().lower() != process_name.lower():
                    return True
            except psutil.Error:
                return True
            title = self._title(hwnd)
            if pattern and not pattern.search(title):
                return True
            candidates.append(hwnd)
            return True

        self.user32.EnumWindows(callback, 0)
        if not candidates:
            raise BlockedError(
                f"No visible top-level window found for process {process_name!r}"
                + (f" matching {title_regex!r}" if title_regex else "")
            )
        return self.info(candidates[0])

    def foreground_hwnd(self) -> int:
        return int(self.user32.GetForegroundWindow())

    def foreground_pid(self) -> int:
        hwnd = self.foreground_hwnd()
        return self._pid(hwnd) if hwnd else 0

    def restore(self, hwnd: int) -> None:
        self.user32.ShowWindow(hwnd, SW_RESTORE)

    def focus(self, hwnd: int) -> None:
        self.restore(hwnd)
        self.user32.SetForegroundWindow(hwnd)

    def interactive_desktop_available(self) -> bool:
        DESKTOP_READOBJECTS = 0x0001
        DESKTOP_SWITCHDESKTOP = 0x0100
        handle = self.user32.OpenInputDesktop(
            0, False, DESKTOP_READOBJECTS | DESKTOP_SWITCHDESKTOP
        )
        if not handle:
            return False
        self.user32.CloseDesktop(handle)
        return True
