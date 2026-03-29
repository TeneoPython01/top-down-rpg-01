"""
src/states/game_over.py - Game over screen (Phase 2).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from settings import NATIVE_WIDTH, NATIVE_HEIGHT, RED, WHITE, BLACK
from src.states.base_state import BaseState

if TYPE_CHECKING:
    from src.game import Game


class GameOverState(BaseState):
    """Shown when all party members are defeated."""

    def __init__(self, game: "Game") -> None:
        super().__init__(game)
        self._timer = 0.0

    def enter(self) -> None:
        self._timer = 0.0
        self.game.audio.play_music("game_over")

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                from src.states.title import TitleState
                self.game.change_state(TitleState(self.game))

    def update(self, dt: float) -> None:
        self._timer += dt

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BLACK)
        font_big = pygame.font.SysFont("monospace", 18, bold=True)
        font_sm = pygame.font.SysFont("monospace", 8)

        go_surf = font_big.render("GAME OVER", True, RED)
        surface.blit(go_surf, go_surf.get_rect(center=(NATIVE_WIDTH // 2, 80)))

        msg_surf = font_sm.render(
            "the world's chaos will grow without your light.", True, WHITE
        )
        surface.blit(msg_surf, msg_surf.get_rect(centerx=NATIVE_WIDTH // 2, top=102))

        if self._timer > 2.0:
            hint = font_sm.render("Press ENTER to return to title", True, WHITE)
            surface.blit(hint, hint.get_rect(centerx=NATIVE_WIDTH // 2, top=120))
