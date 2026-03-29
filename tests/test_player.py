"""
tests/test_player.py - Unit tests for the Player entity.

Covers:
  - gain_xp updates base_stats AND stats (critical regression for the
    "stats revert after equip/unequip" bug that was fixed)
  - take_damage / heal / restore_mp clamp correctly
  - serialisation round-trip (to_dict / from_dict)
  - stat regression after recalculate_stats following level-up
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def fresh_player():
    """Return a brand-new Level-1 Player at tile (5, 5)."""
    from src.entities.player import Player
    return Player(5, 5)


# ---------------------------------------------------------------------------
# take_damage
# ---------------------------------------------------------------------------

class TestTakeDamage:
    def test_normal_damage(self, fresh_player):
        p = fresh_player
        initial_hp = p.hp
        lost = p.take_damage(20)
        assert lost == 20
        assert p.hp == initial_hp - 20

    def test_overkill_clamped_to_zero(self, fresh_player):
        p = fresh_player
        lost = p.take_damage(p.hp + 9999)
        assert p.hp == 0
        assert lost == fresh_player.max_hp  # returned amount equals starting hp

    def test_zero_damage(self, fresh_player):
        p = fresh_player
        initial_hp = p.hp
        lost = p.take_damage(0)
        assert lost == 0
        assert p.hp == initial_hp


# ---------------------------------------------------------------------------
# heal
# ---------------------------------------------------------------------------

class TestHeal:
    def test_partial_heal(self, fresh_player):
        p = fresh_player
        p.take_damage(50)
        healed = p.heal(20)
        assert healed == 20

    def test_heal_capped_at_max(self, fresh_player):
        p = fresh_player
        p.take_damage(10)
        healed = p.heal(9999)
        assert p.hp == p.max_hp
        assert healed == 10

    def test_heal_at_full_hp_returns_zero(self, fresh_player):
        p = fresh_player
        assert p.hp == p.max_hp
        healed = p.heal(50)
        assert healed == 0


# ---------------------------------------------------------------------------
# restore_mp
# ---------------------------------------------------------------------------

class TestRestoreMp:
    def test_restore_mp_capped_at_max(self, fresh_player):
        p = fresh_player
        p.mp = 0
        restored = p.restore_mp(9999)
        assert p.mp == p.max_mp
        assert restored == p.max_mp


# ---------------------------------------------------------------------------
# gain_xp — critical regression test
# ---------------------------------------------------------------------------

class TestGainXp:
    def test_level_up_increments_level(self, fresh_player):
        p = fresh_player
        assert p.level == 1
        p.gain_xp(100)          # level 2 requires 100 XP per levels.json
        assert p.level == 2

    def test_gain_xp_updates_base_stats(self, fresh_player):
        """REGRESSION: gain_xp must write into base_stats, not only stats."""
        p = fresh_player
        p.gain_xp(100)
        # After levelling up to 2 the base STR should have changed.
        assert p.base_stats["str"] != 10 or p.level > 2, (
            "base_stats should be updated on level-up"
        )
        # Concrete check against levels.json level-2 values (str=12).
        assert p.base_stats["str"] == 12

    def test_stats_survive_recalculate_after_level_up(self, fresh_player):
        """REGRESSION: equip/unequip (recalculate_stats) must NOT revert stats
        to Level-1 values after the player has levelled up."""
        p = fresh_player
        p.gain_xp(100)
        level2_stats = dict(p.stats)

        # Simulate equipping/unequipping gear (calls recalculate_stats).
        p.recalculate_stats()

        for stat, value in level2_stats.items():
            assert p.stats[stat] == value, (
                f"stat '{stat}' regressed from {value} to {p.stats[stat]} "
                "after recalculate_stats()"
            )

    def test_full_hp_and_mp_restored_on_level_up(self, fresh_player):
        p = fresh_player
        p.take_damage(50)
        p.mp = 0
        p.gain_xp(100)
        assert p.hp == p.max_hp
        assert p.mp == p.max_mp

    def test_no_level_up_below_threshold(self, fresh_player):
        p = fresh_player
        p.gain_xp(50)           # 100 XP needed for level 2
        assert p.level == 1

    def test_return_value_contains_level_up_message(self, fresh_player):
        p = fresh_player
        msgs = p.gain_xp(100)
        assert len(msgs) == 1
        assert "Level up" in msgs[0]

    def test_no_message_when_no_level_up(self, fresh_player):
        msgs = fresh_player.gain_xp(10)
        assert msgs == []


# ---------------------------------------------------------------------------
# serialisation round-trip
# ---------------------------------------------------------------------------

class TestSerialization:
    def test_to_dict_and_from_dict_round_trip(self, fresh_player):
        from src.entities.player import Player
        p = fresh_player
        p.gain_xp(100)       # level up so there is something non-trivial
        p.take_damage(15)

        data = p.to_dict()
        p2 = Player.from_dict(data)

        assert p2.name == p.name
        assert p2.level == p.level
        assert p2.exp == p.exp
        assert p2.hp == p.hp
        assert p2.max_hp == p.max_hp
        assert p2.mp == p.mp
        assert p2.base_stats == p.base_stats
        assert p2.stats == p.stats

    def test_from_dict_stats_valid_after_recalculate(self, fresh_player):
        """Loaded player's stats must survive recalculate_stats without
        reverting to Level-1 values."""
        from src.entities.player import Player
        p = fresh_player
        p.gain_xp(100)

        p2 = Player.from_dict(p.to_dict())
        expected_stats = dict(p2.stats)
        p2.recalculate_stats()
        assert p2.stats == expected_stats
