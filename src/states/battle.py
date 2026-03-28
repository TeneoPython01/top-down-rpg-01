"""
src/states/battle.py - Turn-based battle state (Phase 2).
"""

from __future__ import annotations

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

if TYPE_CHECKING:
    from src.game import Game


_COMMANDS = ["Attack", "Magic", "Item", "Defend", "Flee"]


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
                dmg *= 2
            actual = target.take_damage(dmg)
            msg = f"{self.player.name} attacks!  -{actual} HP"
            if crit:
                msg = "Critical!  " + msg
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
                dmg *= 2
            if self.player._defending:
                dmg = max(1, dmg // 2)
            actual = self.player.take_damage(dmg)
            msg = f"{enemy.name} attacks!  -{actual} HP"
            if crit:
                msg = "Critical!  " + msg
        else:
            msg = f"{enemy.name} misses!"
        self._show_msg(msg, callback=self._after_action)

    # ── Victory / defeat ──────────────────────────────────────────────────────

    def _begin_victory(self) -> None:
        self._victory_xp = sum(e.xp_reward for e in self.enemies)
        self._victory_gold = sum(e.gold_reward for e in self.enemies)
        self.player.gold += self._victory_gold
        self._level_up_msgs = self.player.gain_xp(self._victory_xp)
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
                    self._phase = _Phase.LEVEL_UP
                else:
                    self.game.pop_state()

        elif self._phase == _Phase.LEVEL_UP:
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_z, pygame.K_SPACE
            ):
                if self._level_up_msgs:
                    self._message = self._level_up_msgs.pop(0)
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
