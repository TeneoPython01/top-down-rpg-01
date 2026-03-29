"""
src/states/dialog.py - NPC dialog overlay state (Phase 4).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Optional

import pygame

from src.states.base_state import BaseState
from src.ui.text_box import TextBox

if TYPE_CHECKING:
    from src.game import Game


class DialogState(BaseState):
    """Overlay state that displays dialog text line-by-line.

    This is an *overlay* — the game loop will keep drawing the state below it
    so the world remains visible behind the dialog box.

    Pressing Z/Enter/Space advances the dialog; ESC skips to the end.

    Parameters
    ----------
    lines:
        Sequence of text strings to display, one at a time.
    speaker:
        Optional name shown in a banner above the text box.
    callback:
        Optional callable invoked after the dialog is closed (all lines shown).
    """

    is_overlay: bool = True

    def __init__(
        self,
        game: "Game",
        lines: list[str],
        speaker: str = "",
        callback: Optional[Callable] = None,
    ) -> None:
        super().__init__(game)
        self._lines = lines
        self._speaker = speaker
        self._index = 0
        self._text_box: Optional[TextBox] = None
        self._callback = callback

    def enter(self) -> None:
        self._index = 0
        self.game.audio.play_sfx("dialog_open")
        if self._lines:
            self._text_box = TextBox(self._lines[0], speaker=self._speaker)
        else:
            self._finish()

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_RETURN, pygame.K_z, pygame.K_SPACE):
            if self._text_box and not self._text_box.done:
                self._text_box.advance()
            else:
                self._next_line()
        elif event.key == pygame.K_ESCAPE:
            self._finish()

    def _next_line(self) -> None:
        self._index += 1
        if self._index < len(self._lines):
            self._text_box = TextBox(
                self._lines[self._index], speaker=self._speaker
            )
        else:
            self._finish()

    def _finish(self) -> None:
        self.game.audio.play_sfx("dialog_close")
        self.game.pop_state()
        if self._callback is not None:
            self._callback()

    def update(self, dt: float) -> None:
        if self._text_box:
            self._text_box.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        if self._text_box:
            self._text_box.draw(surface)

