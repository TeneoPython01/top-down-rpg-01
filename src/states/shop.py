"""
src/states/shop.py - Buy/sell shop state (Phase 4).
"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, List, Dict, Any

import pygame

from settings import (
    NATIVE_WIDTH,
    NATIVE_HEIGHT,
    FONT_NAME,
    FONT_SIZE_NORMAL,
    FONT_SIZE_SMALL,
    WHITE,
    YELLOW,
    CYAN,
    RED,
    DARK_GRAY,
    LIGHT_GRAY,
    DATA_DIR,
)
from src.states.base_state import BaseState
from src.ui.menu import Menu

if TYPE_CHECKING:
    from src.game import Game

_MODE_MAIN = "main"
_MODE_BUY = "buy"
_MODE_SELL = "sell"


class ShopState(BaseState):
    """Buy/sell interface.

    Parameters
    ----------
    game:
        The Game instance (provides ``game.inventory`` for gold/items).
    shop_id:
        Key into ``data/shops.json`` (e.g. ``"ashenvale"``).
    """

    def __init__(self, game: "Game", shop_id: str) -> None:
        super().__init__(game)
        self.shop_id = shop_id
        self._mode = _MODE_MAIN
        self._message = ""
        self._message_timer = 0.0
        self._message_is_error = False

        # Loaded from JSON
        self._shop_name = "Shop"
        self._buy_items: List[Dict[str, Any]] = []
        self._all_items: Dict[str, Dict[str, Any]] = {}
        self._sell_item_ids: List[str] = []

        self._load_shop_data()

        # Menus
        self._main_menu = Menu(["Buy", "Sell", "Exit"], x=20, y=24)
        self._buy_menu: Menu | None = None
        self._sell_menu: Menu | None = None
        self._build_buy_menu()

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_shop_data(self) -> None:
        try:
            with open(os.path.join(DATA_DIR, "items.json"), encoding="utf-8") as fh:
                items_list: List[Dict[str, Any]] = json.load(fh)
            self._all_items = {item["id"]: item for item in items_list}
        except (OSError, json.JSONDecodeError):
            self._all_items = {}

        try:
            with open(os.path.join(DATA_DIR, "shops.json"), encoding="utf-8") as fh:
                all_shops: Dict[str, Any] = json.load(fh)
            shop = all_shops.get(self.shop_id, {"name": "Shop", "items": []})
        except (OSError, json.JSONDecodeError):
            shop = {"name": "Shop", "items": []}

        self._shop_name = shop.get("name", "Shop")
        self._buy_items = [
            self._all_items[iid]
            for iid in shop.get("items", [])
            if iid in self._all_items
        ]

    def _get_sell_price(self, item_id: str) -> int:
        """Return the sell price (50 % of buy price) or 0 if not sellable."""
        item = self._all_items.get(item_id)
        if item and item.get("price", 0) > 0:
            return item["price"] // 2
        return 0

    # ── Menu builders ─────────────────────────────────────────────────────────

    def _build_buy_menu(self) -> None:
        options = [
            f"{item['name'][:13]:<13} {item['price']:>5}G"
            for item in self._buy_items
        ]
        options.append("Back")
        self._buy_menu = Menu(options, x=8, y=18)

    def _build_sell_menu(self) -> None:
        inv = self.game.inventory
        self._sell_item_ids = []
        options: List[str] = []

        for iid in sorted(inv.items):
            cnt = inv.items[iid]
            if cnt <= 0:
                continue
            sell_price = self._get_sell_price(iid)
            if sell_price <= 0:
                continue
            item = self._all_items.get(iid, {"name": iid})
            name = item["name"][:11]
            options.append(f"{name:<11} x{cnt:>2}  {sell_price:>4}G")
            self._sell_item_ids.append(iid)

        if not options:
            options = ["(nothing to sell)"]
        options.append("Back")
        self._sell_menu = Menu(options, x=8, y=18)

    # ── Input ─────────────────────────────────────────────────────────────────

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            if self._mode == _MODE_MAIN:
                self.game.pop_state()
            else:
                self._mode = _MODE_MAIN
            return

        if self._mode == _MODE_MAIN:
            result = self._main_menu.handle_input(event)
            if result == "Buy":
                self._mode = _MODE_BUY
                self._build_buy_menu()
            elif result == "Sell":
                self._mode = _MODE_SELL
                self._build_sell_menu()
            elif result == "Exit":
                self.game.pop_state()

        elif self._mode == _MODE_BUY:
            assert self._buy_menu is not None
            result = self._buy_menu.handle_input(event)
            if result == "Back":
                self._mode = _MODE_MAIN
            elif result is not None:
                idx = self._buy_menu.selected
                if idx < len(self._buy_items):
                    self._buy_item(self._buy_items[idx])

        elif self._mode == _MODE_SELL:
            assert self._sell_menu is not None
            result = self._sell_menu.handle_input(event)
            if result in ("Back", "(nothing to sell)"):
                self._mode = _MODE_MAIN
            elif result is not None:
                idx = self._sell_menu.selected
                if idx < len(self._sell_item_ids):
                    self._sell_item(self._sell_item_ids[idx])

    # ── Transactions ──────────────────────────────────────────────────────────

    def _buy_item(self, item: Dict[str, Any]) -> None:
        price: int = item.get("price", 0)
        if self.game.inventory.gold >= price:
            self.game.inventory.gold -= price
            self.game.inventory.add(item["id"])
            self.game.audio.play_sfx("item_get")
            self._show_message(f"Bought {item['name']}!")
        else:
            self._show_message("Not enough gold!", is_error=True)

    def _sell_item(self, item_id: str) -> None:
        sell_price = self._get_sell_price(item_id)
        if sell_price > 0 and self.game.inventory.remove(item_id):
            self.game.inventory.gold += sell_price
            item = self._all_items.get(item_id, {"name": item_id})
            self._show_message(f"Sold {item['name']} for {sell_price}G!")
            self._build_sell_menu()  # refresh list after selling
        else:
            self._show_message("Can't sell that here.", is_error=True)

    def _show_message(self, text: str, duration: float = 2.0, is_error: bool = False) -> None:
        self._message = text
        self._message_timer = duration
        self._message_is_error = is_error

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        if self._message_timer > 0:
            self._message_timer = max(0.0, self._message_timer - dt)

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(DARK_GRAY)
        pygame.draw.rect(surface, LIGHT_GRAY, surface.get_rect(), 2)

        font_n = pygame.font.SysFont(FONT_NAME, FONT_SIZE_NORMAL)
        font_s = pygame.font.SysFont(FONT_NAME, FONT_SIZE_SMALL)

        # Shop name — top centre
        name_surf = pygame.font.SysFont(FONT_NAME, FONT_SIZE_NORMAL, bold=True).render(
            self._shop_name, True, YELLOW
        )
        surface.blit(name_surf, name_surf.get_rect(centerx=NATIVE_WIDTH // 2, top=4))

        # Gold — top right
        gold_surf = font_s.render(
            f"Gold: {self.game.inventory.gold}G", True, YELLOW
        )
        surface.blit(gold_surf, (NATIVE_WIDTH - gold_surf.get_width() - 4, 4))

        # Mode-specific rendering
        if self._mode == _MODE_MAIN:
            self._main_menu.draw(surface)

        elif self._mode == _MODE_BUY:
            assert self._buy_menu is not None
            lbl = font_s.render("── Buy ──", True, WHITE)
            surface.blit(lbl, (8, 8))
            self._buy_menu.draw(surface)
            # Item description at bottom
            idx = self._buy_menu.selected
            if idx < len(self._buy_items):
                desc = self._buy_items[idx].get("description", "")
                if desc:
                    desc_surf = font_s.render(desc[:38], True, (180, 180, 180))
                    surface.blit(
                        desc_surf,
                        desc_surf.get_rect(left=6, bottom=NATIVE_HEIGHT - 14),
                    )

        elif self._mode == _MODE_SELL:
            assert self._sell_menu is not None
            lbl = font_s.render("── Sell ──", True, WHITE)
            surface.blit(lbl, (8, 8))
            self._sell_menu.draw(surface)

        # Feedback message — bottom centre
        if self._message_timer > 0:
            color = RED if self._message_is_error else CYAN
            msg_surf = font_s.render(self._message, True, color)
            surface.blit(
                msg_surf,
                msg_surf.get_rect(centerx=NATIVE_WIDTH // 2, bottom=NATIVE_HEIGHT - 3),
            )
