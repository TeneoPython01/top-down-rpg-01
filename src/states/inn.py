"""
src/states/inn.py - Inn rest state (Phase 4).

Overlay that lets the player pay gold to rest, restoring HP/MP.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from settings import (
    NATIVE_WIDTH,
    NATIVE_HEIGHT,
    FONT_NAME,
    FONT_SIZE_LARGE,
    FONT_SIZE_NORMAL,
    FONT_SIZE_SMALL,
    INN_COST,
    WHITE,
    YELLOW,
    RED,
    BLACK,
)
from src.states.base_state import BaseState
from src.ui.menu import Menu

if TYPE_CHECKING:
    from src.game import Game


class InnState(BaseState):
    """Prompt the player to pay gold and rest at the inn.

    After resting successfully the overlay stays visible for a short time
    showing a confirmation message, then auto-closes.
    """

    def __init__(self, game: "Game") -> None:
        super().__init__(game)
        self._cost = INN_COST
        self._menu = Menu(
            ["Yes", "No"],
            x=NATIVE_WIDTH // 2 - 14,
            y=NATIVE_HEIGHT // 2 + 10,
        )
        self._message = ""
        self._message_timer = 0.0
        self._rested = False  # True once gold has been deducted

    # ── Input ─────────────────────────────────────────────────────────────────

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if self._rested:
            return  # waiting for auto-close; ignore further input

        if event.key == pygame.K_ESCAPE:
            self.game.pop_state()
            return

        result = self._menu.handle_input(event)
        if result == "Yes":
            if self.game.inventory.gold >= self._cost:
                self.game.inventory.gold -= self._cost
                self._rested = True
                self._message = "You rested well! HP and MP restored."
                self._message_timer = 2.5
                # Restore HP and MP on the player.
                if self.game.player is not None:
                    self.game.player.hp = self.game.player.max_hp
                    self.game.player.mp = self.game.player.max_mp
            else:
                self._message = "Not enough gold!"
                self._message_timer = 2.0
        elif result == "No":
            self.game.pop_state()

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        if self._message_timer > 0:
            self._message_timer = max(0.0, self._message_timer - dt)
            if self._message_timer <= 0 and self._rested:
                self.game.pop_state()

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        # Semi-transparent dark overlay (drawn on top of the town)
        overlay = pygame.Surface((NATIVE_WIDTH, NATIVE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surface.blit(overlay, (0, 0))

        font_big = pygame.font.SysFont(FONT_NAME, FONT_SIZE_LARGE, bold=True)
        font_n = pygame.font.SysFont(FONT_NAME, FONT_SIZE_NORMAL)
        font_s = pygame.font.SysFont(FONT_NAME, FONT_SIZE_SMALL)
        cx = NATIVE_WIDTH // 2
        cy = NATIVE_HEIGHT // 2

        # Title
        title = font_big.render("Welcome to the Inn!", True, YELLOW)
        surface.blit(title, title.get_rect(centerx=cx, centery=cy - 32))

        if not self._rested:
            # Prompt
            prompt = font_n.render(
                f"Rest here for {self._cost} gold?", True, WHITE
            )
            surface.blit(prompt, prompt.get_rect(centerx=cx, centery=cy - 10))
            # Gold remaining
            gold_surf = font_s.render(
                f"Your gold: {self.game.inventory.gold}G", True, (180, 180, 180)
            )
            surface.blit(gold_surf, gold_surf.get_rect(centerx=cx, centery=cy + 2))
            self._menu.draw(surface)

        # Feedback message
        if self._message_timer > 0:
            color = YELLOW if self._rested else RED
            msg_surf = font_n.render(self._message, True, color)
            surface.blit(msg_surf, msg_surf.get_rect(centerx=cx, centery=cy + 28))
