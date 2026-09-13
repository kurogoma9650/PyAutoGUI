from pathlib import Path


def test_scenarios_do_not_import_pyautogui():
    root = Path(__file__).resolve().parents[2] / "src" / "gui_harness" / "scenarios"
    offenders = []
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "import pyautogui" in text or "from pyautogui" in text:
            offenders.append(str(path))
    assert not offenders, f"Scenario modules must use RunContext, not pyautogui: {offenders}"
