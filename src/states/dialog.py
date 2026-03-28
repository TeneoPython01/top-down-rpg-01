"""
src/states/dialog.py - NPC dialog overlay state (Phase 4).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.states.base_state import BaseState
from src.ui.text_box import TextBox

if TYPE_CHECKING:
    from src.game import Game


class DialogState(BaseState):
    """Overlay state that displays dialog text line-by-line.

    Pressing Z/Enter advances the dialog; ESC skips to the end.
    """

    def __init__(self, game: "Game", lines: list[str]) -> None:
        super().__init__(game)
        self._lines = lines
        self._index = 0
        self._text_box: TextBox | None = None

    def enter(self) -> None:
        self._index = 0
        if self._lines:
            self._text_box = TextBox(self._lines[0])
        else:
            self.game.pop_state()

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_RETURN, pygame.K_z, pygame.K_SPACE):
            if self._text_box and not self._text_box.done:
                self._text_box.advance()
            else:
                self._next_line()
        elif event.key == pygame.K_ESCAPE:
            self.game.pop_state()

    def _next_line(self) -> None:
        self._index += 1
        if self._index < len(self._lines):
            self._text_box = TextBox(self._lines[self._index])
        else:
            self.game.pop_state()

    def update(self, dt: float) -> None:
        if self._text_box:
            self._text_box.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        # The underlying state is already drawn; we just add the text box.
        if self._text_box:
            self._text_box.draw(surface)
