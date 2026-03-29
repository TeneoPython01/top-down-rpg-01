"""
src/systems/quest_log.py - Quest log system.

Quests are optional objectives that players discover by talking to NPCs,
entering new zones, or having specific flags set.  Each quest has a start
trigger, a completion flag, and a reward (gold, items, equipment, spells).
"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from settings import DATA_DIR

if TYPE_CHECKING:
    pass


# Module-level cache so quests.json is loaded only once.
_QUESTS_CACHE: Optional[Dict[str, Any]] = None


def _load_quest_data() -> Dict[str, Any]:
    global _QUESTS_CACHE
    if _QUESTS_CACHE is None:
        path = os.path.join(DATA_DIR, "quests.json")
        with open(path, encoding="utf-8") as fh:
            _QUESTS_CACHE = json.load(fh)
    return _QUESTS_CACHE


# States a quest can be in.
INACTIVE = "inactive"
ACTIVE = "active"
COMPLETE = "complete"

# Mapping dialog_id → quest_id for dialog-triggered quests.
# This is derived lazily from quests.json on first access.
_DIALOG_TRIGGERS: Optional[Dict[str, str]] = None
_ZONE_TRIGGERS: Optional[Dict[str, str]] = None
_FLAG_TRIGGERS: Optional[Dict[str, str]] = None


def _build_trigger_maps() -> None:
    global _DIALOG_TRIGGERS, _ZONE_TRIGGERS, _FLAG_TRIGGERS
    if _DIALOG_TRIGGERS is not None:
        return
    data = _load_quest_data()
    _DIALOG_TRIGGERS = {}
    _ZONE_TRIGGERS = {}
    _FLAG_TRIGGERS = {}
    for qid, qdata in data.items():
        trigger = qdata.get("start_trigger", {})
        ttype = trigger.get("type", "")
        if ttype == "dialog":
            _DIALOG_TRIGGERS[trigger["dialog_id"]] = qid
        elif ttype == "zone":
            _ZONE_TRIGGERS[trigger["zone_name"]] = qid
        elif ttype == "flag":
            _FLAG_TRIGGERS[trigger["flag"]] = qid


def get_quest_for_dialog(dialog_id: str) -> Optional[str]:
    """Return the quest_id that is started by *dialog_id*, or None."""
    _build_trigger_maps()
    assert _DIALOG_TRIGGERS is not None
    return _DIALOG_TRIGGERS.get(dialog_id)


def get_quest_for_zone(zone_name: str) -> Optional[str]:
    """Return the quest_id that is started by entering *zone_name*, or None."""
    _build_trigger_maps()
    assert _ZONE_TRIGGERS is not None
    return _ZONE_TRIGGERS.get(zone_name)


class QuestLog:
    """Tracks the state of every quest.

    All quests begin as **inactive** and must be explicitly activated by a
    trigger (NPC dialog, zone entry, or another flag being set).  Once
    activated they become **active**.  When the associated completion flag is
    set the quest transitions to **complete** and rewards are granted.

    Attributes
    ----------
    _data:
        Full quest definitions loaded from ``data/quests.json``.
    _states:
        Mapping quest_id → current state string.
    """

    def __init__(self) -> None:
        self._data: Dict[str, Any] = _load_quest_data()
        self._states: Dict[str, str] = {qid: INACTIVE for qid in self._data}

    # ── Activation ────────────────────────────────────────────────────────────

    def activate(self, quest_id: str) -> bool:
        """Activate *quest_id* if it is currently inactive.

        Returns ``True`` if the quest was newly activated, ``False`` if it was
        already active or complete (or unknown).
        """
        if quest_id not in self._data:
            return False
        if self._states.get(quest_id, INACTIVE) == INACTIVE:
            self._states[quest_id] = ACTIVE
            return True
        return False

    # ── State queries ─────────────────────────────────────────────────────────

    def is_active(self, quest_id: str) -> bool:
        return self._states.get(quest_id, INACTIVE) == ACTIVE

    def is_complete(self, quest_id: str) -> bool:
        return self._states.get(quest_id, INACTIVE) == COMPLETE

    def state_of(self, quest_id: str) -> str:
        return self._states.get(quest_id, INACTIVE)

    def get_quests_by_state(self, state: str) -> List[Tuple[str, Dict[str, Any]]]:
        """Return a list of ``(quest_id, quest_data)`` pairs for quests in
        *state* (INACTIVE / ACTIVE / COMPLETE), ordered by insertion order."""
        return [
            (qid, self._data[qid])
            for qid in self._data
            if self._states.get(qid, INACTIVE) == state
        ]

    def all_quests(self) -> List[Tuple[str, Dict[str, Any], str]]:
        """Return ``(quest_id, quest_data, state)`` for every quest."""
        return [
            (qid, self._data[qid], self._states.get(qid, INACTIVE))
            for qid in self._data
        ]

    # ── Completion / reward granting ──────────────────────────────────────────

    def check_completions(self, quest_flags: Any, player: Any, inventory: Any) -> List[str]:
        """Check all active quests for completion; grant rewards if met.

        Parameters
        ----------
        quest_flags:
            The game's :class:`~src.systems.quest_flags.QuestFlags` instance.
        player:
            The current :class:`~src.entities.player.Player` instance.
        inventory:
            The shared :class:`~src.systems.inventory.Inventory` (game.inventory).

        Returns
        -------
        list[str]
            Human-readable reward messages for each newly completed quest.
        """
        messages: List[str] = []

        # Auto-activate flag-triggered quests (e.g. "final_stand" after BK Lieutenant).
        _build_trigger_maps()
        assert _FLAG_TRIGGERS is not None
        for flag, qid in _FLAG_TRIGGERS.items():
            if quest_flags.get(flag) and self._states.get(qid, INACTIVE) == INACTIVE:
                self._states[qid] = ACTIVE

        # Complete any active quests whose completion flag is now set.
        for qid, qdata in self._data.items():
            if self._states.get(qid, INACTIVE) != ACTIVE:
                continue
            complete_flag = qdata.get("complete_flag", "")
            if complete_flag and quest_flags.get(complete_flag):
                self._states[qid] = COMPLETE
                msgs = self._grant_rewards(qdata, player, inventory)
                title = qdata.get("title", qid)
                messages.append(f'Quest complete: "{title}"!')
                messages.extend(msgs)

        return messages

    def _grant_rewards(
        self,
        qdata: Dict[str, Any],
        player: Any,
        inventory: Any,
    ) -> List[str]:
        """Apply the rewards for *qdata* and return description strings."""
        messages: List[str] = []
        reward = qdata.get("reward", {})

        gold = reward.get("gold", 0)
        if gold:
            inventory.gold += gold
            messages.append(f"  +{gold} gold")

        from src.systems.inventory import load_items
        all_items = load_items()

        for entry in reward.get("items", []):
            iid = entry.get("id", "")
            qty = entry.get("qty", 1)
            if iid:
                inventory.add(iid, qty)
                name = all_items.get(iid, {}).get("name", iid)
                messages.append(f"  +{qty}x {name}")

        for entry in reward.get("equipment", []):
            iid = entry.get("id", "")
            if iid:
                inventory.add(iid, 1)
                name = all_items.get(iid, {}).get("name", iid)
                messages.append(f"  Received: {name}")

        for spell_id in reward.get("spells", []):
            if spell_id and player is not None:
                if spell_id not in player.known_spells:
                    player.known_spells.append(spell_id)
                    from src.systems.magic import load_spells
                    all_spells = load_spells()
                    spell_name = all_spells.get(spell_id, {}).get("name", spell_id)
                    messages.append(f"  Learned: {spell_name}!")

        return messages

    # ── Serialization ─────────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, str]:
        """Return a JSON-serializable snapshot of quest states."""
        return dict(self._states)

    def from_dict(self, data: Dict[str, str]) -> None:
        """Restore quest states from a saved dict (skips unknown quest IDs)."""
        for qid, state in data.items():
            if qid in self._data and state in (INACTIVE, ACTIVE, COMPLETE):
                self._states[qid] = state
