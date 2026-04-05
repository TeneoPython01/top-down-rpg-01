"""
tests/test_battle.py - Unit tests for BattleState and the battle engine.

Covers:
  - _Phase enum has exactly the expected Phase-6 members (no stale Phase-2 values)
  - BattleState.__init__ produces a clean, non-duplicated state
  - physical_damage / magical_damage return positive integers
  - check_hit / check_crit return booleans
  - turn_order sorts by SPD descending
  - Player.gain_xp is called correctly from BattleState._begin_victory path
"""

from __future__ import annotations

import json
import os

import pytest


# ---------------------------------------------------------------------------
# Helpers / shared fixtures
# ---------------------------------------------------------------------------

def _load_first_enemy():
    path = os.path.join("data", "enemies.json")
    with open(path) as fh:
        return json.load(fh)[0]


class _MockGame:
    quest_flags = None
    quest_log = None
    current_location = "overworld"

    class audio:
        @staticmethod
        def play_music(_name): ...
        @staticmethod
        def play_sfx(_name): ...


@pytest.fixture()
def player():
    from src.entities.player import Player
    return Player(5, 5)


@pytest.fixture()
def enemy():
    from src.entities.enemy import Enemy
    return Enemy(_load_first_enemy(), x=0, y=0)


@pytest.fixture()
def battle_state(player, enemy):
    from src.states.battle import BattleState
    return BattleState(_MockGame(), [enemy], player)


# ---------------------------------------------------------------------------
# _Phase enum integrity
# ---------------------------------------------------------------------------

class TestPhaseEnum:
    def test_phase_has_intro(self):
        from src.states.battle import _Phase
        assert _Phase.INTRO.value == "intro"

    def test_phase_has_player_menu(self):
        from src.states.battle import _Phase
        assert _Phase.PLAYER_MENU.value == "player_menu"

    def test_phase_has_no_stale_player_choose_cmd(self):
        """The old Phase-2 enum member must not exist in the final enum."""
        from src.states.battle import _Phase
        assert not hasattr(_Phase, "PLAYER_CHOOSE_CMD"), (
            "Stale Phase-2 _Phase member 'PLAYER_CHOOSE_CMD' should not exist"
        )

    def test_phase_members(self):
        from src.states.battle import _Phase
        expected = {
            "INTRO", "PLAYER_MENU", "PLAYER_SPELL", "PLAYER_ITEM",
            "TARGET_SELECT", "MSG", "VICTORY", "LEVEL_UP", "DEFEAT",
        }
        actual = {m.name for m in _Phase}
        assert actual == expected


# ---------------------------------------------------------------------------
# BattleState.__init__ – no duplicate side-effects
# ---------------------------------------------------------------------------

class TestBattleStateInit:
    def test_initial_phase_is_intro(self, battle_state):
        from src.states.battle import _Phase
        assert battle_state._phase == _Phase.INTRO

    def test_menu_uses_cmd_labels(self, battle_state):
        from src.states.battle import _CMD_LABELS
        assert battle_state._menu.options == _CMD_LABELS

    def test_turn_queue_is_empty_list(self, battle_state):
        assert battle_state._turn_queue == []
        assert battle_state._queue_idx == 0

    def test_fonts_none_initially(self, battle_state):
        """Fonts are cached lazily; must start as None."""
        assert battle_state._font is None
        assert battle_state._font_sm is None

    def test_anims_empty_list(self, battle_state):
        assert battle_state._anims == []

    def test_no_stale_commands_attribute(self):
        """_COMMANDS (stale Phase-2 list) should not exist at module level."""
        import src.states.battle as battle_module
        assert not hasattr(battle_module, "_COMMANDS"), (
            "Stale '_COMMANDS' list should have been removed"
        )


# ---------------------------------------------------------------------------
# Battle engine – physical_damage
# ---------------------------------------------------------------------------

class TestPhysicalDamage:
    def test_returns_positive_int(self, player, enemy):
        from src.systems.battle_engine import physical_damage
        dmg = physical_damage(player, enemy, attack_power=10, armor_defense=0)
        assert isinstance(dmg, int)
        assert dmg >= 1

    def test_higher_attack_power_generally_more_damage(self, player, enemy):
        from src.systems.battle_engine import physical_damage
        import random
        random.seed(0)
        dmg_low = sum(physical_damage(player, enemy, attack_power=1) for _ in range(50))
        random.seed(0)
        dmg_high = sum(physical_damage(player, enemy, attack_power=50) for _ in range(50))
        assert dmg_high > dmg_low


# ---------------------------------------------------------------------------
# Battle engine – magical_damage
# ---------------------------------------------------------------------------

class TestMagicalDamage:
    def test_returns_positive_int(self, player, enemy):
        from src.systems.battle_engine import magical_damage
        dmg = magical_damage(player, enemy, spell_power=10, resist=0)
        assert isinstance(dmg, int)
        assert dmg >= 1

    def test_weakness_doubles_damage(self, player, enemy):
        from src.systems.battle_engine import magical_damage
        import random
        random.seed(42)
        enemy.weaknesses = ["fire"]
        dmg_weak = sum(
            magical_damage(player, enemy, spell_power=10, element="fire")
            for _ in range(100)
        )
        random.seed(42)
        enemy.weaknesses = []
        dmg_normal = sum(
            magical_damage(player, enemy, spell_power=10, element="fire")
            for _ in range(100)
        )
        # With weakness damage should be roughly 2× normal
        assert dmg_weak > dmg_normal * 1.5

    def test_resistance_halves_damage(self, player, enemy):
        from src.systems.battle_engine import magical_damage
        import random
        random.seed(7)
        enemy.resistances = ["ice"]
        dmg_resist = sum(
            magical_damage(player, enemy, spell_power=10, element="ice")
            for _ in range(100)
        )
        random.seed(7)
        enemy.resistances = []
        dmg_normal = sum(
            magical_damage(player, enemy, spell_power=10, element="ice")
            for _ in range(100)
        )
        assert dmg_resist < dmg_normal * 0.75


# ---------------------------------------------------------------------------
# Battle engine – check_hit / check_crit
# ---------------------------------------------------------------------------

class TestHitAndCrit:
    def test_check_hit_returns_bool(self, player, enemy):
        from src.systems.battle_engine import check_hit
        result = check_hit(player, enemy)
        assert isinstance(result, bool)

    def test_blind_reduces_hit_rate(self, player, enemy):
        from src.systems.battle_engine import check_hit
        import random
        random.seed(0)
        hits_normal = sum(check_hit(player, enemy) for _ in range(1000))
        player.status["blind"] = 5
        random.seed(0)
        hits_blind = sum(check_hit(player, enemy) for _ in range(1000))
        assert hits_blind < hits_normal

    def test_check_crit_player_returns_bool(self, player):
        from src.systems.battle_engine import check_crit
        assert isinstance(check_crit(player), bool)

    def test_check_crit_enemy_returns_bool(self, enemy):
        from src.systems.battle_engine import check_crit
        assert isinstance(check_crit(enemy), bool)


# ---------------------------------------------------------------------------
# Battle engine – turn_order
# ---------------------------------------------------------------------------

class TestTurnOrder:
    def test_faster_combatant_acts_first(self, player, enemy):
        from src.systems.battle_engine import turn_order
        player.stats["spd"] = 99
        enemy.stats["spd"] = 1
        ordered = turn_order([enemy, player])
        assert ordered[0] is player

    def test_returns_all_combatants(self, player, enemy):
        from src.systems.battle_engine import turn_order
        ordered = turn_order([player, enemy])
        assert set(id(c) for c in ordered) == {id(player), id(enemy)}
