from __future__ import annotations

import platform
import sys
from pathlib import Path

from ..backends.capture_mss import MssCaptureBackend
from ..backends.window_win32 import Win32WindowBackend
from ..config import ApplicationConfig
from ..errors import BlockedError
from ..models import CheckResult, RunStatus, WindowInfo
from .dpi import enable_per_monitor_v2


def run_preflight(config: ApplicationConfig | None = None) -> tuple[list[CheckResult], WindowInfo | None]:
    checks: list[CheckResult] = []
    target: WindowInfo | None = None

    if sys.platform != "win32":
        return [CheckResult("Platform", RunStatus.BLOCKED, platform.platform())], None

    checks.append(CheckResult("Platform", RunStatus.PASS, platform.platform()))
    checks.append(CheckResult("Python", RunStatus.PASS, sys.version.split()[0]))
    checks.append(CheckResult("DPI Awareness", RunStatus.PASS, enable_per_monitor_v2()))

    windows = Win32WindowBackend()
    interactive = windows.interactive_desktop_available()
    checks.append(
        CheckResult(
            "Interactive Desktop",
            RunStatus.PASS if interactive else RunStatus.BLOCKED,
            "available" if interactive else "unavailable",
        )
    )
    if not interactive:
        return checks, None

    session = windows.current_session_id()
    checks.append(CheckResult("Harness Session", RunStatus.PASS, str(session)))

    if config is None:
        return checks, None

    try:
        target = windows.find(config.process_name, config.title_regex)
    except BlockedError as exc:
        checks.append(CheckResult("Target Window", RunStatus.BLOCKED, str(exc)))
        return checks, None

    checks.extend(
        [
            CheckResult("Target Process", RunStatus.PASS, f"{target.process_name} PID={target.pid}"),
            CheckResult(
                "Target Session",
                RunStatus.PASS if target.session_id == session else RunStatus.BLOCKED,
                str(target.session_id),
            ),
            CheckResult(
                "Visible",
                RunStatus.PASS if target.visible else RunStatus.BLOCKED,
                str(target.visible),
            ),
            CheckResult(
                "Minimized",
                RunStatus.PASS if not target.minimized else RunStatus.BLOCKED,
                str(target.minimized),
            ),
        ]
    )

    try:
        image = MssCaptureBackend().capture_rect(target.client_rect)
        detail = f"{image.width}x{image.height}"
        checks.append(CheckResult("Capture", RunStatus.PASS, detail))
    except Exception as exc:
        checks.append(CheckResult("Capture", RunStatus.BLOCKED, str(exc)))

    if config.executable:
        exists = Path(config.executable).exists()
        checks.append(
            CheckResult(
                "Configured Executable",
                RunStatus.PASS if exists else RunStatus.BLOCKED,
                config.executable,
            )
        )

    return checks, target
