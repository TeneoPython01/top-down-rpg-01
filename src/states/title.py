"""
src/states/title.py - Title screen state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import random

import pygame

from settings import (
    NATIVE_WIDTH,
    NATIVE_HEIGHT,
    WHITE,
    YELLOW,
    BLACK,
    DARK_BLUE,
    FONT_NAME,
    FONT_SIZE_LARGE,
    FONT_SIZE_NORMAL,
    FONT_SIZE_SMALL,
    TITLE_STAR_SEED,
    TITLE_STAR_COUNT,
)
from src.states.base_state import BaseState

if TYPE_CHECKING:
    from src.game import Game


class TitleState(BaseState):
    """Displays the game title and waits for the player to press Enter."""

    def __init__(self, game: "Game") -> None:
        super().__init__(game)
        self._blink_timer = 0.0
        self._show_prompt = True

    def enter(self) -> None:
        self._blink_timer = 0.0
        self._show_prompt = True

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                from src.states.intro import IntroState
                self.game.change_state(IntroState(self.game))
            elif event.key == pygame.K_ESCAPE:
                self.game.running = False

    def update(self, dt: float) -> None:
        self._blink_timer += dt
        if self._blink_timer >= 0.5:
            self._blink_timer = 0.0
            self._show_prompt = not self._show_prompt

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(DARK_BLUE)

        # ── Stars background ──────────────────────────────────────────────────
        rng = random.Random(TITLE_STAR_SEED)
        for _ in range(TITLE_STAR_COUNT):
            sx = rng.randint(0, NATIVE_WIDTH - 1)
            sy = rng.randint(0, NATIVE_HEIGHT // 2)
            surface.set_at((sx, sy), WHITE)

        # ── Title text ────────────────────────────────────────────────────────
        font_big = pygame.font.SysFont(FONT_NAME, FONT_SIZE_LARGE, bold=True)
        font_med = pygame.font.SysFont(FONT_NAME, FONT_SIZE_NORMAL)

        title_surf = font_big.render("Post-Pandemic Fantasy", True, YELLOW)
        sub_surf = font_med.render("Top-Down RPG", True, WHITE)

        cx = NATIVE_WIDTH // 2
        surface.blit(title_surf, title_surf.get_rect(centerx=cx, centery=70))
        surface.blit(sub_surf, sub_surf.get_rect(centerx=cx, centery=88))

        # ── Blinking prompt ───────────────────────────────────────────────────
        if self._show_prompt:
            prompt_surf = font_med.render("Press ENTER to start", True, WHITE)
            surface.blit(
                prompt_surf,
                prompt_surf.get_rect(centerx=cx, centery=140),
            )

        # ── ESC hint ─────────────────────────────────────────────────────────
        hint_surf = pygame.font.SysFont(FONT_NAME, FONT_SIZE_SMALL).render(
            "ESC: quit", True, (120, 120, 160)
        )
        surface.blit(hint_surf, hint_surf.get_rect(centerx=cx, bottom=NATIVE_HEIGHT - 4))
