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
from lib.interact.tile import Tile
from src.helper.client_state import ClientSate


# Eack key is the tileIndex (which one it is in your hand (so either 0, 1 or 2))
# Each value in validPlacements is a tuple of the valid x and y position
validPlacements: dict[int, list[tuple[int, int]]] = {}

def main():
    # Each player should have a copy of game. The game includes a Connection for you, as well as a Client state.
    game = Game()
    botState = game.state
    
    
    cards = botState.my_tiles
    grid = game.state.map._grid
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0

    for tileIndex, tile in enumerate(cards):
        # (if card in validPlacements check) is outside the O(n^2) loop to save computation time
        # NOTE !! CAN_PLACE_TILE_AT ONLY RETURNS BOOLEAN TRUE OR FALSE. IT ALSO ROTATES THE TILE TO THE CORRECT POSITION
        # IF THERE ARE MULTIPLE VALID PLACEMENTS, IT IS SIMPLY THE FIRST ONE CHECKED, AND MAY NOT BE OPTIMAL
        if tileIndex in validPlacements:
            for x in range(height):
                for y in range(width):
                    if game.can_place_tile_at(tile, x, y):
                        validPlacements[tileIndex].append((x, y))
        else:
            for x in range(height):
                for y in range(width):
                    if game.can_place_tile_at(tile, x, y):
                        validPlacements[tileIndex] = [(x, y)]

    while True:
        query = game.get_next_query()

        def choose_move(query: QueryType) -> MoveType:
            match query:
                case QueryPlaceTile() as q:
                    return handle_place_tile(q, game)

                case QueryPlaceMeeple() as q:
                    return handle_place_meeple(game)

        game.send_move(choose_move(query))

def handle_place_tile(query: QueryPlaceTile, game: Game) -> MovePlaceTile:
    # for now, take first valid move from validPlacements

    hand = game.state.my_tiles

    firstTileIndex = next(iter(validPlacements))
    firstTile = hand[firstTileIndex]
    firstCoords = validPlacements[firstTileIndex][0]
    firstTile.placed_pos = firstCoords
    return game.move_place_tile(query, firstTile._to_model(), firstTileIndex)


    # Some basic iteration scaffold where we could calculate potential score

    # maxScore = 0
    # maxScoringIndex = 0
    # maxScoringCoords = firstCoords
    # for tileIndex in validPlacements:
    #     coords = validPlacements[tileIndex][0]

    # Logic to determine highest scoring placement

    # tileToPlace = hand[maxScoringIndex]
    # tileToPlace.placed_pos = maxScoringCoords
    # return game.move_place_tile(
    #     query, tileToPlace._to_model(), tileIndex
    # )


if __name__ == "__main__":
    main()
