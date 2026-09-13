from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from ..backends.capture_mss import MssCaptureBackend
from ..backends.input_pyautogui import PyAutoGuiInputBackend
from ..backends.uia_pywinauto import PywinautoSelectorBackend
from ..backends.window_win32 import Win32WindowBackend
from ..errors import BlockedError
from ..evidence.recorder import EvidenceRecorder
from ..models import ClientPoint, RelativePoint, ScreenPoint, WindowInfo
from ..selectors.base import ImageSelector, UIASelector
from ..selectors.chain import SelectorChain
from ..selectors.image import resolve_image
from .safety import SafetyGuard
from .wait import Waiter


class RunContext:
    def __init__(
        self,
        *,
        window_backend: Win32WindowBackend,
        target: WindowInfo,
        recorder: EvidenceRecorder,
    ) -> None:
        self.windows = window_backend
        self.target = target
        self.recorder = recorder
        self.capture_backend = MssCaptureBackend()
        self.input = PyAutoGuiInputBackend()
        self.uia = PywinautoSelectorBackend()
        self.safety = SafetyGuard(self.windows, self.target)
        self.wait = Waiter(self.capture_image)

    def refresh(self) -> WindowInfo:
        self.target = self.windows.info(self.target.hwnd)
        self.safety.target = self.target
        return self.target

    def focus_window(self, *, timeout: float = 1.5) -> None:
        with self.recorder.timed("focus_window"):
            self.windows.focus(self.target.hwnd)
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                if self.windows.foreground_pid() == self.target.pid:
                    self.refresh()
                    return
                time.sleep(0.05)
            raise BlockedError("Could not make target application foreground.")

    def capture_image(self):
        target = self.refresh()
        return self.capture_backend.capture_rect(target.client_rect)

    def capture(self, name: str) -> Path:
        return self.recorder.screenshot(name, self.capture_image())

    def resolve(self, selector: Any) -> ScreenPoint:
        target = self.refresh()
        if isinstance(selector, ScreenPoint):
            return selector
        if isinstance(selector, ClientPoint):
            return ScreenPoint(
                target.client_rect.left + selector.x,
                target.client_rect.top + selector.y,
            )
        if isinstance(selector, RelativePoint):
            return ScreenPoint(
                target.client_rect.left + int(target.client_rect.width * selector.x),
                target.client_rect.top + int(target.client_rect.height * selector.y),
            )
        if isinstance(selector, UIASelector):
            return self.uia.resolve(
                target.hwnd,
                name=selector.name,
                control_type=selector.control_type,
                automation_id=selector.automation_id,
            )
        if isinstance(selector, ImageSelector):
            return resolve_image(
                self.capture_image(),
                target.client_rect,
                selector.template,
                selector.confidence,
            )
        if isinstance(selector, SelectorChain):
            errors: list[str] = []
            for item in selector.selectors:
                try:
                    return self.resolve(item)
                except BlockedError as exc:
                    errors.append(str(exc))
            raise BlockedError("SelectorChain exhausted: " + " | ".join(errors))
        raise TypeError(f"Unsupported selector type: {type(selector)!r}")

    def click(self, selector: Any) -> None:
        point = self.resolve(selector)
        with self.recorder.timed("click"):
            self.safety.before_pointer_input(point)
            self.input.click(point)

    def double_click(self, selector: Any) -> None:
        point = self.resolve(selector)
        with self.recorder.timed("double_click"):
            self.safety.before_pointer_input(point)
            self.input.double_click(point)

    def drag(self, source: Any, target: Any, *, duration: float = 0.5) -> None:
        source_point = self.resolve(source)
        target_point = self.resolve(target)
        with self.recorder.timed("drag"):
            self.safety.before_pointer_input(source_point)
            self.safety.require_point_in_client(target_point)
            self.input.drag(source_point, target_point, duration=duration)

    def scroll(self, clicks: int, selector: Any | None = None) -> None:
        point = (
            self.resolve(selector)
            if selector is not None
            else ScreenPoint(*self.refresh().client_rect.center)
        )
        with self.recorder.timed("scroll"):
            self.safety.before_pointer_input(point)
            self.input.scroll(clicks, point)

    def type_text(self, text: str) -> None:
        with self.recorder.timed("type_text"):
            self.safety.before_keyboard_input()
            self.input.type_text(text)

    def hotkey(self, *keys: str) -> None:
        with self.recorder.timed("hotkey"):
            self.safety.before_keyboard_input()
            self.input.hotkey(*keys)
