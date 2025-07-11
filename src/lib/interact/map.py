from collections import defaultdict
from lib.interact.tile import (
    Tile,
    create_base_tiles,
    create_river_tiles,
    # create_expansion_tiles,
)

from lib.config.map_config import MAP_CENTER, MAX_MAP_LENGTH


class Map:
    def __init__(self) -> None:
        self.placed_tiles: set[Tile] = set()
        self.available_tiles: set[Tile] = set()
        self.available_tiles_by_type = defaultdict(list)

        self._grid: list[list[Tile | None]] = [
            [None for _ in range(MAX_MAP_LENGTH)] for _ in range(MAX_MAP_LENGTH)
        ]
        self._grid_subscribers = []

    def start_base_phase(self) -> None:
        assert not self.available_tiles
        self.available_tiles.update(set(create_base_tiles()))

        for tile in self.available_tiles:
            self.available_tiles_by_type[tile.tile_type].append(tile)

    def start_river_phase(self) -> None:
        assert not self.available_tiles

        starting_tile = Tile.get_starting_tile()

        self._grid[MAP_CENTER[1]][MAP_CENTER[0]] = starting_tile
        self.placed_tiles.add(starting_tile)
        starting_tile.placed_pos = MAP_CENTER

        self.available_tiles.update(set(create_river_tiles()))

        for tile in self.available_tiles:
            self.available_tiles_by_type[tile.tile_type].append(tile)

    def add_expansion_pack(self, expansion_pack) -> None:
        pass

    def get_tile_by_type(self, type: str, pop: bool) -> "Tile":
        if pop:
            tile = self.available_tiles_by_type[type].pop()
            self.available_tiles.remove(tile)
            return tile

        return self.available_tiles_by_type[type][0]
