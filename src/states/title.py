"""
src/states/title.py - Title screen with New Game / Load Game menu.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Dict, Any

import random

import pygame

from settings import (
    NATIVE_WIDTH,
    NATIVE_HEIGHT,
    NUM_SAVE_SLOTS,
    WHITE,
    YELLOW,
    CYAN,
    DARK_BLUE,
    LIGHT_GRAY,
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

# Main-menu option labels
_MAIN_OPTIONS = ["New Game", "Load Game", "Options", "Quit"]


class TitleState(BaseState):
    """Displays the game title with a New Game / Load Game / Quit menu.

    Modes
    -----
    ``"main"``
        Three-item menu: New Game, Load Game, Quit.
    ``"load"``
        Slot-select sub-menu showing up to NUM_SAVE_SLOTS saves plus a Back
        option.  Selecting an occupied slot loads that save and transitions
        to the overworld.
    """

    def __init__(self, game: "Game") -> None:
        super().__init__(game)
        self._mode = "main"          # "main" | "load"
        self._cursor = 0             # cursor in main menu
        self._load_cursor = 0        # cursor in load sub-menu
        self._slot_infos: List[Optional[Dict[str, Any]]] = []

    def enter(self) -> None:
        self._mode = "main"
        self._cursor = 0
        self._load_cursor = 0
        self._slot_infos = []
        self.game.audio.play_music("title")

    # ── Input ─────────────────────────────────────────────────────────────────

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if self._mode == "main":
            self._handle_main_input(event)
        else:
            self._handle_load_input(event)

    def _handle_main_input(self, event: pygame.event.Event) -> None:
        if event.key in (pygame.K_UP, pygame.K_w):
            self._cursor = (self._cursor - 1) % len(_MAIN_OPTIONS)
            self.game.audio.play_sfx("cursor")
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self._cursor = (self._cursor + 1) % len(_MAIN_OPTIONS)
            self.game.audio.play_sfx("cursor")
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            choice = _MAIN_OPTIONS[self._cursor]
            if choice == "New Game":
                self.game.audio.play_sfx("confirm")
                self._start_new_game()
            elif choice == "Load Game":
                self.game.audio.play_sfx("confirm")
                self._open_load_menu()
            elif choice == "Options":
                self.game.audio.play_sfx("confirm")
                self._open_options()
            elif choice == "Quit":
                self.game.running = False
        elif event.key == pygame.K_ESCAPE:
            self.game.running = False

    def _handle_load_input(self, event: pygame.event.Event) -> None:
        # NUM_SAVE_SLOTS slot entries + 1 "Back" option
        num_opts = NUM_SAVE_SLOTS + 1
        if event.key in (pygame.K_UP, pygame.K_w):
            self._load_cursor = (self._load_cursor - 1) % num_opts
            self.game.audio.play_sfx("cursor")
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self._load_cursor = (self._load_cursor + 1) % num_opts
            self.game.audio.play_sfx("cursor")
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            if self._load_cursor == NUM_SAVE_SLOTS:
                # "Back" option
                self.game.audio.play_sfx("cancel")
                self._mode = "main"
            else:
                slot = self._load_cursor + 1
                if self._slot_infos[self._load_cursor] is not None:
                    self.game.audio.play_sfx("confirm")
                    self._load_slot(slot)
        elif event.key == pygame.K_ESCAPE:
            self.game.audio.play_sfx("cancel")
            self._mode = "main"

    # ── Transitions ───────────────────────────────────────────────────────────

    def _start_new_game(self) -> None:
        from src.states.intro import IntroState
        self.game.change_state(IntroState(self.game))

    def _open_load_menu(self) -> None:
        from src.systems.save_load import get_slot_info
        self._slot_infos = [get_slot_info(i) for i in range(1, NUM_SAVE_SLOTS + 1)]
        self._load_cursor = 0
        self._mode = "load"

    def _open_options(self) -> None:
        from src.states.options import OptionsState
        self.game.push_state(OptionsState(self.game))

    def _load_slot(self, slot: int) -> None:
        from src.systems.save_load import load_from_slot, apply_save_to_game
        from src.states.overworld import OverworldState

        data = load_from_slot(slot)
        if data is None:
            return
        apply_save_to_game(data, self.game)
        self.game.change_state(OverworldState(self.game, player=self.game.player))

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        pass  # no per-frame logic needed

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(DARK_BLUE)
        self._draw_stars(surface)
        self._draw_title(surface)

        if self._mode == "main":
            self._draw_main_menu(surface)
        else:
            self._draw_load_menu(surface)

    def _draw_stars(self, surface: pygame.Surface) -> None:
        rng = random.Random(TITLE_STAR_SEED)
        for _ in range(TITLE_STAR_COUNT):
            sx = rng.randint(0, NATIVE_WIDTH - 1)
            sy = rng.randint(0, NATIVE_HEIGHT // 2)
            surface.set_at((sx, sy), WHITE)

    def _draw_title(self, surface: pygame.Surface) -> None:
        font_big = pygame.font.SysFont(FONT_NAME, FONT_SIZE_LARGE, bold=True)
        font_med = pygame.font.SysFont(FONT_NAME, FONT_SIZE_NORMAL)
        cx = NATIVE_WIDTH // 2

        title_surf = font_big.render("Post-Pandemic Fantasy", True, YELLOW)
        sub_surf = font_med.render("Top-Down RPG", True, WHITE)

        surface.blit(title_surf, title_surf.get_rect(centerx=cx, centery=50))
        surface.blit(sub_surf, sub_surf.get_rect(centerx=cx, centery=66))

    def _draw_main_menu(self, surface: pygame.Surface) -> None:
        font = pygame.font.SysFont(FONT_NAME, FONT_SIZE_NORMAL)
        font_sm = pygame.font.SysFont(FONT_NAME, FONT_SIZE_SMALL)
        cx = NATIVE_WIDTH // 2
        start_y = 95

        for i, label in enumerate(_MAIN_OPTIONS):
            y = start_y + i * 16
            color = YELLOW if i == self._cursor else WHITE
            prefix = "> " if i == self._cursor else "  "
            surf = font.render(f"{prefix}{label}", True, color)
            surface.blit(surf, surf.get_rect(centerx=cx, centery=y))

        hint = font_sm.render(
            "Up/Down: select  Enter: confirm  ESC: quit", True, (120, 120, 160)
        )
        surface.blit(hint, hint.get_rect(centerx=cx, bottom=NATIVE_HEIGHT - 4))

    def _draw_load_menu(self, surface: pygame.Surface) -> None:
        font = pygame.font.SysFont(FONT_NAME, FONT_SIZE_NORMAL)
        font_sm = pygame.font.SysFont(FONT_NAME, FONT_SIZE_SMALL)
        cx = NATIVE_WIDTH // 2

        header = font.render("Load Game", True, YELLOW)
        surface.blit(header, header.get_rect(centerx=cx, centery=82))

        pygame.draw.line(surface, LIGHT_GRAY, (8, 90), (NATIVE_WIDTH - 8, 90), 1)

        slot_start_y = 100
        for i in range(NUM_SAVE_SLOTS):
            y = slot_start_y + i * 16
            info = self._slot_infos[i]
            color = YELLOW if i == self._load_cursor else WHITE

            if info is not None:
                label = (
                    f"Slot {i + 1}  {info['name']}"
                    f"  Lv.{info['level']}"
                    f"  {info['location']}"
                    f"  {info['timestamp']}"
                )
            else:
                label = f"Slot {i + 1}  (empty)"

            prefix = "> " if i == self._load_cursor else "  "
            surf = font_sm.render(f"{prefix}{label}", True, color)
            surface.blit(surf, surf.get_rect(centerx=cx, centery=y))

        # "Back" option
        back_y = slot_start_y + NUM_SAVE_SLOTS * 16
        back_color = YELLOW if self._load_cursor == NUM_SAVE_SLOTS else LIGHT_GRAY
        back_prefix = "> " if self._load_cursor == NUM_SAVE_SLOTS else "  "
        back_surf = font_sm.render(f"{back_prefix}Back", True, back_color)
        surface.blit(back_surf, back_surf.get_rect(centerx=cx, centery=back_y))

        hint = font_sm.render(
            "Up/Down: select  Enter: load  ESC: back", True, (120, 120, 160)
        )
        surface.blit(hint, hint.get_rect(centerx=cx, bottom=NATIVE_HEIGHT - 4))
