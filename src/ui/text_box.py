"""
src/ui/text_box.py - Reusable dialog box with typewriter text effect (Phase 4).
"""

from __future__ import annotations

import pygame

from settings import (
    NATIVE_WIDTH,
    NATIVE_HEIGHT,
    DIALOG_BOX_HEIGHT,
    DIALOG_PADDING,
    TYPEWRITER_SPEED,
    FONT_NAME,
    FONT_SIZE_NORMAL,
    WHITE,
    BLACK,
    DARK_GRAY,
    LIGHT_GRAY,
)


class TextBox:
    """Displays text in a bordered box at the bottom of the screen.

    The text appears character-by-character (typewriter effect).
    Call ``advance()`` to skip to the next page or dismiss.

    Parameters
    ----------
    text:
        Full text to display.
    width:
        Width of the text box in native pixels (defaults to full screen width).
    """

    def __init__(self, text: str, width: int = NATIVE_WIDTH) -> None:
        self._full_text = text
        self._chars_shown = 0
        self._timer = 0.0
        self._done = False
        self.width = width
        self.height = DIALOG_BOX_HEIGHT
        self.y = NATIVE_HEIGHT - self.height - 4

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def done(self) -> bool:
        """True when all characters are visible."""
        return self._done

    def advance(self) -> None:
        """Skip to the end of current text or dismiss if already done."""
        if not self._done:
            self._chars_shown = len(self._full_text)
            self._done = True

    def update(self, dt: float) -> None:
        if self._done:
            return
        self._timer += dt * 60  # convert to frame units
        while self._timer >= 1.0 / TYPEWRITER_SPEED and not self._done:
            self._timer -= 1.0 / TYPEWRITER_SPEED
            self._chars_shown += 1
            if self._chars_shown >= len(self._full_text):
                self._done = True

    def draw(self, surface: pygame.Surface) -> None:
        # Box background
        box_rect = pygame.Rect(4, self.y, self.width - 8, self.height)
        pygame.draw.rect(surface, DARK_GRAY, box_rect)
        pygame.draw.rect(surface, LIGHT_GRAY, box_rect, 2)

        # Text
        font = pygame.font.SysFont(FONT_NAME, FONT_SIZE_NORMAL)
        visible = self._full_text[: self._chars_shown]
        x = box_rect.x + DIALOG_PADDING
        y = box_rect.y + DIALOG_PADDING
        line_height = 10
        for line in visible.split("\n"):
            surf = font.render(line, True, WHITE)
            surface.blit(surf, (x, y))
            y += line_height

        # "More" indicator
        if self._done:
            indicator = font.render("▼", True, (200, 200, 100))
            surface.blit(indicator, (box_rect.right - 12, box_rect.bottom - 12))
