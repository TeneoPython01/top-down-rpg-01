"""
src/states/lore_reader.py - Lore book / tablet reader overlay (Feature 38).

Displays a collected lore entry as a multi-page text panel.
Navigation:
  Z / Enter / Right arrow  — next page
  Left arrow               — previous page
  ESC                      — close
"""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING, List

import pygame

from settings import (
    NATIVE_WIDTH,
    NATIVE_HEIGHT,
    WHITE,
    YELLOW,
    DARK_GRAY,
    LIGHT_GRAY,
    CYAN,
    FONT_NAME,
)

if TYPE_CHECKING:
    from src.game import Game

# Layout constants (native-pixel space)
_PANEL_X = 8
_PANEL_Y = 8
_PANEL_W = NATIVE_WIDTH - 16
_PANEL_H = NATIVE_HEIGHT - 16
_PADDING = 8
_TITLE_HEIGHT = 20   # pixels reserved for the title at the top of the panel
_NAV_HEIGHT = 14     # pixels reserved for page navigation hint at the bottom
_CHARS_PER_LINE = 38  # approximate characters per wrapped line


class LoreReaderState:
    """Overlay state that displays a lore-entry in a book-like panel.

    Parameters
    ----------
    game:
        The shared Game instance.
    lore_id:
        The ``id`` field from ``data/lore.json`` identifying the entry to show.
    """

    is_overlay: bool = True

    def __init__(self, game: "Game", lore_id: str) -> None:
        self.game = game
        self._lore_id = lore_id
        self._pages: List[List[str]] = []   # list of pages; each page = list of text lines
        self._page_idx: int = 0
        self._title: str = ""

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def enter(self) -> None:
        self._page_idx = 0
        lore_entry = self._load_entry()
        if lore_entry:
            self._title = lore_entry.get("title", "")
            raw_paragraphs: List[str] = lore_entry.get("body", [])
            self._pages = self._paginate(raw_paragraphs)
        else:
            self._title = "???"
            self._pages = [["This page is blank."]]
        self.game.audio.play_sfx("dialog_open")

    def exit(self) -> None:
        pass

    # ── Input ─────────────────────────────────────────────────────────────────

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_RETURN, pygame.K_z, pygame.K_RIGHT, pygame.K_d):
            if self._page_idx < len(self._pages) - 1:
                self._page_idx += 1
                self.game.audio.play_sfx("cursor")
            else:
                self.game.audio.play_sfx("dialog_close")
                self.game.pop_state()
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            if self._page_idx > 0:
                self._page_idx -= 1
                self.game.audio.play_sfx("cursor")
        elif event.key == pygame.K_ESCAPE:
            self.game.audio.play_sfx("dialog_close")
            self.game.pop_state()

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        pass

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        # Semi-transparent background overlay
        overlay = pygame.Surface((NATIVE_WIDTH, NATIVE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # Panel background
        panel_rect = pygame.Rect(_PANEL_X, _PANEL_Y, _PANEL_W, _PANEL_H)
        pygame.draw.rect(surface, (30, 20, 50), panel_rect)
        pygame.draw.rect(surface, (160, 100, 200), panel_rect, 2)

        font_bold = pygame.font.SysFont(FONT_NAME, 8, bold=True)
        font = pygame.font.SysFont(FONT_NAME, 7)

        # Title
        title_surf = font_bold.render(self._title, True, YELLOW)
        surface.blit(
            title_surf,
            title_surf.get_rect(
                centerx=_PANEL_X + _PANEL_W // 2,
                top=_PANEL_Y + _PADDING,
            ),
        )
        # Divider under title
        div_y = _PANEL_Y + _TITLE_HEIGHT
        pygame.draw.line(
            surface,
            (160, 100, 200),
            (_PANEL_X + _PADDING, div_y),
            (_PANEL_X + _PANEL_W - _PADDING, div_y),
            1,
        )

        # Body text
        text_y = div_y + 4
        if self._pages:
            for line in self._pages[self._page_idx]:
                if line == "":
                    text_y += 5   # blank-line spacing
                    continue
                surface.blit(font.render(line, True, WHITE), (_PANEL_X + _PADDING, text_y))
                text_y += 9

        # Page indicator & navigation hint
        total = len(self._pages)
        page_str = f"Page {self._page_idx + 1}/{total}"
        page_surf = font.render(page_str, True, LIGHT_GRAY)
        surface.blit(
            page_surf,
            page_surf.get_rect(
                right=_PANEL_X + _PANEL_W - _PADDING,
                bottom=_PANEL_Y + _PANEL_H - _PADDING,
            ),
        )

        if self._page_idx < total - 1:
            hint = font.render("Z/Enter/\u2192: next page   ESC: close", True, CYAN)
        else:
            hint = font.render("Z/Enter: close   \u2190: prev page", True, CYAN)
        surface.blit(hint, (_PANEL_X + _PADDING, _PANEL_Y + _PANEL_H - _NAV_HEIGHT - _PADDING + 2))

    # ── Private helpers ───────────────────────────────────────────────────────

    def _load_entry(self) -> dict | None:
        """Load the matching lore entry from data/lore.json."""
        import json
        import os
        from settings import DATA_DIR
        path = os.path.join(DATA_DIR, "lore.json")
        try:
            with open(path) as fh:
                entries = json.load(fh)
            for entry in entries:
                if entry.get("id") == self._lore_id:
                    return entry
        except (OSError, ValueError):
            pass
        return None

    def _paginate(self, paragraphs: List[str]) -> List[List[str]]:
        """Wrap paragraph text and split into pages that fit the panel."""
        # How many body lines fit between the title divider and the nav hint
        available_h = (
            _PANEL_H
            - _TITLE_HEIGHT       # title + divider
            - _NAV_HEIGHT         # navigation hint row
            - _PADDING * 3        # padding: top + under-divider + bottom
            - 4                   # small extra buffer
        )
        lines_per_page = max(1, available_h // 9)  # 9px per text line

        all_lines: List[str] = []
        for para in paragraphs:
            wrapped = textwrap.wrap(para, width=_CHARS_PER_LINE)
            if not wrapped:
                wrapped = [""]
            all_lines.extend(wrapped)
            all_lines.append("")   # blank line between paragraphs

        # Remove trailing blank line
        while all_lines and all_lines[-1] == "":
            all_lines.pop()

        # Split into pages
        pages: List[List[str]] = []
        for i in range(0, max(1, len(all_lines)), lines_per_page):
            pages.append(all_lines[i : i + lines_per_page])
        return pages if pages else [[]]
