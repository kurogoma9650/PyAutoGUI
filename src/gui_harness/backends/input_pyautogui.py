from __future__ import annotations

import pyautogui

from ..models import ScreenPoint


class PyAutoGuiInputBackend:
    def __init__(self, *, pause: float = 0.05) -> None:
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = pause

    def click(self, point: ScreenPoint) -> None:
        pyautogui.click(point.x, point.y)

    def double_click(self, point: ScreenPoint, *, interval: float = 0.1) -> None:
        pyautogui.doubleClick(point.x, point.y, interval=interval)

    def drag(self, source: ScreenPoint, target: ScreenPoint, *, duration: float = 0.5) -> None:
        pyautogui.moveTo(source.x, source.y)
        pyautogui.dragTo(target.x, target.y, duration=duration, button="left")

    def scroll(self, clicks: int, point: ScreenPoint | None = None) -> None:
        if point is not None:
            pyautogui.moveTo(point.x, point.y)
        pyautogui.scroll(clicks)

    def type_text(self, text: str, *, interval: float = 0.01) -> None:
        pyautogui.write(text, interval=interval)

    def hotkey(self, *keys: str) -> None:
        pyautogui.hotkey(*keys)
