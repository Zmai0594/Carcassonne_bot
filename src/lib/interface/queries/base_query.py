from lib.interface.events.typing import DiscriminatedEvent

from typing import Mapping
from pydantic import BaseModel


class BaseQuery(BaseModel):
    query_type: str
    update: Mapping[int, DiscriminatedEvent]
