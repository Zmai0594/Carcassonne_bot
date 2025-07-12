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
from lib.interact.tile import TileModifier
from src.helper.client_state import ClientSate
from collections import deque
from src.lib.interact.structure import StructureType
from lib.interact.tile import TileModifier

# Eack key is the tileIndex (which one it is in your hand (so either 0, 1 or 2))
# Each value in validPlacements is a tuple of the valid x and y position
validPlacements: dict[int, list[tuple[int, int]]] = {}
lastPlaced: TileModel

# key = structure and edge
# value = position of tile that exists already with said key
# use this to match our cards in hand
connectableBoardEdges: dict[tuple[StructureType, str], tuple[int, int]] = {}

def findValidPlacements(game: Game) -> None:
    cards = game.state.my_tiles
    grid = game.state.map._grid
    height = len(grid) # number of rows
    width = len(grid[0]) if height > 0 else 0


    for row in range(height):
        for col in range(width):
            tile = grid[row][col]
            if tile is None:
                # Find if empty square is a valid placement
                for tileIndex, tile in enumerate(cards):
                    # NOTE !! CAN_PLACE_TILE_AT ONLY RETURNS BOOLEAN TRUE OR FALSE. IT ALSO ROTATES THE TILE TO THE CORRECT POSITION
                    # IF THERE ARE MULTIPLE VALID PLACEMENTS, IT IS SIMPLY THE FIRST ONE CHECKED, AND MAY NOT BE OPTIMAL
                    if game.can_place_tile_at(tile, row, col):
                        if tileIndex in validPlacements:
                            validPlacements[tileIndex].append((row, col))
                        else:
                            validPlacements[tileIndex] = [(row, col)]
            else:
                # this grid location has a Tile
                externalTiles: dict[str, "Tile | None"] = tile.get_external_tiles(grid)
                for edge, externalTile in externalTiles.items():
                    if externalTile is not None:
                        continue
                   
                    # External tile does not exist, therefore "tile" is a border tile of the current board
                    if tile.placed_pos:
                        connectableBoardEdges[(tile.internal_edges[edge], edge)] = tile.placed_pos

def main():
    # Each player should have a copy of game. The game includes a Connection for you, as well as a Client state.
    game = Game()

    while True:
        query = game.get_next_query()

        findValidPlacements(game)

        def choose_move(query: QueryType) -> MoveType:
            match query:
                case QueryPlaceTile() as q:
                    return handle_place_tile(q, game)

                case QueryPlaceMeeple() as q:
                    return handle_place_meeple(q, game)

        game.send_move(choose_move(query))

def handle_place_tile(query: QueryPlaceTile, game: Game) -> MovePlaceTile:
    # for now, take first valid move from validPlacements

    #Donalds hello world!!!
    grid = game.state.map._grid
    hand = game.state.my_tiles

    firstTileIndex = next(iter(validPlacements))
    firstTile = hand[firstTileIndex]
    firstCoords = validPlacements[firstTileIndex][0]
    firstTile.placed_pos = firstCoords

    # Keep track of the last placed from OUR BOT ONLYs
    global lastPlaced
    lastPlaced = firstTile._to_model()

    optimalTile = None
    emblemCards = []
    for i, card in enumerate(hand):
        if TileModifier.EMBLEM in card.modifiers:
            emblemCards.append((i, card))

    for (type, edge), (x, y) in connectableBoardEdges.items():
        startTile = game.state.map._grid[y][x]

        if not startTile:
            continue

        # First complete anything with just 1 incomplete edge
        incompleteEdges = countIncompleteEdges(game, startTile, edge)

        if incompleteEdges == -1:
            continue

        if incompleteEdges == 1:
            # Position that we would place the tile
            emptySquarePos: tuple[int, int] | None = None
            match edge:
                case "left_edge":
                    emptySquarePos = (y, x - 1)
                case "right_edge":
                    emptySquarePos = (y, x + 1)
                case "top_edge":
                    emptySquarePos = (y - 1, x)
                case "bottom_edge":
                    emptySquarePos = (y + 1, x)

            if emptySquarePos:
                for i, card in enumerate(hand):
                    if game.can_place_tile_at(card, emptySquarePos[0], emptySquarePos[1]):
                        card.placed_pos = emptySquarePos[0], emptySquarePos[1]
                        lastPlaced = card._to_model()
                        return game.move_place_tile(query, card._to_model(), i)
        else:
            optimalTile

        
    # Then fill in priority below

    return game.move_place_tile(query, firstTile._to_model(), firstTileIndex)


    # Some basic iteration scaffold where we could calculate potential score

    # maxScore = 0
    # maxScoringIndex = 0
    # maxScoringCoords = firstCoords
    # for tileIndex in validPlacements:
    #     coords = validPlacements[tileIndex][0]

    #haha cheeky edit

# My own edits -z
    # Logic to determine highest scoring placement

# Zhitian was here

    # tileToPlace = hand[maxScoringIndex]
    # tileToPlace.placed_pos = maxScoringCoords
    # return game.move_place_tile(
    #     query, tileToPlace._to_model(), tileIndex
    # )

def countIncompleteEdges(game:Game, startTile: Tile, startEdge: str, maxIncompleteEdges:int = 2) -> int:
    '''
    is this how descriptions are made
    '''
    MAXENEMYMEEPLE = 1
    enemyMeeples = 0
    incompleteEdges = 0
    seen = set()
    desiredType = startTile.internal_edges[startEdge]
    q = deque([(startTile, startEdge)])
    structureBridge = TileModifier.get_bridge_modifier(desiredType)
    
    #they had it, idk the use case. edge given is valid but not traversable?? e.g monastary
    if startEdge not in startTile.internal_edges.keys():
        return -1
    
    while q:
        tile, edge = q.popleft()
        if (tile, edge) in seen:
            continue

        seen.add((tile, edge))
        
        meeple = tile.internal_claims[edge]
        #enemy meeple check for incoming side
        if meeple and meeple.player_id != game.state.me.player_id:
            enemyMeeples += 1
            if enemyMeeples >= MAXENEMYMEEPLE:
                return -1
        
        connectedInternalEdges = []
        #need to check adjacent edges first to be able to connect to opposite edge and keep searching
        for adjacent_edge in Tile.adjacent_edges(edge):
            if tile.internal_edges[adjacent_edge] == desiredType:
                connectedInternalEdges.append(adjacent_edge)

                #enemy meeple check for adjacent sides on same structure
                meeple = tile.internal_claims[adjacent_edge]
                if meeple and meeple.player_id != game.state.me.player_id:
                    enemyMeeples += 1
                    if enemyMeeples >= MAXENEMYMEEPLE:
                        return -1

        #no adjacent edges found but bridge exists so can do opposite side
        if (
            not connectedInternalEdges
            and structureBridge
            and structureBridge in tile.modifiers
            and tile.internal_edges[tile.get_opposite(edge)] == desiredType
        ):
            connectedInternalEdges.append(tile.get_opposite(edge))

            #enemy meeple check for valid oposite side on same structure
            meeple = tile.internal_claims[adjacent_edge]
            if meeple and meeple.player_id != game.state.me.player_id:
                enemyMeeples += 1
                if enemyMeeples >= MAXENEMYMEEPLE:
                    return -1
        

        for connectionEdge in connectedInternalEdges:
            neighbourTile = tile.get_external_tile(connectionEdge, tile.placed_pos, game.state.map._grid)
            neighbourTileEdge = tile.get_opposite(connectionEdge)
            if not neighbourTile: 
                #if edge connected to void
                incompleteEdges += 1
                if incompleteEdges >= maxIncompleteEdges:
                    return -1
                
            elif neighbourTile and (neighbourTile, neighbourTileEdge) not in seen: 
                #if edge connected to valid edge and havent seen before
                q.append((neighbourTile, neighbourTileEdge))
                pass

    return incompleteEdges


def handle_place_meeple(query: QueryPlaceTile, game: Game) -> MovePlaceMeeple | MovePlaceMeeplePass:
    # Do something
    structures = game.state.get_placeable_structures(lastPlaced)
    
    x, y = lastPlaced.pos
    tile = game.state.map._grid[y][x]

    assert tile is not None

    if structures:
        for edge, _ in structures.items():
            if game.state._get_claims(tile, edge):
                continue

            else:
                return game.move_place_meeple(query, lastPlaced, placed_on=edge)

    return game.move_place_meeple_pass(query)


if __name__ == "__main__":
    main()
