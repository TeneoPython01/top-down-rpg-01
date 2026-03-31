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

    def play_sfx(self, name: str) -> None:
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
# Tests: zone-to-zone transition spawn (verdant_plains ↔ silverwood)
# ---------------------------------------------------------------------------

class TestZoneTransitionSpawn:
    """Confirm that zone exit data places the player adjacent to the
    corresponding zone-exit tile in the destination map.

    Key scenario from the problem statement:
      Using the verdant_plains tile on Silverwood's *south* edge (12, 19)
      must place the player at tile (12, 1) in Verdant Plains — exactly one
      tile south of the TILE_ZONE_EXIT ("silverwood tile") at (12, 0).
    """

    def test_silverwood_south_exit_targets_verdant_plains(self):
        """The south-edge zone exit of Silverwood must point to verdant_plains."""
        from src.utils.tilemap import SILVERWOOD_ZONE_EXITS
        assert (12, 19) in SILVERWOOD_ZONE_EXITS, (
            "Expected a zone exit at Silverwood (12, 19) — the south edge"
        )
        target_zone, spawn_col, spawn_row = SILVERWOOD_ZONE_EXITS[(12, 19)]
        assert target_zone == "verdant_plains", (
            f"Expected target 'verdant_plains', got '{target_zone}'"
        )

    def test_silverwood_south_exit_spawn_adjacent_to_verdant_zone_tile(self):
        """The spawn delivered by the Silverwood→Verdant transition must land
        the player exactly one tile from the TILE_ZONE_EXIT at the north edge
        of Verdant Plains (the 'silverwood tile')."""
        from settings import TILE_ZONE_EXIT
        from src.utils.tilemap import SILVERWOOD_ZONE_EXITS, get_zone_data

        _target_zone, spawn_col, spawn_row = SILVERWOOD_ZONE_EXITS[(12, 19)]

        # Build a real verdant_plains TileMap to inspect the tile IDs.
        zone_data = get_zone_data("verdant_plains")
        from src.utils.tilemap import TileMap
        tilemap = TileMap(
            data=zone_data["map"],
            spawn=zone_data["spawn"],
            town_entrances=zone_data["town_entrances"],
            zone_exits=zone_data["zone_exits"],
            dungeon_entries=zone_data["dungeon_entries"],
            hidden_walls=zone_data["hidden_walls"],
        )

        # Locate the TILE_ZONE_EXIT tile(s) at the north edge (row 0) of
        # Verdant Plains that lead back to Silverwood.
        silverwood_exit_tiles = [
            (col, row)
            for (col, row), (zone, _sc, _sr) in tilemap.zone_exits.items()
            if zone == "silverwood_forest"
        ]
        assert silverwood_exit_tiles, (
            "Verdant Plains must have a TILE_ZONE_EXIT leading back to Silverwood"
        )

        # The player should land adjacent (manhattan distance == 1) to the
        # silverwood exit tile.
        min_distance = min(
            abs(spawn_col - ec) + abs(spawn_row - er)
            for ec, er in silverwood_exit_tiles
        )
        assert min_distance == 1, (
            f"Spawn ({spawn_col},{spawn_row}) is not adjacent to any Silverwood "
            f"exit tile in Verdant Plains; nearest distance = {min_distance}"
        )

    def test_player_lands_at_spawn_col_row_after_zone_transition(self):
        """OverworldState with spawn_override=(12,1) positions the player at
        tile (12,1) — confirmed via pixel_to_tile round-trip."""
        from src.utils.tilemap import SILVERWOOD_ZONE_EXITS
        from src.entities.player import Player

        _zone, spawn_col, spawn_row = SILVERWOOD_ZONE_EXITS[(12, 19)]

        game = _MockGame()
        from src.states.overworld import OverworldState
        existing_player = Player(0, 0)
        game.player = existing_player

        # Simulate arrival: create OverworldState for the destination zone with
        # the spawn_override that _transition_zone would pass.
        state = OverworldState(
            game,
            player=existing_player,
            zone_name="verdant_plains",
            spawn_override=(spawn_col, spawn_row),
        )

        arrived_col, arrived_row = state.tilemap.pixel_to_tile(
            state.player.rect.centerx, state.player.rect.centery
        )
        assert (arrived_col, arrived_row) == (spawn_col, spawn_row), (
            f"Expected player at ({spawn_col},{spawn_row}), "
            f"got ({arrived_col},{arrived_row})"
        )

    def test_player_not_on_zone_exit_tile_after_arrival(self):
        """After arriving in Verdant Plains the player must NOT be standing on
        TILE_ZONE_EXIT — that would cause an immediate re-trigger."""
        from settings import TILE_ZONE_EXIT
        from src.utils.tilemap import SILVERWOOD_ZONE_EXITS
        from src.entities.player import Player

        _zone, spawn_col, spawn_row = SILVERWOOD_ZONE_EXITS[(12, 19)]

        game = _MockGame()
        existing_player = Player(0, 0)
        game.player = existing_player

        from src.states.overworld import OverworldState
        state = OverworldState(
            game,
            player=existing_player,
            zone_name="verdant_plains",
            spawn_override=(spawn_col, spawn_row),
        )

        arrived_col, arrived_row = state.tilemap.pixel_to_tile(
            state.player.rect.centerx, state.player.rect.centery
        )
        tile_id = state.tilemap.tile_at(arrived_col, arrived_row)
        assert tile_id != TILE_ZONE_EXIT, (
            f"Player arrived on TILE_ZONE_EXIT at ({arrived_col},{arrived_row}) "
            "— this would cause an immediate re-transition"
        )

    @pytest.mark.parametrize("from_zone,exit_tile,to_zone,spawn", [
        # Verdant Plains → Silverwood (north edge)
        ("verdant_plains",      (12, 0),  "silverwood_forest",  (12, 18)),
        # Silverwood → Verdant Plains (south edge)
        ("silverwood_forest",   (12, 19), "verdant_plains",     (12, 1)),
        # Silverwood → Stormcrag (north edge)
        ("silverwood_forest",   (12, 0),  "stormcrag_mountains",(12, 18)),
        # Stormcrag → Silverwood (south edge)
        ("stormcrag_mountains", (12, 19), "silverwood_forest",  (12, 1)),
        # Stormcrag → Dark Lands (north edge)
        ("stormcrag_mountains", (12, 0),  "dark_lands",         (12, 18)),
        # Dark Lands → Stormcrag (south edge)
        ("dark_lands",          (12, 19), "stormcrag_mountains",(12, 1)),
    ])
    def test_all_zone_exit_spawns_are_adjacent_to_exit_tile(
        self, from_zone, exit_tile, to_zone, spawn
    ):
        """Every zone exit must deliver a spawn one tile away from the
        matching exit tile in the destination zone."""
        from src.utils.tilemap import get_zone_data, TileMap
        from settings import TILE_ZONE_EXIT

        # Verify the exit data matches expectations.
        zone_data = get_zone_data(from_zone)
        actual = zone_data["zone_exits"].get(exit_tile)
        assert actual is not None, (
            f"{from_zone} has no zone exit at {exit_tile}"
        )
        actual_zone, actual_sc, actual_sr = actual
        assert actual_zone == to_zone, (
            f"Exit {exit_tile} in {from_zone}: expected target '{to_zone}', "
            f"got '{actual_zone}'"
        )
        assert (actual_sc, actual_sr) == spawn, (
            f"Exit {exit_tile} in {from_zone}: expected spawn {spawn}, "
            f"got ({actual_sc},{actual_sr})"
        )

        # Verify the spawn lands adjacent to a zone exit in the destination.
        dest_data = get_zone_data(to_zone)
        dest_map = TileMap(
            data=dest_data["map"],
            spawn=dest_data["spawn"],
            town_entrances=dest_data["town_entrances"],
            zone_exits=dest_data["zone_exits"],
            dungeon_entries=dest_data["dungeon_entries"],
            hidden_walls=dest_data["hidden_walls"],
        )
        exit_tiles_in_dest = list(dest_data["zone_exits"].keys())
        assert exit_tiles_in_dest, f"{to_zone} has no zone exits"

        min_dist = min(
            abs(spawn[0] - ec) + abs(spawn[1] - er)
            for ec, er in exit_tiles_in_dest
        )
        assert min_dist == 1, (
            f"Spawn {spawn} in {to_zone} (arriving from {from_zone}) is not "
            f"adjacent to any zone exit tile; min distance = {min_dist}"
        )


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


# ---------------------------------------------------------------------------
# Tests: hidden passage reward mechanics
# ---------------------------------------------------------------------------

class _TrackingInventory:
    """Minimal inventory that records added items and gold changes."""
    def __init__(self):
        self.gold: int = 0
        self.items: list = []

    def add(self, item_id: str, count: int = 1) -> None:
        self.items.append((item_id, count))


class _TrackingQuestFlags:
    def __init__(self):
        self._flags: dict = {}

    def get(self, key: str) -> bool:
        return self._flags.get(key, False)

    def set(self, key: str) -> None:
        self._flags[key] = True


class _TrackingGame(_MockGame):
    def __init__(self):
        super().__init__()
        self.quest_flags = _TrackingQuestFlags()
        self.inventory = _TrackingInventory()
        self._pushed_states: list = []

    def push_state(self, state) -> None:
        self._pushed_states.append(state)


def _make_overworld_tracking(zone_name: str = "verdant_plains"):
    """Create an OverworldState backed by a tracking game stub."""
    game = _TrackingGame()
    from src.states.overworld import OverworldState
    state = OverworldState(game, zone_name=zone_name)
    game.player = state.player
    return game, state


class TestHiddenPassageTiles:
    """Verify that TILE_HIDDEN tiles exist at the expected map positions."""

    @pytest.mark.parametrize("zone,col,row", [
        ("verdant_plains",      12,  6),
        ("silverwood_forest",    6,  5),
        ("stormcrag_mountains", 21,  8),
        ("dark_lands",           6, 11),
    ])
    def test_hidden_tile_present_in_map(self, zone, col, row):
        from settings import TILE_HIDDEN
        from src.utils.tilemap import get_zone_data
        zone_data = get_zone_data(zone)
        tile_id = zone_data["map"][row][col]
        assert tile_id == TILE_HIDDEN, (
            f"{zone} ({col},{row}): expected TILE_HIDDEN ({TILE_HIDDEN}), got {tile_id}"
        )

    @pytest.mark.parametrize("zone,col,row", [
        ("verdant_plains",      12,  6),
        ("silverwood_forest",    6,  5),
        ("stormcrag_mountains", 21,  8),
        ("dark_lands",           6, 11),
    ])
    def test_hidden_tile_registered_in_hidden_walls(self, zone, col, row):
        from src.utils.tilemap import get_zone_data
        zone_data = get_zone_data(zone)
        assert (col, row) in zone_data["hidden_walls"], (
            f"{zone}: ({col},{row}) not found in hidden_walls registry"
        )


class TestHiddenPassageRewards:
    """Verify the reward-passage trigger: items, gold, spells, and flag-guard."""

    def _run_trigger(self, zone: str, col: int, row: int):
        """Trigger the hidden wall at (col, row) in *zone* and return (game, state)."""
        game, state = _make_overworld_tracking(zone_name=zone)
        from src.utils.tilemap import get_zone_data
        hw_data = get_zone_data(zone)["hidden_walls"][(col, row)]
        state._trigger_hidden_wall(hw_data)
        return game, state

    @pytest.mark.parametrize("zone,col,row,expected_gold", [
        ("verdant_plains",      12,  6,  250),
        ("silverwood_forest",    6,  5,  400),
        ("stormcrag_mountains", 21,  8,  700),
        ("dark_lands",           6, 11, 2000),
    ])
    def test_gold_awarded(self, zone, col, row, expected_gold):
        game, _ = self._run_trigger(zone, col, row)
        assert game.inventory.gold == expected_gold

    @pytest.mark.parametrize("zone,col,row,expected_item", [
        ("verdant_plains",      12,  6, "iron_helm"),
        ("silverwood_forest",    6,  5, "silver_ring"),
        ("stormcrag_mountains", 21,  8, "iron_shield"),
        ("dark_lands",           6, 11, "elixir"),
    ])
    def test_items_awarded(self, zone, col, row, expected_item):
        game, _ = self._run_trigger(zone, col, row)
        item_ids = [item_id for item_id, _ in game.inventory.items]
        assert expected_item in item_ids, (
            f"{zone}: expected '{expected_item}' in awarded items {item_ids}"
        )

    @pytest.mark.parametrize("zone,col,row,expected_spell", [
        ("stormcrag_mountains", 21,  8, "dispel"),
        ("dark_lands",           6, 11, "holy"),
    ])
    def test_spell_learned(self, zone, col, row, expected_spell):
        game, state = _make_overworld_tracking(zone_name=zone)
        from src.utils.tilemap import get_zone_data
        hw_data = get_zone_data(zone)["hidden_walls"][(col, row)]
        assert expected_spell not in state.player.known_spells
        state._trigger_hidden_wall(hw_data)
        assert expected_spell in state.player.known_spells, (
            f"{zone}: spell '{expected_spell}' not in player.known_spells after trigger"
        )

    def test_flag_set_after_first_trigger(self):
        game, state = _make_overworld_tracking(zone_name="verdant_plains")
        from src.utils.tilemap import get_zone_data
        hw_data = get_zone_data("verdant_plains")["hidden_walls"][(12, 6)]
        state._trigger_hidden_wall(hw_data)
        assert game.quest_flags.get("passage_opened_verdant_secret_1")

    def test_no_duplicate_reward_on_second_trigger(self):
        game, state = _make_overworld_tracking(zone_name="verdant_plains")
        from src.utils.tilemap import get_zone_data
        hw_data = get_zone_data("verdant_plains")["hidden_walls"][(12, 6)]
        state._trigger_hidden_wall(hw_data)
        first_gold = game.inventory.gold
        state._trigger_hidden_wall(hw_data)
        assert game.inventory.gold == first_gold, (
            "Gold should not be awarded a second time for the same passage"
        )

    def test_already_known_spell_not_duplicated(self):
        game, state = _make_overworld_tracking(zone_name="stormcrag_mountains")
        state.player.known_spells.append("dispel")  # pre-learn the spell
        from src.utils.tilemap import get_zone_data
        hw_data = get_zone_data("stormcrag_mountains")["hidden_walls"][(21, 8)]
        state._trigger_hidden_wall(hw_data)
        assert state.player.known_spells.count("dispel") == 1, (
            "dispel should not be duplicated if already known"
        )

    def test_zone_transition_passage_unchanged(self):
        """The existing Subterra zone-transition passage must still work."""
        game, state = _make_overworld_tracking(zone_name="stormcrag_mountains")
        from src.utils.tilemap import get_zone_data
        hw_data = get_zone_data("stormcrag_mountains")["hidden_walls"][(8, 10)]
        # Zone-transition passages push a dialog/fade state, not a reward
        assert hw_data.get("to_zone") == "subterra_passage"
        # Trigger should not add items (it queues a zone transition instead)
        state._trigger_hidden_wall(hw_data)
        assert game.inventory.gold == 0
        assert game.inventory.items == []
