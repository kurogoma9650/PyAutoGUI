from __future__ import annotations

from pathlib import Path

from ..errors import BlockedError
from ..models import Rect, ScreenPoint


def resolve_image(
    screenshot,
    client_rect: Rect,
    template_path: str,
    confidence: float,
) -> ScreenPoint:
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise BlockedError(
            'Image selector requires optional dependencies: pip install -e ".[vision]"'
        ) from exc

    template_file = Path(template_path)
    if not template_file.exists():
        raise BlockedError(f"Image template does not exist: {template_file}")

    haystack = cv2.cvtColor(np.asarray(screenshot), cv2.COLOR_RGB2BGR)
    needle = cv2.imread(str(template_file), cv2.IMREAD_COLOR)
    if needle is None:
        raise BlockedError(f"Could not load image template: {template_file}")

    result = cv2.matchTemplate(haystack, needle, cv2.TM_CCOEFF_NORMED)
    _, max_value, _, max_location = cv2.minMaxLoc(result)
    if max_value < confidence:
        raise BlockedError(
            f"Image selector confidence {max_value:.3f} below required {confidence:.3f}"
        )

    height, width = needle.shape[:2]
    return ScreenPoint(
        client_rect.left + max_location[0] + width // 2,
        client_rect.top + max_location[1] + height // 2,
    )
