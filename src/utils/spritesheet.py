"""
src/utils/spritesheet.py - Load and slice spritesheets into individual frames.
"""

from __future__ import annotations

from typing import List, Tuple

import pygame


class Spritesheet:
    """Loads a single spritesheet image and exposes methods to cut frames.

    Parameters
    ----------
    path:
        Absolute path to the spritesheet PNG.
    colorkey:
        Colour treated as transparent.  Pass ``None`` to skip.
    scale:
        Integer scale factor applied to every extracted frame.
    """

    def __init__(
        self,
        path: str,
        colorkey: Tuple[int, int, int] | None = None,
        scale: int = 1,
    ) -> None:
        self._sheet = pygame.image.load(path).convert_alpha()
        self._colorkey = colorkey
        self._scale = scale

    # ── Public API ────────────────────────────────────────────────────────────

    def get_frame(self, x: int, y: int, w: int, h: int) -> pygame.Surface:
        """Return a single frame from the sheet at pixel position (x, y).

        Parameters
        ----------
        x, y:
            Top-left corner in sheet pixels.
        w, h:
            Width and height of the frame in sheet pixels.
        """
        frame = pygame.Surface((w, h), pygame.SRCALPHA)
        frame.blit(self._sheet, (0, 0), (x, y, w, h))
        if self._colorkey is not None:
            frame.set_colorkey(self._colorkey)
        if self._scale != 1:
            frame = pygame.transform.scale(
                frame, (w * self._scale, h * self._scale)
            )
        return frame

    def get_row(
        self,
        row: int,
        frame_w: int,
        frame_h: int,
        count: int,
        start_x: int = 0,
    ) -> List[pygame.Surface]:
        """Return *count* frames from a horizontal row.

        Parameters
        ----------
        row:
            Zero-based row index.
        frame_w, frame_h:
            Dimensions of each frame in sheet pixels.
        count:
            Number of frames to extract.
        start_x:
            Pixel offset from the left edge of the sheet for the first frame.
        """
        y = row * frame_h
        return [
            self.get_frame(start_x + i * frame_w, y, frame_w, frame_h)
            for i in range(count)
        ]

    def get_grid(
        self,
        rows: int,
        cols: int,
        frame_w: int,
        frame_h: int,
    ) -> List[List[pygame.Surface]]:
        """Return a 2-D list of all frames in a grid layout."""
        return [
            self.get_row(r, frame_w, frame_h, cols)
            for r in range(rows)
        ]
