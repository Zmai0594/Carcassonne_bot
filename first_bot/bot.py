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
from enum import Enum, auto

# Eack key is the tileIndex (which one it is in your hand (so either 0, 1 or 2))
# Each value in validPlacements is a tuple of the valid x and y position
validPlacements: dict[int, list[tuple[int, int]]] = {}
lastPlaced: TileModel
immediateClaim = False
claimingEdge: str = ""
wantToClaim = False

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

    #Donalds hello world!!!
    hand = game.state.my_tiles
    # Keep track of the last placed from OUR BOT ONLYs
    global lastPlaced
    global immediateClaim
    global claimingEdge
    global wantToClaim
    immediateClaim = False
    claimingEdge = ""
    wantToClaim = False

    optimalTile = None
    optimalPos = None
    placingEmblem = False
    extendingOurs = False
    emblemCards = []

    for card in hand:
        if TileModifier.EMBLEM in card.modifiers:
            emblemCards.append(card)

    for (type, edge), (x, y) in connectableBoardEdges.items():
        startTile = game.state.map._grid[y][x]

        if not startTile:
            continue

        # First complete anything with just 1 incomplete edge
        returnDict = countIncompleteEdges(game, startTile, edge)
        incompleteEdges = returnDict[dfsEnums.INCOMPLETEEDGES]
        claims: dict[int, int] = returnDict[dfsEnums.CLAIMS] # type: ignore
        
        ours = game.state.me.player_id in claims
        unclaimed = len(claims) == 0

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

        if emptySquarePos is None:
            continue

        for i, card in enumerate(hand):
            if game.can_place_tile_at(card, emptySquarePos[0], emptySquarePos[1]):
                # Dont help others lmao
                if not ours and not unclaimed:
                    continue

                # From here, everything is either already ours or unclaimed
                # Immediately place the card if we can finish a structure THAT IS OURS OR UNCLAIMED
                if incompleteEdges == 1:
                    card.placed_pos = emptySquarePos[0], emptySquarePos[1]
                    lastPlaced = card._to_model()

                    # Set immediate claim flag to place a meeple
                    if unclaimed:
                        immediateClaim = True
                        claimingEdge = Tile.get_opposite(edge)
                    return game.move_place_tile(query, card._to_model(), i)

                # Then set priority to extending our cities with emblems
                elif card in emblemCards:
                    optimalTile = card
                    optimalPos = emptySquarePos[0], emptySquarePos[1]
                    placingEmblem = True

                    if unclaimed:
                        wantToClaim = True
                        claimingEdge = Tile.get_opposite(edge)

                # If we arent placing an emblem then focus on extending anything we have
                elif not placingEmblem:
                    if ours:
                        optimalTile = card
                        optimalPos = emptySquarePos[0], emptySquarePos[1]
                        extendingOurs = True
                    elif not extendingOurs:
                        optimalTile = card
                        optimalPos = emptySquarePos[0], emptySquarePos[1]

                        # If we havent already found a tile that is ours and the current structure is unclaimed
                        wantToClaim = True
                        claimingEdge = Tile.get_opposite(edge)

    if optimalTile:
        optimalTile.placed_pos = optimalPos
        lastPlaced = optimalTile._to_model()
        return game.move_place_tile(query, optimalTile._to_model(), hand.index(optimalTile))
    
    # Only returns here if there is no way to extend either our OWN or UNCLAIMED structures
    firstTileIndex = next(iter(validPlacements))
    firstTile = hand[firstTileIndex]
    firstCoords = validPlacements[firstTileIndex][0]
    firstTile.placed_pos = firstCoords
    return game.move_place_tile(query, firstTile._to_model(), firstTileIndex)



class dfsEnums(Enum):
    INCOMPLETEEDGES = auto()
    CURRENTPOINTS = auto()
    COMPLETEDPOINTS = auto()
    CLAIMS = auto()

#CHECK FOR ROAD CROSS SECTION MODIFIER
#QUESTION IF STRIAHGT LINE ROADS WORK
#IF HAVE ADJACENT DO CHECK OPPOSITE
def countIncompleteEdges(game:Game, startTile: Tile, startEdge: str) -> dict[dfsEnums, int | dict[int, int]]:
    '''
    is this how descriptions are made
    '''
    returnDict = {
        dfsEnums.INCOMPLETEEDGES: 0,
        dfsEnums.CURRENTPOINTS: 0, # current points of the structure
        dfsEnums.COMPLETEDPOINTS: 0, # points if structure is completed (should only be different for cities for now)
        dfsEnums.CLAIMS: {}, #player_id: number of meeples on this structure

    }
    seen = set()
    desiredType = startTile.internal_edges[startEdge]
    q = deque([(startTile, startEdge)])
    structureBridge = TileModifier.get_bridge_modifier(desiredType)
    
    #they had it, idk the use case. edge given is valid but not traversable?? e.g monastary
    if startEdge not in startTile.internal_edges.keys():
        return returnDict
    
    while q:
        tile, edge = q.popleft()
        if (tile, edge) in seen:
            continue

        seen.add((tile, edge))
        
        meeple = tile.internal_claims[edge]
        #enemy meeple check for incoming side
        if meeple:
            claimsdict = returnDict[dfsEnums.CLAIMS]
            if meeple.player_id not in claimsdict:
                claimsdict[meeple.player_id] = 0
            claimsdict[meeple.player_id] += 1
            returnDict[dfsEnums.CLAIMS] = claimsdict

        #check for broken/finished road which ends the path
        if TileModifier.BROKEN_ROAD_CENTER in tile.modifiers:
            continue

        connectedInternalEdges = []
        #need to check adjacent edges first to be able to connect to opposite edge and keep searching
        for adjacent_edge in Tile.adjacent_edges(edge):
            if tile.internal_edges[adjacent_edge] == desiredType:
                connectedInternalEdges.append(adjacent_edge)

                #enemy meeple check for adjacent sides on same structure
                meeple = tile.internal_claims[adjacent_edge]
                if meeple:
                    claimsdict = returnDict[dfsEnums.CLAIMS]
                    if meeple.player_id not in claimsdict:
                        claimsdict[meeple.player_id] = 0
                    claimsdict[meeple.player_id] += 1
                    returnDict[dfsEnums.CLAIMS] = claimsdict

        #Any of the subconditions AND the opposite edge is desired type
        if (
            
            (   #roads can go opposite. Gap in road should have been adressed above
                desiredType == StructureType.ROAD
            )
            or
            ( #no adjacent edges found but bridge exists so can do opposite side
            not connectedInternalEdges
            and structureBridge
            and structureBridge in tile.modifiers
            )
            or
            (  # is a city with a adjacent edge so opposite is valid
                desiredType == StructureType.CITY
                and connectedInternalEdges
            )
        ):
            #valid for posible opposite side, check if opposite side is valid
            if tile.internal_edges[tile.get_opposite(edge)] == desiredType: 
                connectedInternalEdges.append(tile.get_opposite(edge))

                #enemy meeple check for valid oposite side on same structure
                meeple = tile.internal_claims[tile.get_opposite(edge)]
                if meeple:
                    claimsdict = returnDict[dfsEnums.CLAIMS]
                    if meeple.player_id not in claimsdict:
                        claimsdict[meeple.player_id] = 0
                    claimsdict[meeple.player_id] += 1
                    returnDict[dfsEnums.CLAIMS] = claimsdict
        

        for connectionEdge in connectedInternalEdges:
            neighbourTile = tile.get_external_tile(connectionEdge, tile.placed_pos, game.state.map._grid)
            neighbourTileEdge = tile.get_opposite(connectionEdge)
            if not neighbourTile: 
                #if edge connected to void
                returnDict[dfsEnums.INCOMPLETEEDGES] += 1
                
            elif neighbourTile and (neighbourTile, neighbourTileEdge) not in seen: 
                #if edge connected to valid edge and havent seen before
                q.append((neighbourTile, neighbourTileEdge))

    return returnDict


def handle_place_meeple(query: QueryPlaceTile, game: Game) -> MovePlaceMeeple | MovePlaceMeeplePass:
    # Do something
    structures = game.state.get_placeable_structures(lastPlaced)
    
    x, y = lastPlaced.pos
    tile = game.state.map._grid[y][x]

    assert tile is not None

    if immediateClaim:
        return game.move_place_meeple(query, lastPlaced, claimingEdge)
    
    if game.state.me.num_meeples < 2:
        return game.move_place_meeple_pass(query)
    
    if wantToClaim:
        return game.move_place_meeple(query, lastPlaced, claimingEdge)
    

    # TODO superflous?
    # if we have more than 1 meeple then place on first valid spot
    if structures:
        for edge, _ in structures.items():
            if game.state._get_claims(tile, edge):
                continue

            return game.move_place_meeple(query, lastPlaced, placed_on=edge)

    return game.move_place_meeple_pass(query)


if __name__ == "__main__":
    main()
