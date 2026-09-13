from __future__ import annotations

import json
import platform
import uuid
from datetime import datetime
from pathlib import Path
from time import perf_counter

from PIL import Image

from ..models import RunStatus, WindowInfo

SCHEMA_VERSION = 1


class EvidenceRecorder:
    def __init__(
        self,
        *,
        application: str,
        scenario: str,
        window: WindowInfo,
        root: Path = Path("artifacts"),
    ) -> None:
        self.application = application
        self.scenario = scenario
        self.run_id = uuid.uuid4().hex[:6]
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_scenario = scenario.replace(".", "_")
        self.run_dir = root / application / f"{stamp}_{safe_scenario}_{self.run_id}"
        self.screens_dir = self.run_dir / "screenshots"
        self.screens_dir.mkdir(parents=True, exist_ok=True)
        self.actions_path = self.run_dir / "actions.jsonl"
        self._seq = 0
        self._shot_seq = 0
        self.started_at = datetime.now().astimezone()
        self._write_manifest(window)

    def _write_manifest(self, window: WindowInfo) -> None:
        data = {
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "application": self.application,
            "scenario": self.scenario,
            "started_at": self.started_at.isoformat(),
            "platform": platform.platform(),
            "window": {
                "title": window.title,
                "pid": window.pid,
                "process_name": window.process_name,
                "session_id": window.session_id,
                "hwnd": window.hwnd,
                "client_rect": {
                    "left": window.client_rect.left,
                    "top": window.client_rect.top,
                    "right": window.client_rect.right,
                    "bottom": window.client_rect.bottom,
                },
            },
        }
        (self.run_dir / "manifest.json").write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def action(self, action: str, status: str = "PASS", **fields) -> None:
        self._seq += 1
        entry = {
            "seq": self._seq,
            "timestamp": datetime.now().astimezone().isoformat(),
            "action": action,
            "status": status,
            **fields,
        }
        with self.actions_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def timed(self, action: str):
        recorder = self

        class _Timer:
            def __enter__(self):
                self.started = perf_counter()
                return self

            def __exit__(self, exc_type, exc, _tb):
                duration_ms = round((perf_counter() - self.started) * 1000, 2)
                if exc is None:
                    recorder.action(action, "PASS", duration_ms=duration_ms)
                else:
                    recorder.action(
                        action,
                        getattr(exc, "status", "ERROR"),
                        duration_ms=duration_ms,
                        error=str(exc),
                    )
                return False

        return _Timer()

    def screenshot(self, name: str, image: Image.Image) -> Path:
        self._shot_seq += 1
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        path = self.screens_dir / f"{self._shot_seq:03d}_{safe}.png"
        image.save(path)
        self.action("capture", "PASS", name=name, path=str(path))
        return path

    def finish(self, status: RunStatus, message: str = "") -> None:
        result = {
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "status": status.value,
            "message": message,
            "finished_at": datetime.now().astimezone().isoformat(),
        }
        (self.run_dir / "result.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (self.run_dir / "result.md").write_text(
            f"# Result\n\n- Status: **{status.value}**\n- Scenario: `{self.scenario}`\n"
            f"- Run ID: `{self.run_id}`\n\n{message}\n",
            encoding="utf-8",
        )
