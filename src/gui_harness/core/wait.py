from __future__ import annotations

import time

from PIL import ImageChops, ImageStat

from ..errors import BlockedError


class Waiter:
    def __init__(self, capture_callback) -> None:
        self.capture_callback = capture_callback

    @staticmethod
    def _mean_difference(a, b) -> float:
        a = a.copy()
        b = b.copy()
        a.thumbnail((320, 180))
        b.thumbnail((320, 180))
        if a.size != b.size:
            b = b.resize(a.size)
        diff = ImageChops.difference(a, b)
        return sum(ImageStat.Stat(diff).mean) / 3.0

    def visual_stable(
        self,
        *,
        timeout: float = 3.0,
        interval: float = 0.1,
        stable_frames: int = 3,
        threshold: float = 1.5,
    ) -> None:
        deadline = time.monotonic() + timeout
        previous = self.capture_callback()
        stable = 0
        while time.monotonic() < deadline:
            time.sleep(interval)
            current = self.capture_callback()
            if self._mean_difference(previous, current) <= threshold:
                stable += 1
                if stable >= stable_frames:
                    return
            else:
                stable = 0
            previous = current
        raise BlockedError("Visual state did not become stable before timeout.")
