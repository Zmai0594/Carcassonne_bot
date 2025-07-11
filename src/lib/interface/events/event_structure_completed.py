from warnings import deprecated
from lib.interact.tile import Tile
from lib.interface.events.base_event import BaseEvent

from typing import Literal


@deprecated
class EventStructureCompleted(BaseEvent):
    event_type: Literal["event_structure_completed"] = "event_structure_completed"
    rewarded_players: list[int]
    reward: int
    triggering_tile: Tile
    triggering_player_id: int
