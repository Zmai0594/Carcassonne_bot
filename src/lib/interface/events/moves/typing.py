from lib.interface.events.moves.move_place_tile import MovePlaceTile, PublicMovePlaceTile
from lib.interface.events.moves.move_place_meeple import (
    MovePlaceMeeple,
    MovePlaceMeeplePass,
)

from typing import Union, TypeAlias

MoveType: TypeAlias = Union[
    MovePlaceTile,
    PublicMovePlaceTile,
    MovePlaceMeeple,
    MovePlaceMeeplePass,
]
