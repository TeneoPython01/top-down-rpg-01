"""
src/ui/floating_text.py - Animated floating text for battle damage and healing numbers.

Each FloatingText rises upward and fades out over its lifetime.
"""

from __future__ import annotations

from typing import Tuple

import pygame


class FloatingText:
    """A short-lived animated label that floats upward and fades out.

    Attributes
    ----------
    x, y:
        Current position (native pixels).  ``y`` decreases each frame.
    text:
        String to render (e.g. "-42" or "+15").
    color:
        RGB draw colour.
    lifetime:
        Total display duration in seconds.
    remaining:
        Seconds of life remaining.
    vel_y:
        Vertical movement per second in native pixels (negative = upward).
    """

    __slots__ = ("x", "y", "text", "color", "lifetime", "remaining", "vel_y")

    def __init__(
        self,
        x: float,
        y: float,
        text: str,
        color: Tuple[int, int, int],
        lifetime: float = 1.0,
        vel_y: float = -28.0,
    ) -> None:
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.lifetime = lifetime
        self.remaining = lifetime
        self.vel_y = vel_y

    def update(self, dt: float) -> None:
        """Advance position and countdown."""
        self.remaining -= dt
        self.y += self.vel_y * dt

    @property
    def is_alive(self) -> bool:
        return self.remaining > 0

    @property
    def alpha(self) -> int:
        """Opacity: fully opaque for the first 60 %, then fade out."""
        ratio = self.remaining / max(0.001, self.lifetime)
        if ratio > 0.4:
            return 255
        return max(0, int(255 * (ratio / 0.4)))

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """Render the floating text onto *surface*."""
        if not self.is_alive:
            return
        text_surf = font.render(self.text, True, self.color)
        text_surf.set_alpha(self.alpha)
        dest = text_surf.get_rect(centerx=int(self.x), bottom=int(self.y))
        surface.blit(text_surf, dest)
