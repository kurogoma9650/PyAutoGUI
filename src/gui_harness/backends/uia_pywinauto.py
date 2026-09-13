from __future__ import annotations

from pywinauto import Desktop
from pywinauto.findwindows import ElementNotFoundError

from ..errors import BlockedError
from ..models import ScreenPoint


class PywinautoSelectorBackend:
    def resolve(
        self,
        hwnd: int,
        *,
        name: str | None = None,
        control_type: str | None = None,
        automation_id: str | None = None,
    ) -> ScreenPoint:
        criteria: dict[str, str] = {}
        if name:
            criteria["title"] = name
        if control_type:
            criteria["control_type"] = control_type
        if automation_id:
            criteria["auto_id"] = automation_id
        try:
            root = Desktop(backend="uia").window(handle=hwnd)
            wrapper = root.child_window(**criteria).wrapper_object()
        except (ElementNotFoundError, RuntimeError) as exc:
            raise BlockedError(f"UIA element not found: {criteria}") from exc
        rect = wrapper.rectangle()
        return ScreenPoint((rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2)
