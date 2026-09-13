import json

from PIL import Image

from gui_harness.evidence.recorder import EvidenceRecorder
from gui_harness.models import Rect, RunStatus, WindowInfo


def test_evidence_recorder_writes_expected_files(tmp_path):
    window = WindowInfo(
        hwnd=1,
        pid=2,
        process_name="fixture.exe",
        title="Fixture",
        window_rect=Rect(0, 0, 200, 100),
        client_rect=Rect(10, 10, 190, 90),
        visible=True,
        minimized=False,
        session_id=1,
    )
    recorder = EvidenceRecorder(
        application="fixture",
        scenario="fixture.smoke",
        window=window,
        root=tmp_path,
    )
    recorder.screenshot("before", Image.new("RGB", (10, 10)))
    recorder.finish(RunStatus.PASS, "ok")

    assert (recorder.run_dir / "manifest.json").exists()
    assert (recorder.run_dir / "actions.jsonl").exists()
    result = json.loads((recorder.run_dir / "result.json").read_text(encoding="utf-8"))
    assert result["status"] == "PASS"
