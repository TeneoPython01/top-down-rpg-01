"""
src/states/fade.py - FadeOverlay: smooth screen fade for zone transitions.

Usage::

    def _on_midpoint():
        # called at peak opacity — swap to the new zone / state here
        game.change_state(OverworldState(game, zone_name="silverwood_forest"))

    game.push_state(FadeOverlay(game, midpoint_callback=_on_midpoint))

The overlay fades the screen to black, calls *midpoint_callback* at peak
opacity, then fades back to transparent before removing itself.
"""

from __future__ import annotations

from typing import Callable, Optional, TYPE_CHECKING

import pygame

from settings import BLACK
from src.states.base_state import BaseState

if TYPE_CHECKING:
    from src.game import Game


class FadeOverlay(BaseState):
    """Full-screen colour fade that calls a callback at peak opacity.

    Parameters
    ----------
    game:
        The owning Game instance.
    midpoint_callback:
        Called exactly once when alpha reaches 255.  Use this to swap zones or
        change game state so the transition is hidden behind the black screen.
    duration:
        Half-duration in seconds (fade-in time = fade-out time = *duration*).
    color:
        Overlay fill colour.  Defaults to black.
    """

    is_overlay = True

    def __init__(
        self,
        game: "Game",
        midpoint_callback: Optional[Callable] = None,
        duration: float = 0.25,
        color: tuple = BLACK,
    ) -> None:
        super().__init__(game)
        self._midpoint_callback = midpoint_callback
        self._half_duration = max(0.05, duration)
        self._color = color
        self._alpha = 0
        self._midpoint_done = False
        self._fading_in = True

    def enter(self) -> None:
        self._alpha = 0
        self._midpoint_done = False
        self._fading_in = True

    def handle_input(self, event: pygame.event.Event) -> None:
        pass  # absorb all input during the fade

    def update(self, dt: float) -> None:
        rate = 255.0 / self._half_duration
        if self._fading_in:
            self._alpha = min(255, self._alpha + int(rate * dt) + 1)
            if self._alpha >= 255:
                self._alpha = 255
                self._fading_in = False
                if self._midpoint_callback and not self._midpoint_done:
                    self._midpoint_done = True
                    self._midpoint_callback()
        else:
            self._alpha = max(0, self._alpha - int(rate * dt) - 1)
            if self._alpha <= 0:
                self.game.pop_state()

    def draw(self, surface: pygame.Surface) -> None:
        if self._alpha <= 0:
            return
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((*self._color, self._alpha))
        surface.blit(overlay, (0, 0))
