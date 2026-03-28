"""
src/states/battle.py - Turn-based battle state (Phase 2).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Any

import pygame

from settings import NATIVE_WIDTH, NATIVE_HEIGHT, WHITE, YELLOW, RED, BLACK, DARK_BLUE
from src.states.base_state import BaseState
from src.ui.menu import Menu

if TYPE_CHECKING:
    from src.game import Game


_COMMANDS = ["Attack", "Magic", "Item", "Defend", "Flee"]


class BattleState(BaseState):
    """Turn-based battle scene.

    Fully implemented in Phase 2.  This stub shows the battle UI skeleton.
    """

    def __init__(self, game: "Game", enemies: List[Any], player: Any) -> None:
        super().__init__(game)
        self.enemies = enemies
        self.player = player
        self._menu = Menu(_COMMANDS, x=NATIVE_WIDTH - 70, y=NATIVE_HEIGHT - 55)
        self._message = ""
        self._message_timer = 0.0

    def enter(self) -> None:
        self._message = "Battle start!"
        self._message_timer = 2.0

    def handle_input(self, event: pygame.event.Event) -> None:
        result = self._menu.handle_input(event)
        if result == "Flee":
            self.game.pop_state()

    def update(self, dt: float) -> None:
        if self._message_timer > 0:
            self._message_timer -= dt
            if self._message_timer <= 0:
                self._message = ""

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(DARK_BLUE)

        font = pygame.font.SysFont("monospace", 8)

        # Enemy area placeholder
        ex = 20
        for enemy in self.enemies:
            if enemy.is_alive():
                pygame.draw.rect(surface, RED, (ex, 20, 32, 32))
                lbl = font.render(enemy.name, True, WHITE)
                surface.blit(lbl, (ex, 56))
                hp_lbl = font.render(f"HP:{enemy.hp}", True, (200, 200, 200))
                surface.blit(hp_lbl, (ex, 66))
                ex += 48

        # Player stats strip
        strip = pygame.Rect(0, NATIVE_HEIGHT - 55, NATIVE_WIDTH, 55)
        pygame.draw.rect(surface, (20, 20, 40), strip)
        pygame.draw.rect(surface, (100, 100, 140), strip, 1)
        surface.blit(
            font.render(
                f"{self.player.name}  HP:{self.player.hp}/{self.player.max_hp}"
                f"  MP:{self.player.mp}/{self.player.max_mp}",
                True,
                WHITE,
            ),
            (6, NATIVE_HEIGHT - 50),
        )

        # Command menu
        self._menu.draw(surface)

        # Message
        if self._message:
            msg = font.render(self._message, True, YELLOW)
            surface.blit(msg, (msg.get_rect(centerx=NATIVE_WIDTH // 2).x, 80))
