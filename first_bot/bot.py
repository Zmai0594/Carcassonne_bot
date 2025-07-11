from helper.game import Game
from lib.interface.events.moves.move_place_meeple import (
    MovePlaceMeeple,
    MovePlaceMeeplePass,
)
from lib.interface.events.moves.move_place_tile import MovePlaceTile
from lib.interface.queries.typing import QueryType
from lib.interface.queries.query_place_tile import QueryPlaceTile
from lib.interface.queries.query_place_meeple import QueryPlaceMeeple
from lib.interface.events.moves.typing import MoveType
from lib.models.tile_model import TileModel
from src.helper.client_state import ClientSate


def main():
    game = Game()
    botState = ClientSate()
    
    validPlacements = {}
    cards = botState.my_tiles
    grid = game.state.map._grid
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0

    for card in cards:
        # (if card in validPlacements check) is outside the O(n^2) loop to save computation time
        if card in validPlacements:
            for x in range(height):
                for y in range(width):
                    if game.can_place_tile_at(card, x, y):
                        validPlacements[card].append((x, y))
        else:
            for x in range(height):
                for y in range(width):
                    if game.can_place_tile_at(card, x, y):
                        validPlacements[card] = [(x, y)]

    while True:
        query = game.get_next_query()

        def choose_move(query: QueryType) -> MoveType:
            match query:
                case QueryPlaceTile() as q:
                    return handle_place_tile(game, botState, q)

                case QueryPlaceMeeple() as q:
                    return handle_place_meeple(game, botState, q)

        game.send_move(choose_move(query))

if __name__ == "__main__":
    main()
