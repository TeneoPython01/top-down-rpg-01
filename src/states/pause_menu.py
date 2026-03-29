"""
src/states/pause_menu.py - Pause/inventory menu (Phase 3).

Tabs:
  Items      — use healing consumables
  Equipment  — equip/unequip gear, view bonuses
  Magic      — view known spells and descriptions
  Stats      — view character stats
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Dict, Any

import pygame

from settings import NATIVE_WIDTH, NATIVE_HEIGHT, WHITE, YELLOW, DARK_GRAY, LIGHT_GRAY, CYAN, GREEN, RED, NUM_SAVE_SLOTS
from src.states.base_state import BaseState
from src.ui.menu import Menu
from src.systems.inventory import load_items, Inventory
from src.systems.magic import load_spells
from src.systems.save_load import get_slot_info, save_to_slot

if TYPE_CHECKING:
    from src.game import Game


_TABS = ["Items", "Equipment", "Magic", "Stats", "Save"]


class PauseMenuState(BaseState):
    """Out-of-battle pause menu with tabs: Items, Equipment, Magic, Stats, Save."""

    is_overlay = True

    def __init__(self, game: "Game", player: Any) -> None:
        super().__init__(game)
        self.player = player
        self._tab_idx = 0
        self._tab_menu = Menu(_TABS, x=8, y=20, item_height=14)

        # Per-tab cursors
        self._items_cursor = 0
        self._equip_cursor = 0
        self._magic_cursor = 0
        self._save_cursor = 0

        self._message = ""
        self._message_timer = 0.0

        self._all_items: Dict[str, Any] = {}
        self._all_spells: Dict[str, Any] = {}
        self._slot_infos: List[Any] = []

        # Which pane has focus: "tabs" or "content"
        self._focus = "tabs"

    def enter(self) -> None:
        self._all_items = load_items()
        self._all_spells = load_spells()
        self._message = ""
        self._message_timer = 0.0
        self._focus = "tabs"
        self._slot_infos = [get_slot_info(i) for i in range(1, NUM_SAVE_SLOTS + 1)]

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            if self._focus == "content":
                self.game.audio.play_sfx("cancel")
                self._focus = "tabs"
            else:
                self.game.audio.play_sfx("cancel")
                self.game.pop_state()
            return

        if self._focus == "tabs":
            # Left/right arrow keys navigate the horizontal tab bar directly.
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self._tab_idx = (self._tab_idx - 1) % len(_TABS)
                self._tab_menu._cursor = self._tab_idx
                self.game.audio.play_sfx("cursor")
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._tab_idx = (self._tab_idx + 1) % len(_TABS)
                self._tab_menu._cursor = self._tab_idx
                self.game.audio.play_sfx("cursor")
            else:
                result = self._tab_menu.handle_input(event, on_move=lambda: self.game.audio.play_sfx("cursor"))
                self._tab_idx = self._tab_menu.selected
                if result:
                    self.game.audio.play_sfx("confirm")
                    self._focus = "content"
                    self._items_cursor = 0
                    self._equip_cursor = 0
                    self._magic_cursor = 0
                    self._save_cursor = 0
        else:
            self._handle_content_input(event)

    def _handle_content_input(self, event: pygame.event.Event) -> None:
        tab = _TABS[self._tab_idx]

        if tab == "Items":
            items = self._get_healing_items()
            if not items:
                return
            keys = list(items.keys())
            if event.key in (pygame.K_UP, pygame.K_w):
                self._items_cursor = (self._items_cursor - 1) % len(keys)
                self.game.audio.play_sfx("cursor")
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._items_cursor = (self._items_cursor + 1) % len(keys)
                self.game.audio.play_sfx("cursor")
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_z):
                item_id = keys[self._items_cursor % len(keys)]
                success, msg = self.player.inventory.use_item(item_id, self.player)
                self.game.audio.play_sfx("item_use")
                self._message = msg
                self._message_timer = 2.5

        elif tab == "Equipment":
            slots = list(Inventory.SLOTS)
            if event.key in (pygame.K_UP, pygame.K_w):
                self._equip_cursor = (self._equip_cursor - 1) % len(slots)
                self.game.audio.play_sfx("cursor")
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._equip_cursor = (self._equip_cursor + 1) % len(slots)
                self.game.audio.play_sfx("cursor")
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_z):
                slot = slots[self._equip_cursor]
                self.game.audio.play_sfx("confirm")
                self._open_equip_submenu(slot)
            elif event.key == pygame.K_x:
                # Unequip
                slot = slots[self._equip_cursor]
                ok, msg = self.player.inventory.unequip_slot(slot, self.player)
                self.game.audio.play_sfx("cancel")
                self._message = msg
                self._message_timer = 2.5

        elif tab == "Magic":
            known = self.player.known_spells
            if not known:
                return
            if event.key in (pygame.K_UP, pygame.K_w):
                self._magic_cursor = (self._magic_cursor - 1) % len(known)
                self.game.audio.play_sfx("cursor")
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._magic_cursor = (self._magic_cursor + 1) % len(known)
                self.game.audio.play_sfx("cursor")

        elif tab == "Save":
            if event.key in (pygame.K_UP, pygame.K_w):
                self._save_cursor = (self._save_cursor - 1) % NUM_SAVE_SLOTS
                self.game.audio.play_sfx("cursor")
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._save_cursor = (self._save_cursor + 1) % NUM_SAVE_SLOTS
                self.game.audio.play_sfx("cursor")
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_z):
                slot = self._save_cursor + 1
                success = save_to_slot(self.game, slot)
                if success:
                    self.game.audio.play_sfx("confirm")
                    self._message = f"Game saved to slot {slot}."
                    # Refresh slot info after saving
                    self._slot_infos[self._save_cursor] = get_slot_info(slot)
                else:
                    self.game.audio.play_sfx("cancel")
                    self._message = "Save failed!"
                self._message_timer = 2.5

    def _open_equip_submenu(self, slot: str) -> None:
        """Find items in inventory matching the slot type and equip the selected one."""
        # Build list of items of this type in inventory
        candidates = [
            iid
            for iid in self.player.inventory.items
            if self._all_items.get(iid, {}).get("type") == slot
        ]
        if not candidates:
            self._message = f"No {slot} to equip."
            self._message_timer = 2.0
            return
        # Auto-equip the first candidate (Phase 3: simple equip)
        item_id = candidates[0]
        ok, msg = self.player.inventory.equip_item(item_id, self.player)
        self._message = msg
        self._message_timer = 2.5

    def _get_healing_items(self) -> Dict[str, int]:
        return self.player.inventory.healing_items()

    def update(self, dt: float) -> None:
        if self._message_timer > 0:
            self._message_timer -= dt
            if self._message_timer <= 0:
                self._message = ""

    def draw(self, surface: pygame.Surface) -> None:
        # Semi-transparent overlay
        overlay = pygame.Surface((NATIVE_WIDTH, NATIVE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 30, 200))
        surface.blit(overlay, (0, 0))

        # Outer box
        box = pygame.Rect(4, 4, NATIVE_WIDTH - 8, NATIVE_HEIGHT - 8)
        pygame.draw.rect(surface, DARK_GRAY, box)
        pygame.draw.rect(surface, LIGHT_GRAY, box, 2)

        font = pygame.font.SysFont("monospace", 8, bold=True)
        font_sm = pygame.font.SysFont("monospace", 7)

        # Title
        surface.blit(
            font.render("MENU", True, YELLOW),
            (NATIVE_WIDTH // 2 - 12, 8),
        )

        # Tab row (always visible)
        tab_x = 8
        for i, tab_name in enumerate(_TABS):
            color = YELLOW if i == self._tab_idx else WHITE
            if i == self._tab_idx:
                bg = pygame.Rect(tab_x - 2, 18, len(tab_name) * 6 + 6, 12)
                pygame.draw.rect(surface, (60, 60, 100), bg)
            surf = font_sm.render(tab_name, True, color)
            surface.blit(surf, (tab_x, 20))
            tab_x += len(tab_name) * 6 + 10

        # Divider
        pygame.draw.line(surface, LIGHT_GRAY, (8, 33), (NATIVE_WIDTH - 8, 33), 1)

        # Content area (y=37 onward)
        self._draw_content(surface, font, font_sm)

        # Focus hint
        if self._focus == "tabs":
            hint = font_sm.render(
                "Left/Right or Up/Down: select tab  Enter: open  ESC: close",
                True, (130, 130, 160),
            )
        else:
            hint = font_sm.render(
                "Up/Down: navigate  Enter: use/equip/save  ESC: back",
                True, (130, 130, 160),
            )
        surface.blit(hint, (8, NATIVE_HEIGHT - 14))

        # Status message
        if self._message:
            msg_surf = font_sm.render(self._message, True, CYAN)
            surface.blit(msg_surf, (8, NATIVE_HEIGHT - 24))

    def _draw_content(self, surface: pygame.Surface, font: pygame.font.Font, font_sm: pygame.font.Font) -> None:
        tab = _TABS[self._tab_idx]
        content_y = 38

        if tab == "Items":
            self._draw_items_tab(surface, font, font_sm, content_y)
        elif tab == "Equipment":
            self._draw_equipment_tab(surface, font, font_sm, content_y)
        elif tab == "Magic":
            self._draw_magic_tab(surface, font, font_sm, content_y)
        elif tab == "Stats":
            self._draw_stats_tab(surface, font, font_sm, content_y)
        elif tab == "Save":
            self._draw_save_tab(surface, font, font_sm, content_y)

    def _draw_items_tab(self, surface: pygame.Surface, font: pygame.font.Font, font_sm: pygame.font.Font, y: int) -> None:
        items = self._get_healing_items()
        if not items:
            surface.blit(font_sm.render("No items.", True, WHITE), (12, y))
            return

        keys = list(items.keys())
        for i, iid in enumerate(keys):
            item_data = self._all_items.get(iid, {})
            name = item_data.get("name", iid)
            qty = items[iid]
            color = YELLOW if (self._focus == "content" and i == self._items_cursor) else WHITE
            row = f"{'>' if (self._focus == 'content' and i == self._items_cursor) else ' '} {name:<18} x{qty:2d}"
            surface.blit(font_sm.render(row, True, color), (12, y + i * 10))

        # Description of highlighted item
        if self._focus == "content" and keys:
            iid = keys[self._items_cursor % len(keys)]
            desc = self._all_items.get(iid, {}).get("description", "")
            surface.blit(font_sm.render(desc, True, (160, 200, 160)), (12, NATIVE_HEIGHT - 35))

    def _draw_equipment_tab(self, surface: pygame.Surface, font: pygame.font.Font, font_sm: pygame.font.Font, y: int) -> None:
        slots = list(Inventory.SLOTS)
        for i, slot in enumerate(slots):
            equipped_id = self.player.inventory.equipped(slot)
            if equipped_id:
                item_data = self._all_items.get(equipped_id, {})
                label = item_data.get("name", equipped_id)
                # Show bonus summary
                bonuses = []
                for key, sym in (("atk", "ATK"), ("def", "DEF"), ("mdf", "MDF"), ("lck", "LCK")):
                    val = item_data.get(key, 0)
                    if val:
                        bonuses.append(f"+{val}{sym}")
                bonus_str = " ".join(bonuses) if bonuses else ""
            else:
                label = "---"
                bonus_str = ""

            color = YELLOW if (self._focus == "content" and i == self._equip_cursor) else WHITE
            prefix = ">" if (self._focus == "content" and i == self._equip_cursor) else " "
            slot_str = f"{prefix} {slot.capitalize():<10} {label:<14} {bonus_str}"
            surface.blit(font_sm.render(slot_str, True, color), (12, y + i * 11))

        if self._focus == "content":
            hint2 = font_sm.render("Enter: equip from bag  X: unequip", True, (130, 130, 160))
            surface.blit(hint2, (12, NATIVE_HEIGHT - 35))

    def _draw_magic_tab(self, surface: pygame.Surface, font: pygame.font.Font, font_sm: pygame.font.Font, y: int) -> None:
        known = self.player.known_spells
        if not known:
            surface.blit(font_sm.render("No spells known.", True, WHITE), (12, y))
            return

        for i, sid in enumerate(known):
            spell_data = self._all_spells.get(sid, {})
            name = spell_data.get("name", sid)
            mp = spell_data.get("mp", 0)
            stype = spell_data.get("type", "")
            color = YELLOW if (self._focus == "content" and i == self._magic_cursor) else WHITE
            prefix = ">" if (self._focus == "content" and i == self._magic_cursor) else " "
            row = f"{prefix} {name:<12} {mp:>3}MP  [{stype}]"
            surface.blit(font_sm.render(row, True, color), (12, y + i * 10))

        # Description of highlighted spell
        if self._focus == "content" and known:
            sid = known[self._magic_cursor % len(known)]
            desc = self._all_spells.get(sid, {}).get("description", "")
            surface.blit(font_sm.render(desc, True, (160, 200, 255)), (12, NATIVE_HEIGHT - 35))

    def _draw_stats_tab(self, surface: pygame.Surface, font: pygame.font.Font, font_sm: pygame.font.Font, y: int) -> None:
        p = self.player
        lines = [
            f"Name:  {p.name}",
            f"Level: {p.level}    EXP: {p.exp}",
            f"HP:    {p.hp}/{p.max_hp}",
            f"MP:    {p.mp}/{p.max_mp}",
            f"Gold:  {p.gold}",
            "",
            f"STR:{p.stats.get('str',0):3d}  DEF:{p.stats.get('def',0):3d}  MAG:{p.stats.get('mag',0):3d}",
            f"MDF:{p.stats.get('mdf',0):3d}  SPD:{p.stats.get('spd',0):3d}  LCK:{p.stats.get('lck',0):3d}",
        ]
        for i, line in enumerate(lines):
            surface.blit(font_sm.render(line, True, WHITE), (12, y + i * 11))

    def _draw_save_tab(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        font_sm: pygame.font.Font,
        y: int,
    ) -> None:
        """Render the five save-slot rows."""
        for i in range(NUM_SAVE_SLOTS):
            info = self._slot_infos[i] if i < len(self._slot_infos) else None
            is_selected = self._focus == "content" and i == self._save_cursor
            color = YELLOW if is_selected else WHITE
            prefix = ">" if is_selected else " "

            if info is not None:
                slot_text = (
                    f"{prefix} Slot {i + 1}  {info['name']}"
                    f"  Lv.{info['level']}"
                    f"  {info['location']}"
                    f"  {info['timestamp']}"
                )
            else:
                slot_text = f"{prefix} Slot {i + 1}  (empty)"

            surface.blit(font_sm.render(slot_text, True, color), (12, y + i * 12))

        if self._focus == "content":
            hint2 = font_sm.render(
                "Enter: save to selected slot", True, (130, 130, 160)
            )
            surface.blit(hint2, (12, NATIVE_HEIGHT - 35))
