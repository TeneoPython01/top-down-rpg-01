"""
src/ui/menu.py - Reusable menu component with cursor navigation (Phase 3 & 6).

Phase 6: animated ▶ cursor that bobs left/right.
"""

from __future__ import annotations

import math
from typing import List

import pygame

from settings import WHITE, YELLOW, DARK_GRAY, LIGHT_GRAY, FONT_NAME, FONT_SIZE_NORMAL, MENU_CURSOR_BG


class Menu:
    """A vertical list of text options with a cursor.

    Parameters
    ----------
    options:
        List of option labels.
    x, y:
        Top-left position in native pixels.
    item_height:
        Vertical spacing between items in native pixels.
    """

    def __init__(
        self,
        options: List[str],
        x: int,
        y: int,
        item_height: int = 12,
        padding: int = 4,
    ) -> None:
        self.options = options
        self.x = x
        self.y = y
        self.item_height = item_height
        self.padding = padding
        self._cursor = 0

    @property
    def selected(self) -> int:
        return self._cursor

    @property
    def selected_option(self) -> str:
        return self.options[self._cursor]

    def move_up(self) -> None:
        self._cursor = (self._cursor - 1) % len(self.options)

    def move_down(self) -> None:
        self._cursor = (self._cursor + 1) % len(self.options)

    def set_cursor(self, index: int) -> None:
        """Set the cursor to *index* (clamped to valid range)."""
        self._cursor = index % len(self.options)

    def handle_input(self, event: pygame.event.Event, on_move=None) -> str | None:
        """Handle navigation keys.  Returns the selected option label on confirm.

        Parameters
        ----------
        on_move:
            Optional zero-argument callable invoked whenever the cursor moves
            (used by callers to play a cursor-movement sound effect).
        """
        if event.type != pygame.KEYDOWN:
            return None
        if event.key in (pygame.K_UP, pygame.K_w):
            self.move_up()
            if on_move is not None:
                on_move()
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.move_down()
            if on_move is not None:
                on_move()
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_z):
            return self.selected_option
        return None

    def draw(self, surface: pygame.Surface) -> None:
        font = pygame.font.SysFont(FONT_NAME, FONT_SIZE_NORMAL)
        # Phase-6: bobbing cursor offset — uses wall-clock time so it animates
        # even when no events are being processed.
        t = pygame.time.get_ticks() / 1000.0
        cursor_x_offset = int(math.sin(t * 7.0) * 1.5) + 1  # oscillates 0–3 px

        for i, option in enumerate(self.options):
            color = YELLOW if i == self._cursor else WHITE
            text_surf = font.render(option, True, color)
            iy = self.y + i * self.item_height
            if i == self._cursor:
                bg = pygame.Rect(
                    self.x - self.padding,
                    iy - 1,
                    text_surf.get_width() + self.padding * 2 + 10,
                    self.item_height,
                )
                pygame.draw.rect(surface, MENU_CURSOR_BG, bg)
                cursor_surf = font.render("▶", True, YELLOW)
                surface.blit(cursor_surf, (self.x + cursor_x_offset, iy))
            surface.blit(text_surf, (self.x + 10, iy))
