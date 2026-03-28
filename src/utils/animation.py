"""
src/utils/animation.py - Frame-based animation controller.
"""

from __future__ import annotations

from typing import List

import pygame


class Animation:
    """Cycles through a list of frames at a given speed.

    Parameters
    ----------
    frames:
        Ordered list of ``pygame.Surface`` objects.
    fps:
        Desired playback speed in frames-per-second.
    loop:
        Whether the animation loops back to frame 0 after the last frame.
    """

    def __init__(
        self,
        frames: List[pygame.Surface],
        fps: float = 8.0,
        loop: bool = True,
    ) -> None:
        self.frames = frames
        self.fps = fps
        self.loop = loop
        self._timer = 0.0
        self._index = 0
        self.done = False

    # ── Public API ────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """Advance the animation by *dt* seconds."""
        if self.done:
            return
        self._timer += dt
        frame_duration = 1.0 / self.fps
        while self._timer >= frame_duration:
            self._timer -= frame_duration
            self._index += 1
            if self._index >= len(self.frames):
                if self.loop:
                    self._index = 0
                else:
                    self._index = len(self.frames) - 1
                    self.done = True
                    break

    def reset(self) -> None:
        """Restart the animation from frame 0."""
        self._timer = 0.0
        self._index = 0
        self.done = False

    @property
    def current_frame(self) -> pygame.Surface:
        """Return the surface for the current frame."""
        return self.frames[self._index]
