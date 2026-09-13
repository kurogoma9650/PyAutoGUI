from __future__ import annotations

from pathlib import Path

from ..backends.window_win32 import Win32WindowBackend
from ..config import load_application_config
from ..errors import HarnessError
from ..evidence.recorder import EvidenceRecorder
from ..models import RunStatus
from ..scenarios.registry import create_scenario
from .context import RunContext
from .dpi import enable_per_monitor_v2


def run_scenario(name: str, *, artifacts_root: Path = Path("artifacts")) -> tuple[RunStatus, Path]:
    scenario = create_scenario(name)
    config = load_application_config(scenario.application)
    enable_per_monitor_v2()

    windows = Win32WindowBackend()
    target = windows.find(config.process_name, config.title_regex)
    recorder = EvidenceRecorder(
        application=scenario.application,
        scenario=name,
        window=target,
        root=artifacts_root,
    )
    ctx = RunContext(window_backend=windows, target=target, recorder=recorder)

    status = RunStatus.ERROR
    message = ""
    setup_complete = False
    try:
        ctx.safety.require_same_session()
        scenario.setup(ctx)
        setup_complete = True
        scenario.run(ctx)
        status = RunStatus.PASS
        message = "Automation scenario completed."
    except HarnessError as exc:
        status = RunStatus(exc.status)
        message = str(exc)
    except KeyboardInterrupt:
        status = RunStatus.ABORTED
        message = "Interrupted by operator."
    except Exception as exc:
        status = RunStatus.ERROR
        message = f"{type(exc).__name__}: {exc}"
    finally:
        if setup_complete:
            try:
                scenario.cleanup(ctx)
            except Exception as cleanup_exc:
                if status == RunStatus.PASS:
                    status = RunStatus.ERROR
                    message = f"Cleanup failed: {cleanup_exc}"
        recorder.finish(status, message)

    return status, recorder.run_dir
