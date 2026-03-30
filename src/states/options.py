"""
src/states/options.py - In-game Options / Settings menu (Feature #19).

Accessible from:
  - The title screen  (``O`` key or menu item "Options")
  - The pause menu    (tab label "Options")

Settings exposed
----------------
Music Volume   : float  0 % – 100 % (step 5 %)
SFX Volume     : float  0 % – 100 % (step 5 %)
Battle Speed   : Normal / Fast / Instant
Text Speed     : Slow / Normal / Fast

All changes are written to ``data/config.json`` immediately so they survive
between sessions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple

import pygame

from settings import (
    BATTLE_SPEED_LABELS,
    BATTLE_SPEED_VALUES,
    CYAN,
    DARK_BLUE,
    DARK_GRAY,
    FONT_NAME,
    FONT_SIZE_NORMAL,
    FONT_SIZE_SMALL,
    LIGHT_GRAY,
    NATIVE_HEIGHT,
    NATIVE_WIDTH,
    WHITE,
    YELLOW,
)
from src.states.base_state import BaseState
from src.systems.config import TEXT_SPEED_LABELS, TEXT_SPEED_VALUES

if TYPE_CHECKING:
    from src.game import Game

# ── Row definitions ──────────────────────────────────────────────────────────
# Each row is a (label, config_key, kind) tuple.
# kind is "pct" for 0-1 float stored as percent steps, "choice" for index list.
_ROWS: List[Tuple[str, str, str]] = [
    ("Music Volume",  "music_volume",  "pct"),
    ("SFX Volume",    "sfx_volume",    "pct"),
    ("Battle Speed",  "battle_speed",  "choice"),
    ("Text Speed",    "text_speed",    "choice"),
]

_CHOICE_LABELS = {
    "battle_speed": BATTLE_SPEED_LABELS,
    "text_speed":   TEXT_SPEED_LABELS,
}

_PCT_STEP = 0.05   # 5 % increment for volume sliders


class OptionsState(BaseState):
    """Full-screen options menu.

    Popped off the stack (returning to the caller) when the player presses
    **Esc** or selects the **Back** item.  All changes take effect immediately
    and are auto-saved.
    """

    is_overlay = False   # draw over a dark background, not the underlying scene

    def __init__(self, game: "Game") -> None:
        super().__init__(game)
        self._cursor = 0

    def enter(self) -> None:
        # Snap volumes to the nearest 5 % step for display consistency
        cfg = self.game.config
        cfg["music_volume"] = round(cfg.get("music_volume", 0.5) / _PCT_STEP) * _PCT_STEP
        cfg["sfx_volume"]   = round(cfg.get("sfx_volume",   0.7) / _PCT_STEP) * _PCT_STEP

    # ── Input ─────────────────────────────────────────────────────────────────

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        num_rows = len(_ROWS) + 1  # +1 for the "Back" row
        if event.key in (pygame.K_UP, pygame.K_w):
            self._cursor = (self._cursor - 1) % num_rows
            self.game.audio.play_sfx("cursor")

        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self._cursor = (self._cursor + 1) % num_rows
            self.game.audio.play_sfx("cursor")

        elif event.key in (pygame.K_LEFT, pygame.K_a):
            if self._cursor < len(_ROWS):
                self._adjust(_ROWS[self._cursor], -1)
                self.game.audio.play_sfx("cursor")

        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            if self._cursor < len(_ROWS):
                self._adjust(_ROWS[self._cursor], +1)
                self.game.audio.play_sfx("cursor")

        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_z):
            if self._cursor == len(_ROWS):
                self._back()
            else:
                self._adjust(_ROWS[self._cursor], +1)
                self.game.audio.play_sfx("cursor")

        elif event.key == pygame.K_ESCAPE:
            self._back()

    # ── Logic helpers ─────────────────────────────────────────────────────────

    def _adjust(self, row: Tuple[str, str, str], direction: int) -> None:
        _, key, kind = row
        cfg = self.game.config
        if kind == "pct":
            val = cfg.get(key, 0.5)
            val = round(val / _PCT_STEP) * _PCT_STEP
            val = max(0.0, min(1.0, val + direction * _PCT_STEP))
            cfg[key] = round(val / _PCT_STEP) * _PCT_STEP  # stay on grid
        else:  # "choice"
            choices = _CHOICE_LABELS[key]
            idx = int(cfg.get(key, 0))
            cfg[key] = (idx + direction) % len(choices)
        # Persist and re-apply immediately
        self.game.save_config()

    def _back(self) -> None:
        self.game.audio.play_sfx("cancel")
        self.game.pop_state()

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        pass

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(DARK_BLUE)
        self._draw_title(surface)
        self._draw_rows(surface)
        self._draw_hint(surface)

    def _draw_title(self, surface: pygame.Surface) -> None:
        font = pygame.font.SysFont(FONT_NAME, FONT_SIZE_NORMAL, bold=True)
        cx = NATIVE_WIDTH // 2
        title_s = font.render("Options", True, YELLOW)
        surface.blit(title_s, title_s.get_rect(centerx=cx, centery=18))
        pygame.draw.line(surface, LIGHT_GRAY, (8, 26), (NATIVE_WIDTH - 8, 26), 1)

    def _draw_rows(self, surface: pygame.Surface) -> None:
        font = pygame.font.SysFont(FONT_NAME, FONT_SIZE_NORMAL)
        font_sm = pygame.font.SysFont(FONT_NAME, FONT_SIZE_SMALL)
        cfg = self.game.config
        cx = NATIVE_WIDTH // 2
        start_y = 42
        row_h = 18

        for i, (label, key, kind) in enumerate(_ROWS):
            y = start_y + i * row_h
            selected = (i == self._cursor)
            label_color = YELLOW if selected else WHITE

            if kind == "pct":
                val = cfg.get(key, 0.5)
                pct = int(round(val * 100))
                # Draw bar
                bar_x, bar_y = cx - 30, y - 3
                bar_w, bar_h = 60, 6
                pygame.draw.rect(surface, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h))
                filled = int(bar_w * val)
                bar_color = CYAN if selected else LIGHT_GRAY
                if filled > 0:
                    pygame.draw.rect(surface, bar_color, (bar_x, bar_y, filled, bar_h))
                pygame.draw.rect(surface, LIGHT_GRAY, (bar_x, bar_y, bar_w, bar_h), 1)
                value_s = font_sm.render(f"{pct}%", True, label_color)
                surface.blit(value_s, value_s.get_rect(left=bar_x + bar_w + 4, centery=y))
            else:
                choices = _CHOICE_LABELS[key]
                idx = int(cfg.get(key, 0))
                choice_text = choices[idx] if 0 <= idx < len(choices) else "?"
                arrow_l = "< " if idx > 0 else "  "
                arrow_r = " >" if idx < len(choices) - 1 else "  "
                value_str = f"{arrow_l}{choice_text}{arrow_r}"
                value_s = font_sm.render(value_str, True, CYAN if selected else LIGHT_GRAY)
                surface.blit(value_s, value_s.get_rect(centerx=cx + 40, centery=y))

            prefix = "> " if selected else "  "
            lbl_s = font.render(f"{prefix}{label}", True, label_color)
            surface.blit(lbl_s, lbl_s.get_rect(right=cx - 36, centery=y))

        # "Back" row
        back_y = start_y + len(_ROWS) * row_h
        selected_back = (self._cursor == len(_ROWS))
        back_color = YELLOW if selected_back else LIGHT_GRAY
        back_prefix = "> " if selected_back else "  "
        back_s = font.render(f"{back_prefix}Back", True, back_color)
        surface.blit(back_s, back_s.get_rect(centerx=cx, centery=back_y))

    def _draw_hint(self, surface: pygame.Surface) -> None:
        font = pygame.font.SysFont(FONT_NAME, FONT_SIZE_SMALL)
        hint = font.render(
            "Up/Down: select   Left/Right: change   ESC: back",
            True, (100, 100, 140),
        )
        surface.blit(hint, hint.get_rect(centerx=NATIVE_WIDTH // 2, bottom=NATIVE_HEIGHT - 4))
