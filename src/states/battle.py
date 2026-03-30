"""
src/states/battle.py - Turn-based battle state (Phase 2, 3 & 6).

Phase 6 additions
-----------------
- Battle-intro stripe effect when entering combat.
- Visual flash animations on enemy/player sprites for attacks and spells.
- Magic and Item sub-menus with full spell/consumable support.
- Cursor SFX feedback when navigating menus.
"""

from __future__ import annotations

import enum
import re
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
from src.ui.floating_text import FloatingText
from src.systems import battle_engine, magic as magic_sys
from src.systems.inventory import load_items

if TYPE_CHECKING:
    from src.game import Game

_MSG_LINE_LEN = 50  # max characters per message display line

_CMD_LABELS = ["Attack", "Magic", "Item", "Defend", "Flee"]

# Phase-6: animation colour palette per element
_ANIM_COLORS: dict = {
    "fire":          (255, 100,  30),
    "ice":           ( 80, 180, 255),
    "lightning":     (255, 240,  60),
    "wind":          (100, 220, 100),
    "holy":          (255, 255, 200),
    "dark":          (120,  20, 180),
    "non_elemental": (200, 200, 200),
    "physical":      (255, 255, 255),
}


def _parse_amount(msg: str) -> int:
    """Extract the first integer from a battle message string.

    Used to obtain the damage or heal amount from messages returned by
    ``cast_spell`` and ``apply_battle_item`` so floating numbers can be
    spawned without changing those APIs.  Returns 0 if no integer is found.
    """
    m = re.search(r"(\d+)", msg)
    return int(m.group(1)) if m else 0


class _Phase(enum.Enum):
    INTRO        = "intro"         # battle-start stripe flash
    PLAYER_MENU  = "player_menu"
    PLAYER_SPELL = "player_spell"
    PLAYER_ITEM  = "player_item"
    MSG          = "msg"
    VICTORY      = "victory"
    LEVEL_UP     = "level_up"
    DEFEAT       = "defeat"


class _Anim:
    """A short-lived visual flash drawn over a combatant sprite."""

    __slots__ = ("ex", "ey", "ew", "eh", "color", "duration", "remaining", "label")

    def __init__(
        self,
        ex: int,
        ey: int,
        ew: int,
        eh: int,
        color: tuple,
        duration: float,
        label: str = "",
    ) -> None:
        self.ex = ex
        self.ey = ey
        self.ew = ew
        self.eh = eh
        self.color = color
        self.duration = duration
        self.remaining = duration
        self.label = label

    @property
    def alpha(self) -> int:
        return max(0, int(200 * (self.remaining / max(0.001, self.duration))))


class BattleState(BaseState):
    """Full turn-based battle state.

    Turn order is SPD-based (faster combatants act first).  Each round all
    combatants act once in order.  The player interacts through the command
    menu; enemies execute AI automatically.
    """

    # Duration of the battle-intro stripe animation (seconds)
    _INTRO_DURATION = 0.55

    def __init__(
        self,
        game: "Game",
        enemies: List[Any],
        player: Any,
        victory_flags: Optional[List[str]] = None,
        on_victory: Optional[Callable] = None,
    ) -> None:
        super().__init__(game)
        self.enemies = enemies
        self.player = player
        self._victory_flags: List[str] = victory_flags or []
        self._on_victory: Optional[Callable] = on_victory

        self._menu = Menu(_CMD_LABELS, x=NATIVE_WIDTH - 72, y=NATIVE_HEIGHT - 52, item_height=10)

        # Spell submenu
        self._all_spells = magic_sys.load_spells()
        self._spell_labels: List[str] = []
        self._spell_ids: List[str] = []
        self._spell_menu: Optional[Menu] = None

        # Item submenu
        self._item_labels: List[str] = []
        self._item_ids: List[str] = []
        self._item_menu: Optional[Menu] = None

        self._phase = _Phase.INTRO
        self._intro_timer = self._INTRO_DURATION
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

        # Phase-6: active battle animations
        self._anims: List[_Anim] = []

        # Floating damage / healing numbers
        self._floating_texts: List[FloatingText] = []

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def enter(self) -> None:
        self.player._defending = False
        is_boss = any(getattr(e, "boss", False) for e in self.enemies)
        self.game.audio.play_music("boss_battle" if is_boss else "battle")
        self._phase = _Phase.INTRO
        self._intro_timer = self._INTRO_DURATION

    # ── Spell / item submenu helpers ──────────────────────────────────────────

    def _rebuild_spell_menu(self) -> None:
        known = self.player.known_spells
        self._spell_ids = [sid for sid in known if sid in self._all_spells]
        self._spell_labels = [
            f"{self._all_spells[sid]['name']} ({self._all_spells[sid]['mp']}MP)"
            for sid in self._spell_ids
        ]
        if self._spell_ids:
            self._spell_menu = Menu(
                self._spell_labels, x=NATIVE_WIDTH - 100, y=NATIVE_HEIGHT - 55
            )
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
            self._item_menu = Menu(
                self._item_labels, x=NATIVE_WIDTH - 100, y=NATIVE_HEIGHT - 55
            )
        else:
            self._item_menu = None

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
            self._fire_anim_on(target, "physical", label="SLASH")
            self._spawn_float_on_enemy(target, dmg)
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

    def _execute_player_spell(self, spell_id: str) -> None:
        """Cast a player spell then proceed to enemy turn."""
        spell_data = self._all_spells.get(spell_id, {})
        target_type = spell_data.get("target", "enemy_single")
        if target_type.startswith("enemy"):
            targets = [e for e in self.enemies if e.is_alive()]
            if not targets:
                self._after_action()
                return
            target = targets[0]
        else:
            target = self.player

        success, msg = magic_sys.cast_spell(spell_id, self.player, target, self._all_spells)
        if success:
            self.game.audio.play_sfx("spell_cast")
            element = spell_data.get("element") or "non_elemental"
            if target_type.startswith("enemy"):
                self._fire_anim_on(target, element)
                amount = _parse_amount(msg)
                if amount:
                    self._spawn_float_on_enemy(target, amount)
            else:
                self._fire_anim_on_player(element)
                amount = _parse_amount(msg)
                if amount:
                    self._spawn_float_on_player(amount, is_heal=True)
        self._show_msg(msg, callback=self._after_action)

    def _execute_player_item(self, item_id: str) -> None:
        """Use a battle item then proceed to enemy turn."""
        item_data = load_items().get(item_id, {})
        if item_data.get("type") == "battle":
            targets = [e for e in self.enemies if e.is_alive()]
            if not targets:
                self._after_action()
                return
            target = targets[0]
            success, msg = battle_engine.apply_battle_item(item_id, self.player, target)
            if msg == "smoke_bomb":
                self._show_msg(
                    "Escaped via Smoke Bomb!", duration=1.5, callback=self.game.pop_state
                )
                return
            if success:
                self.game.audio.play_sfx("item_use")
                effect = item_data.get("effect", "")
                element = (
                    "fire"      if "fire"      in effect else
                    "ice"       if "ice"       in effect else
                    "lightning" if "lightning" in effect else
                    "non_elemental"
                )
                self._fire_anim_on(target, element)
                amount = _parse_amount(msg)
                if amount:
                    self._spawn_float_on_enemy(target, amount)
        else:
            success, msg = self.player.inventory.use_item(item_id, self.player)
            if success:
                self.game.audio.play_sfx("item_use")
                self._fire_anim_on_player("non_elemental")
                amount = _parse_amount(msg)
                if amount:
                    self._spawn_float_on_player(amount, is_heal=True)
        self._rebuild_item_menu()
        self._show_msg(msg, callback=self._after_action)

    # ── Enemy AI ──────────────────────────────────────────────────────────────

    def _execute_enemy_turn(self, enemy: Any) -> None:
        """Dispatch to AI based on enemy.ai field."""
        ai = getattr(enemy, "ai", None) or getattr(enemy, "_data", {}).get("ai", "basic_attack")
        # Initialise per-enemy AI state lazily
        if not hasattr(enemy, "_ai_turn"):
            enemy._ai_turn = 0
        enemy._ai_turn += 1

        if ai == "boss_wolf":
            self._ai_boss_wolf(enemy)
        elif ai == "boss_lieutenant":
            self._ai_boss_lieutenant(enemy)
        elif ai == "boss_beast_king":
            self._ai_boss_beast_king(enemy)
        elif ai == "boss_sentinel":
            self._ai_boss_sentinel(enemy)
        elif ai == "boss_black_knight":
            self._ai_boss_black_knight(enemy)
        elif ai == "poison_attack":
            self._ai_poison_attack(enemy)
        elif ai == "status_attack":
            self._ai_status_attack(enemy)
        elif ai == "elemental_attack":
            self._ai_elemental_attack(enemy)
        elif ai == "spellcaster":
            self._ai_spellcaster(enemy)
        elif ai == "self_buff":
            self._ai_self_buff(enemy)
        else:
            self._ai_basic_attack(enemy)

    # -- Basic AI helpers -------------------------------------------------------

    def _ai_physical_hit(self, enemy: Any, power_mult: float = 1.0) -> tuple:
        """Attempt a physical attack.  Returns (hit, msg)."""
        if check_hit(enemy, self.player):
            crit = check_crit(enemy)
            dmg = physical_damage(enemy, self.player, attack_power=UNARMED_ATTACK_POWER)
            dmg = int(dmg * power_mult)
            if crit:
                dmg *= 3
            if getattr(self.player, "_defending", False):
                dmg = max(1, dmg // 2)
            actual = self.player.take_damage(dmg)
            self.game.audio.play_sfx("attack_hit")
            self._fire_anim_on_player("physical")
            self._spawn_float_on_player(dmg)
            msg = f"{enemy.name} attacks!  -{actual} HP"
            if crit:
                msg = "CRITICAL HIT!  " + msg
            return True, msg
        return False, f"{enemy.name} misses!"

    def _ai_basic_attack(self, enemy: Any) -> None:
        _, msg = self._ai_physical_hit(enemy)
        self._show_msg(msg, callback=self._after_action)

    # -- Boss AI ----------------------------------------------------------------

    def _ai_boss_wolf(self, enemy: Any) -> None:
        """Dire Wolf Alpha: multi-hit on odd turns, rallying howl on every 3rd turn."""
        turn = enemy._ai_turn
        hp_pct = enemy.hp / max(1, enemy.max_hp)

        if turn % 3 == 0:
            # Rallying howl — buffs own STR temporarily
            if not hasattr(enemy, "buffs"):
                enemy.buffs = {}
            enemy.buffs["str"] = (1.5, 2)  # 1.5× STR for 2 turns
            self._show_msg(
                f"{enemy.name} lets out a fearsome howl!  Its strength rises!",
                callback=self._after_action,
            )
            return

        # Phase 2 (< 50% HP): double hit
        if hp_pct < 0.5:
            hit1, msg1 = self._ai_physical_hit(enemy, power_mult=0.7)
            hit2, msg2 = self._ai_physical_hit(enemy, power_mult=0.7)
            combined = f"{msg1}  {msg2}"
            self._show_msg(combined, callback=self._after_action)
        else:
            self._ai_basic_attack(enemy)

    def _ai_boss_lieutenant(self, enemy: Any) -> None:
        """BK Lieutenant: alternates physical sword and dark magic attacks."""
        turn = enemy._ai_turn
        hp_pct = enemy.hp / max(1, enemy.max_hp)

        # Phase 2 (< 40% HP): prefer magic 2/3 of the time
        use_magic = (turn % 2 == 0) or (hp_pct < 0.4 and turn % 3 != 0)

        if use_magic:
            from src.systems import battle_engine as be
            dmg = int(be.magical_damage(enemy, self.player, spell_power=20))
            if getattr(self.player, "_defending", False):
                dmg = max(1, dmg // 2)
            actual = self.player.take_damage(dmg)
            self.game.audio.play_sfx("spell_cast")
            self._fire_anim_on_player("dark")
            self._spawn_float_on_player(dmg)
            msg = f"{enemy.name} unleashes Dark Slash!  -{actual} HP"
            self._show_msg(msg, callback=self._after_action)
        else:
            _, msg = self._ai_physical_hit(enemy, power_mult=1.2)
            self._show_msg(msg, callback=self._after_action)

    def _ai_boss_beast_king(self, enemy: Any) -> None:
        """Corrupted Beast King: three phases based on HP."""
        hp_pct = enemy.hp / max(1, enemy.max_hp)

        if hp_pct > 0.5:
            # Phase 1: heavy physical
            _, msg = self._ai_physical_hit(enemy, power_mult=1.5)
            self._show_msg(msg, callback=self._after_action)
        elif hp_pct > 0.25:
            # Phase 2: alternate physical / magic
            turn = enemy._ai_turn
            if turn % 2 == 0:
                from src.systems import battle_engine as be
                dmg = int(be.magical_damage(enemy, self.player, spell_power=30))
                actual = self.player.take_damage(dmg)
                self.game.audio.play_sfx("spell_cast")
                self._fire_anim_on_player("dark")
                self._spawn_float_on_player(dmg)
                self._show_msg(
                    f"{enemy.name} bellows with corrupted magic!  -{actual} HP",
                    callback=self._after_action,
                )
            else:
                _, msg = self._ai_physical_hit(enemy, power_mult=1.3)
                self._show_msg(msg, callback=self._after_action)
        else:
            # Phase 3: magic + attempt sleep status
            from src.systems import battle_engine as be
            dmg = int(be.magical_damage(enemy, self.player, spell_power=35))
            actual = self.player.take_damage(dmg)
            self.game.audio.play_sfx("spell_cast")
            self._fire_anim_on_player("dark")
            self._spawn_float_on_player(dmg)
            # Chance to inflict Sleep
            if random.random() < 0.35:
                if not hasattr(self.player, "status"):
                    self.player.status = {}
                self.player.status["sleep"] = 2
                msg = f"{enemy.name} casts Nightmare!  -{actual} HP  Player falls asleep!"
            else:
                msg = f"{enemy.name} casts Nightmare!  -{actual} HP"
            self._show_msg(msg, callback=self._after_action)

    def _ai_boss_sentinel(self, enemy: Any) -> None:
        """Crystal Sentinel: physical-only (immune to magic), high power."""
        turn = enemy._ai_turn
        if turn % 4 == 0:
            # Crystalline slam: very heavy hit
            _, msg = self._ai_physical_hit(enemy, power_mult=2.0)
            self._show_msg(f"CRYSTAL SLAM!  {msg}", callback=self._after_action)
        else:
            _, msg = self._ai_physical_hit(enemy, power_mult=1.2)
            self._show_msg(msg, callback=self._after_action)

    def _ai_boss_black_knight(self, enemy: Any) -> None:
        """The Black Knight: multi-phase, heals once at 50% HP, full spell kit."""
        hp_pct = enemy.hp / max(1, enemy.max_hp)

        # Heal once at 50% HP
        if hp_pct <= 0.5 and not getattr(enemy, "_bk_healed", False):
            enemy._bk_healed = True
            heal = min(enemy.max_hp // 3, enemy.max_hp - enemy.hp)
            enemy.hp = min(enemy.max_hp, enemy.hp + heal)
            self.game.audio.play_sfx("item_use")
            self._show_msg(
                f"{enemy.name} drinks a dark elixir!  +{heal} HP!",
                callback=self._after_action,
            )
            return

        turn = enemy._ai_turn
        action = turn % 5

        if action == 0:
            # Dark magic burst
            from src.systems import battle_engine as be
            dmg = int(be.magical_damage(enemy, self.player, spell_power=50))
            actual = self.player.take_damage(dmg)
            self.game.audio.play_sfx("spell_cast")
            self._fire_anim_on_player("dark")
            self._spawn_float_on_player(dmg)
            self._show_msg(
                f"{enemy.name} casts Void Strike!  -{actual} HP",
                callback=self._after_action,
            )
        elif action == 1:
            # Sword combo: two hits
            hit1, msg1 = self._ai_physical_hit(enemy, power_mult=0.8)
            hit2, msg2 = self._ai_physical_hit(enemy, power_mult=0.8)
            self._show_msg(f"Sword Combo!  {msg1}  {msg2}", callback=self._after_action)
        elif action == 2:
            # Dark flame
            from src.systems import battle_engine as be
            dmg = int(be.magical_damage(enemy, self.player, spell_power=40))
            actual = self.player.take_damage(dmg)
            self.game.audio.play_sfx("spell_cast")
            self._fire_anim_on_player("dark")
            self._spawn_float_on_player(dmg)
            self._show_msg(
                f"{enemy.name} unleashes Black Flame!  -{actual} HP",
                callback=self._after_action,
            )
        elif action == 3:
            # Attempt Blind
            if random.random() < 0.5:
                if not hasattr(self.player, "status"):
                    self.player.status = {}
                self.player.status["blind"] = 3
                self._show_msg(
                    f"{enemy.name} casts Shadow Shroud!  Player is Blinded!",
                    callback=self._after_action,
                )
            else:
                self._ai_basic_attack(enemy)
        else:
            _, msg = self._ai_physical_hit(enemy, power_mult=1.3)
            self._show_msg(msg, callback=self._after_action)

    # -- Elemental and status AI -----------------------------------------------

    def _ai_poison_attack(self, enemy: Any) -> None:
        """Attack and try to poison."""
        _, msg = self._ai_physical_hit(enemy)
        if random.random() < 0.4:
            if not hasattr(self.player, "status"):
                self.player.status = {}
            self.player.status["poison"] = 3
            msg += "  Player is Poisoned!"
        self._show_msg(msg, callback=self._after_action)

    def _ai_status_attack(self, enemy: Any) -> None:
        """Alternate between attack and inflicting a status."""
        turn = enemy._ai_turn
        if turn % 3 == 0:
            if not hasattr(self.player, "status"):
                self.player.status = {}
            effect = random.choice(["blind", "poison"])
            self.player.status[effect] = 2
            self._show_msg(
                f"{enemy.name} uses a Status attack!  Player is {effect.capitalize()}ed!",
                callback=self._after_action,
            )
        else:
            self._ai_basic_attack(enemy)

    def _ai_elemental_attack(self, enemy: Any) -> None:
        """Magic elemental attack."""
        from src.systems import battle_engine as be
        dmg = int(be.magical_damage(enemy, self.player, spell_power=15))
        actual = self.player.take_damage(dmg)
        self.game.audio.play_sfx("spell_cast")
        self._fire_anim_on_player("fire")
        self._spawn_float_on_player(dmg)
        self._show_msg(
            f"{enemy.name} uses an elemental attack!  -{actual} HP",
            callback=self._after_action,
        )

    def _ai_spellcaster(self, enemy: Any) -> None:
        """Random spell from the enemy's kit."""
        from src.systems import battle_engine as be
        dmg = int(be.magical_damage(enemy, self.player, spell_power=20))
        actual = self.player.take_damage(dmg)
        self.game.audio.play_sfx("spell_cast")
        self._fire_anim_on_player("non_elemental")
        self._spawn_float_on_player(dmg)
        self._show_msg(
            f"{enemy.name} casts a spell!  -{actual} HP",
            callback=self._after_action,
        )

    def _ai_self_buff(self, enemy: Any) -> None:
        """Buff self on first turn, attack on subsequent turns."""
        if enemy._ai_turn == 1:
            if not hasattr(enemy, "buffs"):
                enemy.buffs = {}
            enemy.buffs["spd"] = (2.0, 3)
            self._show_msg(
                f"{enemy.name} charges with dark energy!  Speed rises!",
                callback=self._after_action,
            )
        else:
            self._ai_basic_attack(enemy)

    # ── Victory / defeat ──────────────────────────────────────────────────────

    def _begin_victory(self) -> None:
        self._victory_xp = sum(e.xp_reward for e in self.enemies)
        self._victory_gold = sum(e.gold_reward for e in self.enemies)
        self.game.inventory.gold += self._victory_gold
        self._level_up_msgs = self.player.gain_xp(self._victory_xp)

        # Process loot drops from each enemy's loot table
        for enemy in self.enemies:
            for loot_entry in getattr(enemy, "loot_table", []):
                if random.random() < loot_entry.get("chance", 0):
                    item_id = loot_entry.get("id", "")
                    if item_id:
                        self.game.inventory.add(item_id, 1)

        # Set quest flags for this battle (e.g. boss defeated)
        for flag in self._victory_flags:
            self.game.quest_flags.set(flag)

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

    # ── Phase-6: Animation helpers ─────────────────────────────────────────────

    def _fire_anim_on(self, enemy: Any, element: str, label: str = "") -> None:
        """Queue a short visual effect flash on the given enemy sprite."""
        color = _ANIM_COLORS.get(element, (200, 200, 200))
        try:
            idx = self.enemies.index(enemy)
        except ValueError:
            idx = 0
        ex = 16 + idx * 56
        ey = 16
        self._anims.append(_Anim(ex, ey, 28, 28, color, 0.35, label=label))

    def _fire_anim_on_player(self, element: str) -> None:
        """Queue a short visual flash on the player panel strip (incoming damage)."""
        color = _ANIM_COLORS.get(element, (200, 200, 200))
        self._anims.append(_Anim(0, NATIVE_HEIGHT - 58, NATIVE_WIDTH, 8, color, 0.30))

    # ── Floating damage / heal helpers ─────────────────────────────────────────

    def _spawn_float_on_enemy(self, enemy: Any, amount: int, is_heal: bool = False) -> None:
        """Spawn a floating number above the given enemy sprite.

        *amount* should be the full (uncapped) damage value, not capped at the
        target's remaining HP.
        """
        try:
            idx = self.enemies.index(enemy)
        except ValueError:
            idx = 0
        x = float(16 + idx * 56 + 14)  # horizontal centre of the 28-px sprite
        y = float(16)                   # top of the enemy area
        text = f"+{amount}" if is_heal else f"-{amount}"
        color = (100, 255, 100) if is_heal else (255, 80, 80)
        self._floating_texts.append(FloatingText(x, y, text, color))

    def _spawn_float_on_player(self, amount: int, is_heal: bool = False) -> None:
        """Spawn a floating number above the player panel.

        *amount* should be the full (uncapped) damage value, not capped at the
        player's remaining HP.
        """
        x = float(NATIVE_WIDTH // 4)
        y = float(NATIVE_HEIGHT - 58)
        text = f"+{amount}" if is_heal else f"-{amount}"
        color = (100, 255, 100) if is_heal else (255, 80, 80)
        self._floating_texts.append(FloatingText(x, y, text, color))

    # ── Input ─────────────────────────────────────────────────────────────────

    def handle_input(self, event: pygame.event.Event) -> None:
        if self._phase == _Phase.INTRO:
            return  # no input during the intro flash

        if self._phase == _Phase.PLAYER_MENU:
            result = self._menu.handle_input(
                event,
                on_move=lambda: self.game.audio.play_sfx("cursor"),
            )
            if result == "Attack":
                self._execute_player_attack()
            elif result == "Defend":
                self._execute_player_defend()
            elif result == "Flee":
                self._execute_player_flee()
            elif result == "Magic":
                if not self.player.known_spells:
                    self._show_msg(
                        "No spells known!", duration=1.5, callback=self._return_to_menu
                    )
                else:
                    self._rebuild_spell_menu()
                    self._phase = _Phase.PLAYER_SPELL
            elif result == "Item":
                battle_inv = self.player.inventory.battle_items()
                if not battle_inv:
                    self._show_msg(
                        "No usable items!", duration=1.5, callback=self._return_to_menu
                    )
                else:
                    self._rebuild_item_menu()
                    self._phase = _Phase.PLAYER_ITEM

        elif self._phase == _Phase.PLAYER_SPELL:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._phase = _Phase.PLAYER_MENU
                return
            if self._spell_menu:
                result = self._spell_menu.handle_input(
                    event,
                    on_move=lambda: self.game.audio.play_sfx("cursor"),
                )
                if result:
                    idx = self._spell_menu.selected
                    self._execute_player_spell(self._spell_ids[idx])

        elif self._phase == _Phase.PLAYER_ITEM:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._phase = _Phase.PLAYER_MENU
                return
            if self._item_menu:
                result = self._item_menu.handle_input(
                    event,
                    on_move=lambda: self.game.audio.play_sfx("cursor"),
                )
                if result:
                    idx = self._item_menu.selected
                    self._execute_player_item(self._item_ids[idx])

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
                    if self._on_victory is not None:
                        cb = self._on_victory
                        self._on_victory = None
                        cb()

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
        # Battle-intro stripe animation
        if self._phase == _Phase.INTRO:
            self._intro_timer -= dt
            if self._intro_timer <= 0:
                self._show_msg(
                    "An enemy appears!", duration=1.5, callback=self._start_new_round
                )
            return

        if self._phase == _Phase.MSG:
            self._msg_timer -= dt
            if self._msg_timer <= 0:
                cb = self._msg_callback
                self._msg_callback = None
                self._message = ""
                if cb:
                    cb()

        # Tick active animations
        self._anims = [a for a in self._anims if a.remaining > 0]
        for a in self._anims:
            a.remaining -= dt

        # Tick floating damage / heal numbers
        self._floating_texts = [ft for ft in self._floating_texts if ft.is_alive]
        for ft in self._floating_texts:
            ft.update(dt)

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(DARK_BLUE)
        font = self._get_font()
        font_sm = self._get_font_sm()

        if self._phase == _Phase.INTRO:
            self._draw_intro(surface)
            return

        self._draw_enemies(surface, font, font_sm)
        self._draw_player_panel(surface, font, font_sm)

        # Draw floating damage / heal numbers on top of everything else
        for ft in self._floating_texts:
            ft.draw(surface, font_sm)

        if self._phase == _Phase.PLAYER_MENU:
            self._menu.draw(surface)
        elif self._phase == _Phase.MSG:
            if self._message:
                self._draw_message(surface, font, self._message)
        elif self._phase == _Phase.VICTORY:
            self._draw_victory(surface, font, font_sm)
        elif self._phase == _Phase.LEVEL_UP:
            self._draw_message(surface, font, self._message)
    # ── Draw helpers ──────────────────────────────────────────────────────────

    def _draw_intro(self, surface: pygame.Surface) -> None:
        """FF-style battle intro: horizontal stripes sweep in from both sides."""
        progress = 1.0 - (self._intro_timer / self._INTRO_DURATION)
        stripe_h = 4
        n_stripes = NATIVE_HEIGHT // stripe_h
        bright = int(220 * min(1.0, progress * 1.5))
        for i in range(n_stripes):
            y = i * stripe_h
            w = int(NATIVE_WIDTH * min(1.0, progress * 2.2))
            if i % 2 == 0:
                pygame.draw.rect(surface, (bright, bright, bright), (0, y, w, stripe_h))
            else:
                pygame.draw.rect(
                    surface, (bright, bright, bright), (NATIVE_WIDTH - w, y, w, stripe_h)
                )

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
                ex += 56
                continue
            pygame.draw.rect(surface, RED, (ex, ey, 28, 28))
            name = enemy.name if len(enemy.name) <= 10 else enemy.name[:9] + "…"
            surface.blit(font_sm.render(name, True, WHITE), (ex, ey + 30))
            hp_bar_w = 40
            hp_pct = max(0.0, enemy.hp / max(1, enemy.max_hp))
            pygame.draw.rect(surface, BLACK, (ex, ey + 39, hp_bar_w, 4))
            bar_color = RED if hp_pct < 0.25 else YELLOW if hp_pct < 0.5 else GREEN
            pygame.draw.rect(
                surface, bar_color, (ex, ey + 39, int(hp_bar_w * hp_pct), 4)
            )
            ex += 56

        # Draw enemy-side animations (those above the player panel)
        for anim in self._anims:
            if anim.ey < NATIVE_HEIGHT - 60:
                anim_surf = pygame.Surface((anim.ew, anim.eh), pygame.SRCALPHA)
                anim_surf.fill((*anim.color, anim.alpha))
                surface.blit(anim_surf, (anim.ex, anim.ey))
                if anim.label:
                    lbl = font_sm.render(anim.label, True, anim.color)
                    surface.blit(lbl, (anim.ex, anim.ey - 8))

    def _draw_player_panel(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        font_sm: pygame.font.Font,
    ) -> None:
        panel = pygame.Rect(0, NATIVE_HEIGHT - 58, NATIVE_WIDTH, 58)
        pygame.draw.rect(surface, DARK_GRAY, panel)
        pygame.draw.rect(surface, LIGHT_GRAY, panel, 1)

        # Draw player-side damage flash animations
        for anim in self._anims:
            if anim.ey >= NATIVE_HEIGHT - 60:
                anim_surf = pygame.Surface((anim.ew, anim.eh), pygame.SRCALPHA)
                anim_surf.fill((*anim.color, anim.alpha))
                surface.blit(anim_surf, (anim.ex, anim.ey))

        py = panel.y + 6
        surface.blit(font.render(self.player.name, True, WHITE), (8, py))
        lv_text = f"Lv{self.player.level}  XP:{self.player.exp}"
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
            st_surf = font_sm.render(
                " ".join(s.upper() for s in statuses), True, (255, 160, 0)
            )
            surface.blit(st_surf, (6, NATIVE_HEIGHT - 40))

        # Controls hint (only when player is choosing)
        if self._phase == _Phase.PLAYER_MENU:
            hint = font_sm.render("W/S: move  Z/Enter: select", True, (150, 150, 180))
            surface.blit(hint, (8, NATIVE_HEIGHT - 8))
        # Phase-appropriate content
        if self._phase == _Phase.PLAYER_MENU:
            self._menu.draw(surface)
            hint = font_sm.render("W/S: move  Z/Enter: select", True, (150, 150, 180))
            surface.blit(hint, (8, NATIVE_HEIGHT - 8))

        elif self._phase == _Phase.PLAYER_SPELL:
            header = font.render("-- Magic --", True, CYAN)
            surface.blit(header, (NATIVE_WIDTH - 100, NATIVE_HEIGHT - 65))
            if self._spell_menu:
                self._spell_menu.draw(surface)
            hint = font_sm.render("ESC: back", True, (120, 120, 160))
            surface.blit(hint, (4, NATIVE_HEIGHT - 14))

        elif self._phase == _Phase.PLAYER_ITEM:
            header = font.render("-- Items --", True, CYAN)
            surface.blit(header, (NATIVE_WIDTH - 100, NATIVE_HEIGHT - 65))
            if self._item_menu:
                self._item_menu.draw(surface)
            hint = font_sm.render("ESC: back", True, (120, 120, 160))
            surface.blit(hint, (4, NATIVE_HEIGHT - 14))

        elif self._phase == _Phase.MSG:
            self._draw_message(surface, font, self._message)

        elif self._phase == _Phase.VICTORY:
            self._draw_victory(surface, font, font_sm)

        elif self._phase == _Phase.LEVEL_UP:
            self._draw_message(surface, font, self._message)

        elif self._phase == _Phase.DEFEAT:
            d = font.render("DEFEATED...", True, RED)
            surface.blit(
                d, d.get_rect(centerx=NATIVE_WIDTH // 2, centery=NATIVE_HEIGHT // 2 - 20)
            )

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
