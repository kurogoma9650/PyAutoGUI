from __future__ import annotations

from pathlib import Path

import mss
from PIL import Image

from ..models import Rect


class MssCaptureBackend:
    def capture_rect(self, rect: Rect) -> Image.Image:
        region = {
            "left": rect.left,
            "top": rect.top,
            "width": rect.width,
            "height": rect.height,
        }
        with mss.mss() as sct:
            shot = sct.grab(region)
        return Image.frombytes("RGB", shot.size, shot.rgb)

    def save_rect(self, rect: Rect, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.capture_rect(rect).save(path)
        return path
