"""
tests/test_map_transitions.py - Tests for map-transition spawn behaviour.

Covers the fix for: "when leaving a town the player should appear just
outside the town entrance, not at the overworld's default spawn."
"""

from __future__ import annotations

import pytest

from settings import TILE_SIZE, PLAYER_SIZE


# ---------------------------------------------------------------------------
# Minimal game stub — enough for OverworldState.__init__ to succeed without
# a real pygame window or file I/O that is unavailable in headless CI.
# ---------------------------------------------------------------------------

class _QuestFlags:
    def get(self, key: str) -> bool:
        return False

    def set(self, key: str) -> None:
        pass


class _QuestLog:
    def activate(self, quest_id: str) -> bool:
        return False

    def check_completions(self, *args):
        return []


class _Audio:
    def play_music(self, name: str) -> None:
        pass


class _Inventory:
    gold: int = 0


class _MockGame:
    def __init__(self) -> None:
        self.player = None
        self.quest_flags = _QuestFlags()
        self.quest_log = _QuestLog()
        self.audio = _Audio()
        self.inventory = _Inventory()
        self.current_location = ""

    def push_state(self, state) -> None:
        pass

    def pop_state(self) -> None:
        pass

    def change_state(self, state) -> None:
        pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_overworld(zone_name: str = "verdant_plains"):
    """Create an OverworldState without pushing it onto a real state stack."""
    game = _MockGame()
    from src.states.overworld import OverworldState
    state = OverworldState(game, zone_name=zone_name)
    return game, state


def _place_player_at_tile(state, game, col: int, row: int) -> None:
    """Reposition the player in *state* to the given tile coordinates."""
    from src.entities.player import Player
    _margin = (TILE_SIZE - PLAYER_SIZE) // 2
    player = Player(col, row)
    player.pos.x = col * TILE_SIZE + _margin
    player.pos.y = row * TILE_SIZE + _margin
    player.rect.topleft = (round(player.pos.x), round(player.pos.y))
    state.player = player
    game.player = player


# ---------------------------------------------------------------------------
# Tests: town-exit spawn
# ---------------------------------------------------------------------------

class TestTownExitSpawn:
    """Player must land just outside the town entrance when exiting a town."""

    @pytest.mark.parametrize("town_col,town_row,zone", [
        (22, 3, "verdant_plains"),     # Ironhaven entrance
        (22, 9, "verdant_plains"),     # Ashenvale entrance
        (18, 9, "silverwood_forest"),  # Willowmere entrance
        (9,  2, "subterra_passage"),   # Subterra town entrance
    ])
    def test_player_near_entrance_after_exit(self, town_col, town_row, zone):
        """After returning from a town the player should be within one tile
        of the town entrance tile."""
        game, state = _make_overworld(zone_name=zone)
        _place_player_at_tile(state, game, town_col, town_row)

        # Record which tile we entered from (done in update() normally).
        state._return_tile = (town_col, town_row)

        # Simulate the TownState being popped: OverworldState.enter() is called.
        state.enter()

        # The player should now be adjacent to (town_col, town_row).
        col_after, row_after = state.tilemap.pixel_to_tile(
            state.player.rect.centerx, state.player.rect.centery
        )
        manhattan = abs(col_after - town_col) + abs(row_after - town_row)
        assert manhattan == 1, (
            f"[{zone}] Player at ({col_after},{row_after}) after exiting town at "
            f"({town_col},{town_row}); expected distance 1, got {manhattan}"
        )

    @pytest.mark.parametrize("town_col,town_row,zone", [
        (22, 3, "verdant_plains"),
        (22, 9, "verdant_plains"),
    ])
    def test_player_not_at_default_spawn_after_exit(self, town_col, town_row, zone):
        """Player must NOT land at the zone's default spawn after exiting a town."""
        from src.utils.tilemap import get_zone_data
        game, state = _make_overworld(zone_name=zone)
        default_spawn_col, default_spawn_row = get_zone_data(zone)["spawn"]

        _place_player_at_tile(state, game, town_col, town_row)
        state._return_tile = (town_col, town_row)
        state.enter()

        col_after, row_after = state.tilemap.pixel_to_tile(
            state.player.rect.centerx, state.player.rect.centery
        )
        assert (col_after, row_after) != (default_spawn_col, default_spawn_row), (
            "Player landed at the default spawn instead of near the town entrance"
        )

    def test_return_tile_cleared_after_enter(self):
        """_return_tile must be None after enter() so a subsequent dialog-close
        does not re-trigger repositioning."""
        game, state = _make_overworld()
        _place_player_at_tile(state, game, 22, 3)
        state._return_tile = (22, 3)
        state.enter()
        assert state._return_tile is None

    def test_no_reposition_when_return_tile_not_set(self):
        """When _return_tile is None, enter() must not move the player."""
        game, state = _make_overworld()
        _place_player_at_tile(state, game, 4, 9)
        expected_x = state.player.pos.x
        expected_y = state.player.pos.y

        state._return_tile = None  # no town exit pending
        state.enter()

        assert state.player.pos.x == expected_x
        assert state.player.pos.y == expected_y


# ---------------------------------------------------------------------------
# Tests: _place_player_outside_tile unit test
# ---------------------------------------------------------------------------

class TestPlacePlayerOutsideTile:
    """Direct unit tests for the _place_player_outside_tile helper."""

    def test_lands_on_walkable_adjacent_tile(self):
        """The player should end up on a non-blocked tile one step away."""
        from settings import TILE_WALL, TILE_WATER, TILE_TOWN
        game, state = _make_overworld(zone_name="verdant_plains")
        _place_player_at_tile(state, game, 22, 3)

        state._place_player_outside_tile(22, 3)

        col, row = state.tilemap.pixel_to_tile(
            state.player.rect.centerx, state.player.rect.centery
        )
        tile = state.tilemap.tile_at(col, row)
        assert tile not in (TILE_WALL, TILE_WATER, TILE_TOWN), (
            f"Player placed on blocked tile {tile} at ({col},{row})"
        )
        manhattan = abs(col - 22) + abs(row - 3)
        assert manhattan == 1
