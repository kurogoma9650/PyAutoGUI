import pytest

from gui_harness.models import Rect, RelativePoint


def test_rect_dimensions_and_contains():
    rect = Rect(10, 20, 110, 70)
    assert rect.width == 100
    assert rect.height == 50
    assert rect.center == (60, 45)
    assert rect.contains(10, 20)
    assert rect.contains(109, 69)
    assert not rect.contains(110, 70)


def test_relative_point_rejects_out_of_range():
    with pytest.raises(ValueError):
        RelativePoint(1.1, 0.5)
