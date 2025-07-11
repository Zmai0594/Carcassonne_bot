from lib.models.tile_model import TileModel
from lib.interface.events.base_event import BaseEvent

from typing import Literal


class EventMeeplePlaced(BaseEvent):
    event_type: Literal["event_meeple_placed"] = "event_meeple_placed"
    player_id: int
    tile: TileModel
    edge: str
