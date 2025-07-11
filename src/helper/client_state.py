from lib.config.map_config import MAX_MAP_LENGTH
from lib.interact.meeple import Meeple
from lib.interact.map import Map
from lib.interact.tile import Tile
from lib.interface.events.typing import EventType
from lib.models.player_model import PlayerModel, PublicPlayerModel
from lib.models.tile_model import TileModel
from lib.interact.structure import StructureType


class ClientSate:
    def __init__(self):
        self.round = -1
        self.players: dict[int, PublicPlayerModel]
        self.players_meeples: dict[int, int]
        self.map = Map()

        self.game_over = False
        self.num_placed_tiles = 0

        self.event_history: list["EventType"] = []
        self.new_events: int = 0
        self.turn_order: list[int] = []

        self.points = 0
        self.me: PlayerModel
        self.my_tiles: list[Tile] = []

    def get_meeples_placed_by(self, player_id: int | None) -> list[Meeple]:
        """
        Get Meeples Placed
        Giving None as player id retruns all placed meeples
        """
        meeples = []
        for x in range(MAX_MAP_LENGTH):
            for y in range(MAX_MAP_LENGTH):
                tile = self.map._grid[y][x]

                if tile is None:
                    continue

                for edge, meeple in tile.internal_claims.items():
                    if meeple and (meeple.player_id == player_id or not player_id):
                        meeples.append(meeple)

        return meeples

    def get_tile_structures(self, tile: TileModel) -> dict[str, StructureType]:
        return {
            edge: structure
            for t in self.map.available_tiles
            for edge, structure in t.internal_edges.items()
            if tile.tile_type == t.tile_type
        }

    def get_my_tile_by_type(self, tile_type: str, pop: bool) -> Tile:
        for tile in self.my_tiles:
            if tile.tile_type == tile_type:
                if pop:
                    self.my_tiles.remove(tile)
                return tile

        RuntimeError(f"No tile of type {tile_type} in hand")
