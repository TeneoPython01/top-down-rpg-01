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
from src.systems.quest_log import ACTIVE, COMPLETE
from src.systems.save_load import get_slot_info, save_to_slot
from src.entities.player import _get_levels_data

if TYPE_CHECKING:
    from src.game import Game


_BASE_TABS = ["Items", "Equipment", "Magic", "Stats", "Quests", "Save", "Options"]
_CHEAT_LABEL = "Cheats"

# Konami code: ↑ ↑ ↓ ↓ ← → ← →  (enter while viewing the Quests tab)
_KONAMI = [
    pygame.K_UP, pygame.K_UP,
    pygame.K_DOWN, pygame.K_DOWN,
    pygame.K_LEFT, pygame.K_RIGHT,
    pygame.K_LEFT, pygame.K_RIGHT,
]

# Cheat definitions: (button label, description shown at bottom)
_CHEATS = [
    ("Give 100,000 Gold",  "Adds 100,000 gold to your wallet."),
    ("Max Level (Lv 30)",  "Jumps level and stats to Lv 30 if currently below Lv 30."),
    ("Endgame Equipment",  "Adds and equips the Exo Weapon and Exo Armor."),
    ("Learn All Spells",   "Teaches every spell in the game."),
    ("Toggle Always-Crit", "Every player attack becomes a critical hit (toggle ON/OFF)."),
]

# Pixel width of one character in the small monospace font (7pt).
_CHAR_W = 6


class PauseMenuState(BaseState):
    """Out-of-battle pause menu with tabs: Items, Equipment, Magic, Stats, Save."""

    is_overlay = True

    def __init__(self, game: "Game", player: Any) -> None:
        super().__init__(game)
        self.player = player
        self._tab_idx = 0
        self._tab_menu = Menu(list(_BASE_TABS), x=8, y=20, item_height=14)

        # Per-tab cursors
        self._items_cursor = 0
        self._equip_cursor = 0
        self._magic_cursor = 0
        self._quests_cursor = 0
        self._save_cursor = 0
        self._cheat_cursor = 0

        self._message = ""
        self._message_timer = 0.0

        self._all_items: Dict[str, Any] = {}
        self._all_spells: Dict[str, Any] = {}
        self._slot_infos: List[Any] = []

        # Which pane has focus: "tabs" or "content"
        self._focus = "tabs"

        # Cheat-mode state (persisted on the player object between menu opens)
        self._cheat_unlocked: bool = getattr(player, "cheat_unlocked", False)
        self._konami_progress: int = 0
        if self._cheat_unlocked:
            self._tab_menu.options = self._tabs

    # ── Dynamic tab list ──────────────────────────────────────────────────────

    @property
    def _tabs(self) -> List[str]:
        """Return the active tab list, including 'Cheats' once unlocked."""
        if self._cheat_unlocked:
            return _BASE_TABS + [_CHEAT_LABEL]
        return list(_BASE_TABS)

    def enter(self) -> None:
        self._all_items = load_items()
        self._all_spells = load_spells()
        self._message = ""
        self._message_timer = 0.0
        self._focus = "tabs"
        self._slot_infos = [get_slot_info(i) for i in range(1, NUM_SAVE_SLOTS + 1)]
        # Sync cheat-unlock state from the persistent player flag
        self._cheat_unlocked = getattr(self.player, "cheat_unlocked", False)
        if self._cheat_unlocked:
            self._tab_menu.options = self._tabs

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        # ── Konami code: ↑↑↓↓←→←→ while viewing the Quests tab ────────────
        if not self._cheat_unlocked and self._tabs[self._tab_idx] == "Quests":
            if event.key == _KONAMI[self._konami_progress]:
                self._konami_progress += 1
                if self._konami_progress == len(_KONAMI):
                    # Sequence complete — unlock the Cheats tab
                    self._cheat_unlocked = True
                    self.player.cheat_unlocked = True
                    self._konami_progress = 0
                    self._tab_menu.options = self._tabs
                    self._tab_idx = self._tabs.index(_CHEAT_LABEL)
                    self._tab_menu._cursor = self._tab_idx
                    self._focus = "tabs"
                    self._message = "\u2605 CHEAT MODE ENABLED \u2605"
                    self._message_timer = 3.0
                    self.game.audio.play_sfx("confirm")
                    return  # consume this key press
            else:
                self._konami_progress = 0

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
                self._tab_idx = (self._tab_idx - 1) % len(self._tabs)
                self._tab_menu._cursor = self._tab_idx
                self.game.audio.play_sfx("cursor")
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._tab_idx = (self._tab_idx + 1) % len(self._tabs)
                self._tab_menu._cursor = self._tab_idx
                self.game.audio.play_sfx("cursor")
            else:
                result = self._tab_menu.handle_input(event, on_move=lambda: self.game.audio.play_sfx("cursor"))
                self._tab_idx = self._tab_menu.selected
                if result:
                    self.game.audio.play_sfx("confirm")
                    # Options tab launches the dedicated OptionsState overlay
                    if self._tabs[self._tab_idx] == "Options":
                        from src.states.options import OptionsState
                        self.game.push_state(OptionsState(self.game))
                    else:
                        self._focus = "content"
                        self._items_cursor = 0
                        self._equip_cursor = 0
                        self._magic_cursor = 0
                        self._quests_cursor = 0
                        self._save_cursor = 0
                        self._cheat_cursor = 0
        else:
            self._handle_content_input(event)

    def _handle_content_input(self, event: pygame.event.Event) -> None:
        tab = self._tabs[self._tab_idx]

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

        elif tab == "Quests":
            quest_entries = self._get_quest_entries()
            if not quest_entries:
                return
            if event.key in (pygame.K_UP, pygame.K_w):
                self._quests_cursor = (self._quests_cursor - 1) % len(quest_entries)
                self.game.audio.play_sfx("cursor")
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._quests_cursor = (self._quests_cursor + 1) % len(quest_entries)
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

        elif tab == "Cheats":
            if event.key in (pygame.K_UP, pygame.K_w):
                self._cheat_cursor = (self._cheat_cursor - 1) % len(_CHEATS)
                self.game.audio.play_sfx("cursor")
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._cheat_cursor = (self._cheat_cursor + 1) % len(_CHEATS)
                self.game.audio.play_sfx("cursor")
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_z):
                self._activate_cheat(self._cheat_cursor)

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

    def _activate_cheat(self, index: int) -> None:
        """Execute cheat *index* and show a feedback message."""
        p = self.player
        if index == 0:
            # Cheat 1: Give 100,000 gold
            p.inventory.gold += 100_000
            self._message = "Received 100,000 gold!"
            self.game.audio.play_sfx("confirm")

        elif index == 1:
            # Cheat 2: Set level and stats to Lv 30 (if below Lv 30)
            if p.level >= 30:
                self._message = "Already at Lv 30 or higher."
                self._message_timer = 2.5
                return
            levels_data = _get_levels_data()
            lv30 = next((e for e in levels_data if e["level"] == 30), None)
            if lv30:
                p.level = 30
                p.exp = lv30["xp_required"]
                p.max_hp = lv30["hp"]
                p.hp = p.max_hp
                p.max_mp = lv30["mp"]
                p.mp = p.max_mp
                for stat in ("str", "def", "mag", "mdf", "spd", "lck"):
                    p.base_stats[stat] = lv30[stat]
                p.recalculate_stats()
                # Learn all spells that would have been gained by level 30
                for sid, sdata in self._all_spells.items():
                    if sdata.get("learn_level", 99) <= 30 and sid not in p.known_spells:
                        p.known_spells.append(sid)
                self._message = "Jumped to Lv 30 with full stats!"
            self.game.audio.play_sfx("confirm")

        elif index == 2:
            # Cheat 3: Give and equip endgame equipment
            for item_id in ("exo_weapon", "exo_armor"):
                if not p.inventory.has(item_id):
                    p.inventory.add(item_id, 1)
                p.inventory.equip_item(item_id, p)
            self._message = "Equipped Exo Weapon and Exo Armor!"
            self.game.audio.play_sfx("confirm")

        elif index == 3:
            # Cheat 4: Learn all spells
            added = 0
            for sid in self._all_spells:
                if sid not in p.known_spells:
                    p.known_spells.append(sid)
                    added += 1
            if added:
                self._message = f"Learned {added} new spell(s)!"
            else:
                self._message = "All spells already known."
            self.game.audio.play_sfx("confirm")

        elif index == 4:
            # Cheat 5: Toggle always-crit
            p.always_crit = not p.always_crit
            state = "ON" if p.always_crit else "OFF"
            self._message = f"Always-Crit: {state}"
            self.game.audio.play_sfx("confirm")

        self._message_timer = 2.5

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
        for i, tab_name in enumerate(self._tabs):
            color = YELLOW if i == self._tab_idx else WHITE
            if i == self._tab_idx:
                bg = pygame.Rect(tab_x - 2, 18, len(tab_name) * _CHAR_W + _CHAR_W, 12)
                pygame.draw.rect(surface, (60, 60, 100), bg)
            surf = font_sm.render(tab_name, True, color)
            surface.blit(surf, (tab_x, 20))
            tab_x += len(tab_name) * _CHAR_W + 10

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
        tab = self._tabs[self._tab_idx]
        content_y = 38

        if tab == "Items":
            self._draw_items_tab(surface, font, font_sm, content_y)
        elif tab == "Equipment":
            self._draw_equipment_tab(surface, font, font_sm, content_y)
        elif tab == "Magic":
            self._draw_magic_tab(surface, font, font_sm, content_y)
        elif tab == "Stats":
            self._draw_stats_tab(surface, font, font_sm, content_y)
        elif tab == "Quests":
            self._draw_quests_tab(surface, font, font_sm, content_y)
        elif tab == "Save":
            self._draw_save_tab(surface, font, font_sm, content_y)
        elif tab == "Cheats":
            self._draw_cheats_tab(surface, font, font_sm, content_y)
        elif tab == "Options":
            hint = font_sm.render("Press Enter / Z to open Options", True, LIGHT_GRAY)
            surface.blit(hint, hint.get_rect(centerx=NATIVE_WIDTH // 2, centery=content_y + 20))

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

    def _get_quest_entries(self) -> List[tuple]:
        """Return a list of (quest_id, quest_data, state) for active and complete quests."""
        return [
            (qid, qdata, state)
            for qid, qdata, state in self.game.quest_log.all_quests()
            if state in (ACTIVE, COMPLETE)
        ]

    def _draw_quests_tab(self, surface: pygame.Surface, font: pygame.font.Font, font_sm: pygame.font.Font, y: int) -> None:
        quest_entries = self._get_quest_entries()
        if not quest_entries:
            surface.blit(font_sm.render("No quests discovered yet.", True, WHITE), (12, y))
            return

        for i, (qid, qdata, state) in enumerate(quest_entries):
            title = qdata.get("title", qid)
            status_color = GREEN if state == COMPLETE else YELLOW
            status_str = "[DONE]" if state == COMPLETE else "[ACTIVE]"
            is_selected = self._focus == "content" and i == self._quests_cursor
            prefix = ">" if is_selected else " "
            row_color = YELLOW if is_selected else WHITE
            row = f"{prefix} {title:<22} {status_str}"
            surface.blit(font_sm.render(row, True, row_color), (12, y + i * 11))
            # Draw the status badge in its own color
            badge_x = 12 + (len(prefix) + 1 + 22 + 1) * _CHAR_W
            surface.blit(font_sm.render(status_str, True, status_color), (badge_x, y + i * 11))

        # Show objective/description of highlighted quest
        if self._focus == "content" and quest_entries:
            idx = self._quests_cursor % len(quest_entries)
            _, qdata, state = quest_entries[idx]
            objective = qdata.get("objective", qdata.get("description", ""))
            if objective:
                surface.blit(font_sm.render(objective, True, (200, 200, 160)), (12, NATIVE_HEIGHT - 35))

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

    def _draw_cheats_tab(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        font_sm: pygame.font.Font,
        y: int,
    ) -> None:
        """Render the cheat list with cursor and bottom description."""
        surface.blit(font_sm.render("\u2605 CHEAT MODE \u2605", True, RED), (12, y))
        y += 14

        for i, (label, _desc) in enumerate(_CHEATS):
            is_sel = self._focus == "content" and i == self._cheat_cursor
            color = YELLOW if is_sel else WHITE
            prefix = ">" if is_sel else " "
            if i == 4:
                # Always-Crit shows live ON/OFF state
                toggle = "[ON] " if self.player.always_crit else "[OFF]"
                row = f"{prefix} {label}  {toggle}"
            else:
                row = f"{prefix} {label}"
            surface.blit(font_sm.render(row, True, color), (12, y + i * 12))

        if self._focus == "content":
            _, desc = _CHEATS[self._cheat_cursor]
            surface.blit(font_sm.render(desc, True, (200, 160, 200)), (12, NATIVE_HEIGHT - 35))
