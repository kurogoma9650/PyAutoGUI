from __future__ import annotations

import subprocess
import time

from ..backends.window_win32 import Win32WindowBackend
from ..config import ApplicationConfig
from ..errors import ConfigurationError, BlockedError
from ..models import WindowInfo


def launch_application(
    config: ApplicationConfig,
    *,
    timeout: float = 10.0,
) -> WindowInfo:
    if not config.executable:
        raise ConfigurationError(
            f"No executable configured for {config.app_id}. "
            "Set it in .gui-harness.local.toml or the environment."
        )

    subprocess.Popen(
        [config.executable],
        cwd=config.working_directory or None,
    )

    windows = Win32WindowBackend()
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            return windows.find(config.process_name, config.title_regex)
        except BlockedError as exc:
            last_error = exc
            time.sleep(0.2)
    raise BlockedError(f"Application did not expose its target window before timeout: {last_error}")
