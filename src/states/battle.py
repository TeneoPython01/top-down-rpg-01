"""
src/states/battle.py - Turn-based battle state (Phase 2 & 3).
"""

from __future__ import annotations

import random
from enum import Enum, auto
from typing import TYPE_CHECKING, List, Any

import pygame

from settings import NATIVE_WIDTH, NATIVE_HEIGHT, WHITE, YELLOW, RED, BLACK, DARK_BLUE, CYAN, GREEN
from src.states.base_state import BaseState
from src.ui.menu import Menu
from src.systems import battle_engine, magic as magic_sys
from src.systems.inventory import load_items

if TYPE_CHECKING:
    from src.game import Game

_MSG_LINE_LEN = 50  # max characters per message display line


class _Phase(Enum):
    PLAYER_CHOOSE_CMD = auto()
    PLAYER_CHOOSE_TARGET = auto()
    PLAYER_CHOOSE_SPELL = auto()
    PLAYER_CHOOSE_ITEM = auto()
    EXECUTE_PLAYER = auto()
    ENEMY_TURN = auto()
    SHOW_MESSAGE = auto()
    VICTORY = auto()
    DEFEAT = auto()


_CMD_LABELS = ["Attack", "Magic", "Item", "Defend", "Flee"]


class BattleState(BaseState):
    """Turn-based battle scene with Attack / Magic / Item / Defend / Flee."""

    def __init__(self, game: "Game", enemies: List[Any], player: Any) -> None:
        super().__init__(game)
        self.enemies = enemies
        self.player = player

        self._cmd_menu = Menu(_CMD_LABELS, x=NATIVE_WIDTH - 70, y=NATIVE_HEIGHT - 55)

        # Spell submenu (populated in enter())
        self._spell_labels: List[str] = []
        self._spell_ids: List[str] = []
        self._spell_menu: Menu | None = None

        # Item submenu
        self._item_labels: List[str] = []
        self._item_ids: List[str] = []
        self._item_menu: Menu | None = None

        # Target selection
        self._targets: List[Any] = []
        self._target_cursor: int = 0

        self._phase = _Phase.PLAYER_CHOOSE_CMD
        self._messages: List[str] = []
        self._msg_timer = 0.0
        self._pending_action: str = ""
        self._pending_spell_id: str = ""
        self._pending_item_id: str = ""

        self._all_spells = magic_sys.load_spells()

    def enter(self) -> None:
        self._phase = _Phase.PLAYER_CHOOSE_CMD
        self._messages = ["Battle start!"]
        self._msg_timer = 1.5
        self._rebuild_spell_menu()
        self._rebuild_item_menu()

    def _rebuild_spell_menu(self) -> None:
        known = self.player.known_spells
        self._spell_ids = [sid for sid in known if sid in self._all_spells]
        self._spell_labels = [
            f"{self._all_spells[sid]['name']} ({self._all_spells[sid]['mp']}MP)"
            for sid in self._spell_ids
        ]
        if self._spell_ids:
            self._spell_menu = Menu(self._spell_labels, x=NATIVE_WIDTH - 90, y=NATIVE_HEIGHT - 55)
        else:
            self._spell_menu = None

    def _rebuild_item_menu(self) -> None:
        battle_inv = self.player.inventory.battle_items()
        all_items = load_items()
        self._item_ids = list(battle_inv.keys())
        self._item_labels = [
            f"{all_items.get(iid, {}).get('name', iid)} x{battle_inv[iid]}"
            for iid in self._item_ids
        ]
        if self._item_ids:
            self._item_menu = Menu(self._item_labels, x=NATIVE_WIDTH - 100, y=NATIVE_HEIGHT - 55)
        else:
            self._item_menu = None

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if self._phase == _Phase.SHOW_MESSAGE:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_z, pygame.K_SPACE):
                self._messages.clear()
                self._msg_timer = 0.0
                self._advance_phase_after_message()
            return

        if self._phase == _Phase.VICTORY or self._phase == _Phase.DEFEAT:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_z, pygame.K_SPACE):
                self.game.pop_state()
            return

        if self._phase == _Phase.PLAYER_CHOOSE_CMD:
            result = self._cmd_menu.handle_input(event)
            if event.key == pygame.K_ESCAPE:
                self.game.pop_state()
                return
            if result:
                self._handle_command(result)

        elif self._phase == _Phase.PLAYER_CHOOSE_TARGET:
            alive_enemies = [e for e in self.enemies if e.is_alive()]
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self._target_cursor = (self._target_cursor - 1) % max(1, len(alive_enemies))
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._target_cursor = (self._target_cursor + 1) % max(1, len(alive_enemies))
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_z):
                self._execute_player_action(alive_enemies[self._target_cursor])
            elif event.key == pygame.K_ESCAPE:
                self._phase = _Phase.PLAYER_CHOOSE_CMD

        elif self._phase == _Phase.PLAYER_CHOOSE_SPELL:
            if event.key == pygame.K_ESCAPE:
                self._phase = _Phase.PLAYER_CHOOSE_CMD
                return
            if self._spell_menu:
                result = self._spell_menu.handle_input(event)
                if result:
                    idx = self._spell_menu.selected
                    self._pending_spell_id = self._spell_ids[idx]
                    spell_data = self._all_spells[self._pending_spell_id]
                    tgt = spell_data.get("target", "enemy_single")
                    if tgt.startswith("enemy"):
                        self._phase = _Phase.PLAYER_CHOOSE_TARGET
                        self._pending_action = "spell"
                        self._target_cursor = 0
                    else:
                        # Ally-targeting spell: cast on player
                        self._execute_player_action(self.player)

        elif self._phase == _Phase.PLAYER_CHOOSE_ITEM:
            if event.key == pygame.K_ESCAPE:
                self._phase = _Phase.PLAYER_CHOOSE_CMD
                return
            if self._item_menu:
                result = self._item_menu.handle_input(event)
                if result:
                    idx = self._item_menu.selected
                    self._pending_item_id = self._item_ids[idx]
                    item_data = load_items().get(self._pending_item_id, {})
                    itype = item_data.get("type", "")
                    if itype == "battle":
                        self._phase = _Phase.PLAYER_CHOOSE_TARGET
                        self._pending_action = "item"
                        self._target_cursor = 0
                    else:
                        # Consumable: use on self
                        self._execute_player_action(self.player)

    def _handle_command(self, cmd: str) -> None:
        alive_enemies = [e for e in self.enemies if e.is_alive()]
        if cmd == "Attack":
            self._pending_action = "attack"
            self._phase = _Phase.PLAYER_CHOOSE_TARGET
            self._target_cursor = 0
        elif cmd == "Magic":
            if not self.player.known_spells:
                self._show_messages(["No spells known!"])
                return
            self._rebuild_spell_menu()
            self._phase = _Phase.PLAYER_CHOOSE_SPELL
        elif cmd == "Item":
            battle_inv = self.player.inventory.battle_items()
            if not battle_inv:
                self._show_messages(["No usable items!"])
                return
            self._rebuild_item_menu()
            self._phase = _Phase.PLAYER_CHOOSE_ITEM
        elif cmd == "Defend":
            if not hasattr(self.player, "buffs"):
                self.player.buffs = {}
            self.player.buffs["def"] = [1.5, 1]
            self._show_messages([f"{self.player.name} takes a defensive stance!"])
            self._pending_action = "defend"
            self._next_is_enemy_turn()
        elif cmd == "Flee":
            party = [self.player]
            chance = battle_engine.flee_chance(party, alive_enemies)
            if random.random() < chance:
                self._show_messages(["Escaped successfully!"])
                self._phase = _Phase.VICTORY  # repurpose Victory to pop state
            else:
                self._show_messages(["Couldn't escape!"])
                self._next_is_enemy_turn()

    def _execute_player_action(self, target: Any) -> None:
        msgs: List[str] = []

        if self._pending_action == "attack":
            if battle_engine.check_hit(self.player, target):
                is_crit = battle_engine.check_crit(self.player)
                dmg = battle_engine.physical_damage(self.player, target)
                if is_crit:
                    dmg *= 2
                    msgs.append("Critical hit!")
                actual = target.take_damage(dmg)
                msgs.append(f"{self.player.name} attacks {target.name} for {actual} damage!")
            else:
                msgs.append(f"{self.player.name}'s attack missed!")

        elif self._pending_action == "spell":
            success, msg = magic_sys.cast_spell(
                self._pending_spell_id, self.player, target, self._all_spells
            )
            msgs.append(msg)

        elif self._pending_action == "item":
            item_data = load_items().get(self._pending_item_id, {})
            if item_data.get("type") == "battle":
                success, msg = battle_engine.apply_battle_item(
                    self._pending_item_id, self.player, target
                )
                if msg == "smoke_bomb":
                    msgs.append("Escaped via Smoke Bomb!")
                    self._show_messages(msgs)
                    self._phase = _Phase.VICTORY
                    return
                msgs.append(msg)
            else:
                success, msg = self.player.inventory.use_item(self._pending_item_id, target)
                msgs.append(msg)
            self._rebuild_item_menu()

        else:
            # Direct consumable use on self
            success, msg = self.player.inventory.use_item(self._pending_item_id, self.player)
            msgs.append(msg)
            self._rebuild_item_menu()

        # Check if enemy is dead
        alive = [e for e in self.enemies if e.is_alive()]
        if not alive:
            msgs.append("All enemies defeated! Victory!")
            self._show_messages(msgs)
            self._phase = _Phase.VICTORY
            return

        self._show_messages(msgs)
        self._next_is_enemy_turn()

    def _next_is_enemy_turn(self) -> None:
        self._after_message_phase = _Phase.ENEMY_TURN

    def _advance_phase_after_message(self) -> None:
        after = getattr(self, "_after_message_phase", _Phase.PLAYER_CHOOSE_CMD)
        self._after_message_phase = _Phase.PLAYER_CHOOSE_CMD

        if after == _Phase.ENEMY_TURN:
            self._do_enemy_turns()
        elif after == _Phase.VICTORY:
            self._phase = _Phase.VICTORY
        elif after == _Phase.DEFEAT:
            self._phase = _Phase.DEFEAT
        else:
            self._phase = _Phase.PLAYER_CHOOSE_CMD

    def _do_enemy_turns(self) -> None:
        msgs: List[str] = []
        alive = [e for e in self.enemies if e.is_alive()]

        for enemy in alive:
            # Tick status effects at start of enemy's turn
            tick_msgs = magic_sys.tick_status_effects(enemy)
            msgs.extend(tick_msgs)

            if not enemy.is_alive():
                continue

            # Skip if sleeping
            if enemy.status.get("sleep", 0) > 0:
                msgs.append(f"{enemy.name} is asleep and skips their turn.")
                continue

            # Simple AI: physical attack
            if battle_engine.check_hit(enemy, self.player):
                dmg = battle_engine.physical_damage(enemy, self.player)
                actual = self.player.take_damage(dmg)
                msgs.append(f"{enemy.name} attacks for {actual} damage!")
            else:
                msgs.append(f"{enemy.name}'s attack missed!")

            if not self.player.is_alive():
                msgs.append(f"{self.player.name} has fallen!")
                self._show_messages(msgs)
                self._after_message_phase = _Phase.DEFEAT
                return

        # Tick player status effects
        player_tick = magic_sys.tick_status_effects(self.player)
        msgs.extend(player_tick)
        if not self.player.is_alive():
            msgs.append(f"{self.player.name} has fallen!")
            self._show_messages(msgs)
            self._after_message_phase = _Phase.DEFEAT
            return

        self._show_messages(msgs)
        self._after_message_phase = _Phase.PLAYER_CHOOSE_CMD

    def _show_messages(self, msgs: List[str]) -> None:
        self._messages = [m for m in msgs if m]
        self._phase = _Phase.SHOW_MESSAGE
        self._msg_timer = 0.0

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(DARK_BLUE)

        font = pygame.font.SysFont("monospace", 8)
        font_sm = pygame.font.SysFont("monospace", 7)

        # Enemy area
        alive_enemies = [e for e in self.enemies if e.is_alive()]
        selected_enemy = (
            alive_enemies[self._target_cursor % len(alive_enemies)]
            if alive_enemies and self._phase == _Phase.PLAYER_CHOOSE_TARGET
            else None
        )
        ex = 20
        for enemy in self.enemies:
            if not enemy.is_alive():
                continue
            color = YELLOW if enemy is selected_enemy else RED
            pygame.draw.rect(surface, color, (ex, 20, 32, 32))
            lbl = font_sm.render(enemy.name, True, WHITE)
            surface.blit(lbl, (ex, 56))
            hp_lbl = font_sm.render(f"HP:{enemy.hp}/{enemy.max_hp}", True, (200, 200, 200))
            surface.blit(hp_lbl, (ex, 66))
            ex += 60

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

        # Status icons
        statuses = list(getattr(self.player, "status", {}).keys())
        if statuses:
            st_surf = font_sm.render(" ".join(s.upper() for s in statuses), True, (255, 160, 0))
            surface.blit(st_surf, (6, NATIVE_HEIGHT - 40))

        # Draw phase-appropriate menu
        if self._phase == _Phase.PLAYER_CHOOSE_CMD:
            self._cmd_menu.draw(surface)
            hint = font_sm.render("Enter/Z:select  ESC:flee", True, (120, 120, 160))
            surface.blit(hint, (4, NATIVE_HEIGHT - 14))

        elif self._phase == _Phase.PLAYER_CHOOSE_SPELL:
            header = font.render("-- Magic --", True, CYAN)
            surface.blit(header, (NATIVE_WIDTH - 90, NATIVE_HEIGHT - 65))
            if self._spell_menu:
                self._spell_menu.draw(surface)
            hint = font_sm.render("ESC: back", True, (120, 120, 160))
            surface.blit(hint, (4, NATIVE_HEIGHT - 14))

        elif self._phase == _Phase.PLAYER_CHOOSE_ITEM:
            header = font.render("-- Items --", True, CYAN)
            surface.blit(header, (NATIVE_WIDTH - 100, NATIVE_HEIGHT - 65))
            if self._item_menu:
                self._item_menu.draw(surface)
            hint = font_sm.render("ESC: back", True, (120, 120, 160))
            surface.blit(hint, (4, NATIVE_HEIGHT - 14))

        elif self._phase == _Phase.PLAYER_CHOOSE_TARGET:
            hint = font.render("Choose target (←/→, Enter)", True, YELLOW)
            surface.blit(hint, (4, NATIVE_HEIGHT - 65))

        elif self._phase == _Phase.SHOW_MESSAGE:
            msg_text = "  ".join(self._messages)
            # Split into up to two lines at word boundaries where possible
            if len(msg_text) <= _MSG_LINE_LEN:
                line1, line2 = msg_text, ""
            else:
                split_at = msg_text.rfind(" ", 0, _MSG_LINE_LEN)
                if split_at == -1:
                    split_at = _MSG_LINE_LEN
                line1 = msg_text[:split_at]
                line2 = msg_text[split_at:split_at + _MSG_LINE_LEN].strip()
            msg_surf = font.render(line1, True, WHITE)
            surface.blit(msg_surf, (4, NATIVE_HEIGHT - 65))
            if line2:
                msg_surf2 = font.render(line2, True, WHITE)
                surface.blit(msg_surf2, (4, NATIVE_HEIGHT - 55))
            hint = font_sm.render("Press Enter/Z to continue", True, (150, 150, 150))
            surface.blit(hint, (4, NATIVE_HEIGHT - 14))

        elif self._phase == _Phase.VICTORY:
            v = font.render("VICTORY!  Press Enter", True, YELLOW)
            surface.blit(v, v.get_rect(centerx=NATIVE_WIDTH // 2, centery=NATIVE_HEIGHT // 2))

        elif self._phase == _Phase.DEFEAT:
            d = font.render("DEFEATED...  Press Enter", True, RED)
            surface.blit(d, d.get_rect(centerx=NATIVE_WIDTH // 2, centery=NATIVE_HEIGHT // 2))
