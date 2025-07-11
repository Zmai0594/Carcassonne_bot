from lib.interface.events.base_event import BaseEvent

from typing import Literal


class EventRiverPhaseCompleted(BaseEvent):
    event_type: Literal["event_river_phase_completed"] = "event_river_phase_completed"
