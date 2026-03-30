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
    YELLOW,
)


class TextBox:
    """Displays text in a bordered box at the bottom of the screen.

    The text appears character-by-character (typewriter effect).
    Call ``advance()`` to skip to the next page or dismiss.

    Parameters
    ----------
    text:
        Full text to display.
    speaker:
        Optional name of the speaker shown as a banner above the box.
    width:
        Width of the text box in native pixels (defaults to full screen width).
    speed:
        Typewriter characters-per-frame override.  Defaults to the global
        ``TYPEWRITER_SPEED`` constant if not provided (or if ``None``).
    """

    def __init__(
        self,
        text: str,
        speaker: str = "",
        width: int = NATIVE_WIDTH,
        speed: int | None = None,
    ) -> None:
        self._full_text = text
        self._speaker = speaker
        self._chars_shown = 0
        self._timer = 0.0
        self._done = False
        self.width = width
        self.height = DIALOG_BOX_HEIGHT
        self.y = NATIVE_HEIGHT - self.height - 4
        self._speed = speed if speed is not None else TYPEWRITER_SPEED

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
        while self._timer >= 1.0 / self._speed and not self._done:
            self._timer -= 1.0 / self._speed
            self._chars_shown += 1
            if self._chars_shown >= len(self._full_text):
                self._done = True

    def draw(self, surface: pygame.Surface) -> None:
        font = pygame.font.SysFont(FONT_NAME, FONT_SIZE_NORMAL)

        # Speaker name banner (drawn just above the main box)
        if self._speaker:
            name_w = font.size(self._speaker)[0] + DIALOG_PADDING * 2
            name_h = FONT_SIZE_NORMAL + DIALOG_PADDING
            name_rect = pygame.Rect(4, self.y - name_h - 1, name_w, name_h)
            pygame.draw.rect(surface, DARK_GRAY, name_rect)
            pygame.draw.rect(surface, LIGHT_GRAY, name_rect, 1)
            name_surf = font.render(self._speaker, True, YELLOW)
            surface.blit(
                name_surf,
                (name_rect.x + DIALOG_PADDING, name_rect.y + DIALOG_PADDING // 2),
            )

        # Box background
        box_rect = pygame.Rect(4, self.y, self.width - 8, self.height)
        pygame.draw.rect(surface, DARK_GRAY, box_rect)
        pygame.draw.rect(surface, LIGHT_GRAY, box_rect, 2)

        # Text
        visible = self._full_text[: self._chars_shown]
        x = box_rect.x + DIALOG_PADDING
        y = box_rect.y + DIALOG_PADDING
        line_height = 10
        max_text_w = box_rect.width - DIALOG_PADDING * 2
        for raw_line in visible.split("\n"):
            for wrapped_line in self._wrap_line(font, raw_line, max_text_w):
                surf = font.render(wrapped_line, True, WHITE)
                surface.blit(surf, (x, y))
                y += line_height

        # "More" indicator
        if self._done:
            indicator = font.render("▼", True, (200, 200, 100))
            surface.blit(indicator, (box_rect.right - 12, box_rect.bottom - 12))

    def _wrap_line(self, font: pygame.font.Font, line: str, max_width: int) -> list[str]:
        """Break *line* into sub-lines that each fit within *max_width* pixels."""
        words = line.split(" ")
        wrapped: list[str] = []
        current = ""
        for word in words:
            test = (current + " " + word) if current else word
            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    wrapped.append(current)
                current = word
        if current:
            wrapped.append(current)
        return wrapped or [""]
