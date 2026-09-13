from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .backends.capture_mss import MssCaptureBackend
from .backends.window_win32 import Win32WindowBackend
from .config import load_application_config
from .core.dpi import enable_per_monitor_v2
from .core.launcher import launch_application
from .core.preflight import run_preflight
from .core.runtime import run_scenario
from .errors import ConfigurationError, HarnessError
from .models import RunStatus
from .scenarios.registry import list_scenarios

EXIT_CODES = {
    RunStatus.PASS: 0,
    RunStatus.BLOCKED: 3,
    RunStatus.FAIL: 4,
    RunStatus.ERROR: 5,
    RunStatus.ABORTED: 130,
}


def _overall_status(checks) -> RunStatus:
    statuses = {check.status for check in checks}
    if RunStatus.ERROR in statuses:
        return RunStatus.ERROR
    if RunStatus.BLOCKED in statuses:
        return RunStatus.BLOCKED
    if RunStatus.FAIL in statuses:
        return RunStatus.FAIL
    return RunStatus.PASS


def _print_checks(checks, as_json: bool) -> None:
    overall = _overall_status(checks)
    if as_json:
        print(
            json.dumps(
                {"result": overall.value, "checks": [c.as_dict() for c in checks]},
                indent=2,
                ensure_ascii=False,
            )
        )
        return
    print("GUI Harness Doctor\n")
    for check in checks:
        print(f"{check.name:<24} {check.status.value:<8} {check.detail}")
    print(f"\nRESULT: {overall.value}")


def cmd_doctor(args) -> int:
    config = load_application_config(args.app) if args.app else None
    checks, _ = run_preflight(config)
    _print_checks(checks, args.json)
    return EXIT_CODES[_overall_status(checks)]


def cmd_list(_args) -> int:
    for name in list_scenarios():
        print(name)
    return 0


def cmd_capture(args) -> int:
    enable_per_monitor_v2()
    config = load_application_config(args.app)
    windows = Win32WindowBackend()
    target = windows.find(config.process_name, config.title_regex)
    windows.focus(target.hwnd)
    target = windows.info(target.hwnd)
    output = Path(args.output or f"artifacts/{args.app}/manual_capture.png")
    MssCaptureBackend().save_rect(target.client_rect, output)
    print(output)
    return 0


def cmd_launch(args) -> int:
    config = load_application_config(args.app)
    target = launch_application(config, timeout=args.timeout)
    payload = {
        "status": "PASS",
        "app": args.app,
        "pid": target.pid,
        "hwnd": target.hwnd,
        "title": target.title,
    }
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"Launched: {target.process_name} PID={target.pid}")
        print(f"Window: {target.title}")
    return 0


def cmd_run(args) -> int:
    status, run_dir = run_scenario(args.scenario, artifacts_root=Path(args.artifacts))
    payload = {"status": status.value, "artifacts": str(run_dir)}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Status: {status.value}")
        print(f"Artifacts: {run_dir}")
    return EXIT_CODES[status]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gui-harness")
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="Check GUI automation prerequisites.")
    doctor.add_argument("--app")
    doctor.add_argument("--json", action="store_true")
    doctor.set_defaults(func=cmd_doctor)

    listing = sub.add_parser("list", help="List scenarios.")
    listing.set_defaults(func=cmd_list)

    capture = sub.add_parser("capture", help="Capture an application client area.")
    capture.add_argument("--app", required=True)
    capture.add_argument("--output")
    capture.set_defaults(func=cmd_capture)

    launch = sub.add_parser("launch", help="Launch a configured application and wait for its window.")
    launch.add_argument("--app", required=True)
    launch.add_argument("--timeout", type=float, default=10.0)
    launch.add_argument("--json", action="store_true")
    launch.set_defaults(func=cmd_launch)

    run = sub.add_parser("run", help="Run a scenario.")
    run.add_argument("scenario")
    run.add_argument("--artifacts", default="artifacts")
    run.add_argument("--json", action="store_true")
    run.set_defaults(func=cmd_run)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except (ConfigurationError, HarnessError) as exc:
        print(f"{exc.status}: {exc}", file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
