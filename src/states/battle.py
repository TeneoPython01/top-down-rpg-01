"""
src/states/battle.py - Turn-based battle state (Phase 2 & 3).
"""

from __future__ import annotations

import random
from enum import Enum, auto
from typing import TYPE_CHECKING, List, Any

import pygame

from settings import NATIVE_WIDTH, NATIVE_HEIGHT, WHITE, YELLOW, RED, BLACK, DARK_BLUE, CYAN, GREEN
import enum
import random
from typing import TYPE_CHECKING, Any, Callable, List, Optional

import pygame

from settings import (
    BLACK,
    CYAN,
    DARK_BLUE,
    DARK_GRAY,
    GREEN,
    LIGHT_GRAY,
    NATIVE_HEIGHT,
    NATIVE_WIDTH,
    RED,
    UNARMED_ATTACK_POWER,
    WHITE,
    YELLOW,
)
from src.states.base_state import BaseState
from src.systems.battle_engine import (
    check_crit,
    check_hit,
    flee_chance,
    physical_damage,
    turn_order,
)
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
class _Phase(enum.Enum):
    PLAYER_MENU = "player_menu"
    MSG = "msg"
    VICTORY = "victory"
    LEVEL_UP = "level_up"
    DEFEAT = "defeat"


class BattleState(BaseState):
    """Full turn-based battle state.

    Turn order is SPD-based (faster combatants act first).  Each round all
    combatants act once in order.  The player interacts through the command
    menu; enemies execute AI automatically.
    """

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
                    dmg *= 3
                    msgs.append("CRITICAL HIT!")
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
        self._menu = Menu(_COMMANDS, x=NATIVE_WIDTH - 72, y=NATIVE_HEIGHT - 52, item_height=10)
        self._phase = _Phase.PLAYER_MENU
        self._message = ""
        self._msg_timer = 0.0
        self._msg_callback: Optional[Callable] = None

        # Victory bookkeeping
        self._victory_xp = 0
        self._victory_gold = 0
        self._level_up_msgs: List[str] = []

        # Per-round turn queue
        self._turn_queue: List[Any] = []
        self._queue_idx = 0

        # Cached fonts (initialised lazily)
        self._font: Optional[pygame.font.Font] = None
        self._font_sm: Optional[pygame.font.Font] = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def enter(self) -> None:
        self.player._defending = False
        is_boss = any(getattr(e, "boss", False) for e in self.enemies)
        self.game.audio.play_music("boss_battle" if is_boss else "battle")
        self._show_msg("An enemy appears!", duration=1.5, callback=self._start_new_round)

    # ── Turn management ───────────────────────────────────────────────────────

    def _start_new_round(self) -> None:
        """Check end conditions, reset defend flag, then build the next turn queue."""
        alive = [e for e in self.enemies if e.is_alive()]
        if not alive:
            self._begin_victory()
            return
        if self.player.hp <= 0:
            self._begin_defeat()
            return

        self.player._defending = False
        all_combatants = [self.player] + alive
        self._turn_queue = turn_order(all_combatants)
        self._queue_idx = 0
        self._process_next_turn()

    def _process_next_turn(self) -> None:
        """Advance to the next actor in the queue; start a new round when exhausted."""
        while self._queue_idx < len(self._turn_queue):
            actor = self._turn_queue[self._queue_idx]
            self._queue_idx += 1
            if actor is self.player:
                self._phase = _Phase.PLAYER_MENU
                return
            if actor.is_alive():
                self._execute_enemy_turn(actor)
                return
            # Dead enemy — skip silently
        # All turns in this round are done
        self._start_new_round()

    def _after_action(self) -> None:
        """Common callback after any action message expires."""
        alive = [e for e in self.enemies if e.is_alive()]
        if not alive:
            self._begin_victory()
            return
        if self.player.hp <= 0:
            self._begin_defeat()
            return
        self._process_next_turn()

    # ── Player actions ────────────────────────────────────────────────────────

    def _execute_player_attack(self) -> None:
        targets = [e for e in self.enemies if e.is_alive()]
        if not targets:
            self._after_action()
            return
        target = targets[0]
        if check_hit(self.player, target):
            crit = check_crit(self.player)
            dmg = physical_damage(self.player, target, attack_power=UNARMED_ATTACK_POWER)
            if crit:
                dmg *= 3
            actual = target.take_damage(dmg)
            self.game.audio.play_sfx("attack_hit")
            msg = f"{self.player.name} attacks!  -{actual} HP"
            if crit:
                msg = "CRITICAL HIT!  " + msg
        else:
            msg = f"{self.player.name} misses!"
        self._show_msg(msg, callback=self._after_action)

    def _execute_player_defend(self) -> None:
        self.player._defending = True
        self._show_msg(f"{self.player.name} defends!", callback=self._after_action)

    def _execute_player_flee(self) -> None:
        alive = [e for e in self.enemies if e.is_alive()]
        if random.random() < flee_chance([self.player], alive):
            self._show_msg("Escaped safely!", duration=1.5, callback=self.game.pop_state)
        else:
            self._show_msg("Couldn't escape!", callback=self._after_action)

    # ── Enemy AI ──────────────────────────────────────────────────────────────

    def _execute_enemy_turn(self, enemy: Any) -> None:
        """Basic enemy AI: physical attack against the player."""
        if check_hit(enemy, self.player):
            crit = check_crit(enemy)
            dmg = physical_damage(enemy, self.player, attack_power=UNARMED_ATTACK_POWER)
            if crit:
                dmg *= 3
            if self.player._defending:
                dmg = max(1, dmg // 2)
            actual = self.player.take_damage(dmg)
            self.game.audio.play_sfx("attack_hit")
            msg = f"{enemy.name} attacks!  -{actual} HP"
            if crit:
                msg = "CRITICAL HIT!  " + msg
        else:
            msg = f"{enemy.name} misses!"
        self._show_msg(msg, callback=self._after_action)

    # ── Victory / defeat ──────────────────────────────────────────────────────

    def _begin_victory(self) -> None:
        self._victory_xp = sum(e.xp_reward for e in self.enemies)
        self._victory_gold = sum(e.gold_reward for e in self.enemies)
        self.game.inventory.gold += self._victory_gold
        self._level_up_msgs = self.player.gain_xp(self._victory_xp)
        self.game.audio.play_music("victory", loops=0)
        self._phase = _Phase.VICTORY

    def _begin_defeat(self) -> None:
        self._show_msg("Defeated...", duration=2.0, callback=self._go_to_game_over)

    def _go_to_game_over(self) -> None:
        from src.states.game_over import GameOverState
        self.game.change_state(GameOverState(self.game))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _show_msg(
        self,
        text: str,
        duration: float = 2.0,
        callback: Optional[Callable] = None,
    ) -> None:
        self._message = text
        self._msg_timer = duration
        self._msg_callback = callback
        self._phase = _Phase.MSG

    def _return_to_menu(self) -> None:
        self._phase = _Phase.PLAYER_MENU

    def _get_font(self) -> pygame.font.Font:
        if self._font is None:
            self._font = pygame.font.SysFont("monospace", 8)
        return self._font

    def _get_font_sm(self) -> pygame.font.Font:
        if self._font_sm is None:
            self._font_sm = pygame.font.SysFont("monospace", 7)
        return self._font_sm

    # ── Input ─────────────────────────────────────────────────────────────────

    def handle_input(self, event: pygame.event.Event) -> None:
        if self._phase == _Phase.PLAYER_MENU:
            result = self._menu.handle_input(event)
            if result == "Attack":
                self._execute_player_attack()
            elif result == "Defend":
                self._execute_player_defend()
            elif result == "Flee":
                self._execute_player_flee()
            elif result == "Magic":
                self._show_msg("No spells learned yet!", duration=1.5,
                               callback=self._return_to_menu)
            elif result == "Item":
                self._show_msg("No items in bag!", duration=1.5,
                               callback=self._return_to_menu)

        elif self._phase == _Phase.VICTORY:
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_z, pygame.K_SPACE
            ):
                if self._level_up_msgs:
                    self._message = self._level_up_msgs.pop(0)
                    self.game.audio.play_sfx("level_up")
                    self._phase = _Phase.LEVEL_UP
                else:
                    self.game.pop_state()

        elif self._phase == _Phase.LEVEL_UP:
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_z, pygame.K_SPACE
            ):
                if self._level_up_msgs:
                    self._message = self._level_up_msgs.pop(0)
                    self.game.audio.play_sfx("level_up")
                else:
                    self.game.pop_state()

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        if self._phase == _Phase.MSG:
            self._msg_timer -= dt
            if self._msg_timer <= 0:
                cb = self._msg_callback
                self._msg_callback = None
                self._message = ""
                if cb:
                    cb()

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(DARK_BLUE)
        font = self._get_font()
        font_sm = self._get_font_sm()

        self._draw_enemies(surface, font, font_sm)
        self._draw_player_panel(surface, font, font_sm)

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
        if self._phase == _Phase.PLAYER_MENU:
            self._menu.draw(surface)
        elif self._phase == _Phase.MSG:
            if self._message:
                self._draw_message(surface, font, self._message)
        elif self._phase == _Phase.VICTORY:
            self._draw_victory(surface, font, font_sm)
        elif self._phase == _Phase.LEVEL_UP:
            self._draw_message(surface, font, self._message)

    def _draw_enemies(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        font_sm: pygame.font.Font,
    ) -> None:
        ex = 16
        ey = 16
        for enemy in self.enemies:
            if not enemy.is_alive():
                continue
            pygame.draw.rect(surface, RED, (ex, ey, 28, 28))
            name = enemy.name if len(enemy.name) <= 10 else enemy.name[:9] + "…"
            surface.blit(font_sm.render(name, True, WHITE), (ex, ey + 30))
            hp_bar_w = 40
            hp_pct = max(0.0, enemy.hp / max(1, enemy.max_hp))
            pygame.draw.rect(surface, BLACK, (ex, ey + 39, hp_bar_w, 4))
            bar_color = RED if hp_pct < 0.25 else YELLOW if hp_pct < 0.5 else GREEN
            pygame.draw.rect(surface, bar_color, (ex, ey + 39, int(hp_bar_w * hp_pct), 4))
            ex += 56

    def _draw_player_panel(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        font_sm: pygame.font.Font,
    ) -> None:
        panel = pygame.Rect(0, NATIVE_HEIGHT - 58, NATIVE_WIDTH, 58)
        pygame.draw.rect(surface, DARK_GRAY, panel)
        pygame.draw.rect(surface, LIGHT_GRAY, panel, 1)

        py = panel.y + 6
        surface.blit(font.render(self.player.name, True, WHITE), (8, py))
        lv_text = f"Lv{self.player.level}  XP:{self.player.xp}"
        surface.blit(font_sm.render(lv_text, True, YELLOW), (8, py + 10))

        # HP bar
        hp_pct = max(0.0, self.player.hp / max(1, self.player.max_hp))
        pygame.draw.rect(surface, BLACK, (8, py + 20, 64, 5))
        hp_color = RED if hp_pct < 0.25 else YELLOW if hp_pct < 0.5 else GREEN
        pygame.draw.rect(surface, hp_color, (8, py + 20, int(64 * hp_pct), 5))
        surface.blit(
            font_sm.render(f"HP {self.player.hp}/{self.player.max_hp}", True, WHITE),
            (76, py + 19),
        )

        # MP bar
        mp_pct = max(0.0, self.player.mp / max(1, self.player.max_mp))
        pygame.draw.rect(surface, BLACK, (8, py + 27, 64, 5))
        pygame.draw.rect(surface, CYAN, (8, py + 27, int(64 * mp_pct), 5))
        surface.blit(
            font_sm.render(f"MP {self.player.mp}/{self.player.max_mp}", True, WHITE),
            (76, py + 26),
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
        # Controls hint (only when player is choosing)
        if self._phase == _Phase.PLAYER_MENU:
            hint = font_sm.render("W/S: move  Z/Enter: select", True, (150, 150, 180))
            surface.blit(hint, (8, NATIVE_HEIGHT - 8))

    def _draw_message(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        text: str,
    ) -> None:
        msg_surf = font.render(text, True, YELLOW)
        cx = NATIVE_WIDTH // 2
        cy = NATIVE_HEIGHT // 2 - 24
        bg = pygame.Rect(
            cx - msg_surf.get_width() // 2 - 4,
            cy - 3,
            msg_surf.get_width() + 8,
            msg_surf.get_height() + 6,
        )
        pygame.draw.rect(surface, DARK_GRAY, bg)
        pygame.draw.rect(surface, LIGHT_GRAY, bg, 1)
        surface.blit(msg_surf, (cx - msg_surf.get_width() // 2, cy))

    def _draw_victory(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        font_sm: pygame.font.Font,
    ) -> None:
        cx = NATIVE_WIDTH // 2
        v_surf = font.render("Victory!", True, YELLOW)
        surface.blit(v_surf, v_surf.get_rect(centerx=cx, centery=76))
        reward = f"Earned  {self._victory_xp} XP   {self._victory_gold} Gold"
        surface.blit(
            font_sm.render(reward, True, WHITE),
            font_sm.render(reward, True, WHITE).get_rect(centerx=cx, centery=92),
        )
        hint = font_sm.render("Press ENTER to continue", True, (150, 150, 180))
        surface.blit(hint, hint.get_rect(centerx=cx, centery=108))
