from lib.interface.events.moves.move_place_meeple import (
    MovePlaceMeeple,
    MovePlaceMeeplePass,
)
from helper.game import Game
from lib.interface.events.moves.move_place_tile import MovePlaceTile
from lib.interface.queries.typing import QueryType
from lib.interface.queries.query_place_tile import QueryPlaceTile
from lib.interface.queries.query_place_meeple import QueryPlaceMeeple
from lib.interface.events.moves.typing import MoveType
from lib.models.tile_model import TileModel
from lib.interact.tile import Tile
from lib.interact.tile import TileModifier
from helper.client_state import ClientSate
from collections import deque
from lib.interact.structure import StructureType
from lib.interact.tile import TileModifier
from enum import Enum, auto
from lib.config.map_config import MAX_MAP_LENGTH, MAP_CENTER
MAXROWINDEX= MAX_MAP_LENGTH - 1
MAXCOLINDEX = MAX_MAP_LENGTH - 1

# Eack key is the tileIndex (which one it is in your hand (so either 0, 1 or 2))
# Each value in validPlacements is a tuple of the valid x and y position
validPlacements: dict[int, list[tuple[int, int]]] = {}
lastPlaced: TileModel
lastPlacedTile: Tile
immediateClaim: bool = False
claimingEdge: str = ""
wantToClaim: bool = False

# key = structure and edge
# value = position of tile that exists already with said key
# use this to match our cards in hand
connectableBoardEdges: dict[tuple[StructureType, str], set[tuple[int, int]]] = {}


def findValidPlacements(game: Game) -> None:
    cards = game.state.my_tiles
    grid = game.state.map._grid

    four_latest:list[Tile] = game.state.map.placed_tiles[-4:]
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    need_to_check:set[Tile] = set()


    for t in four_latest:
        if not t:
            continue
        need_to_check.add(t)
        # Valid Placements
        for direction in directions:
            x = t.placed_pos[0] + direction[0]
            y = t.placed_pos[1] + direction[1]
            tile = grid[y][x]
            if tile is None:
                # Find if empty square is a valid placement
                for tileIndex, tile in enumerate(cards):
                    # NOTE !! CAN_PLACE_TILE_AT ONLY RETURNS BOOLEAN TRUE OR FALSE. IT ALSO ROTATES THE TILE TO THE CORRECT POSITION
                    # IF THERE ARE MULTIPLE VALID PLACEMENTS, IT IS SIMPLY THE FIRST ONE CHECKED, AND MAY NOT BE OPTIMAL
                    if game.can_place_tile_at(tile, x, y):
                        if tileIndex in validPlacements:
                            validPlacements[tileIndex].append((x, y))
                        else:
                            validPlacements[tileIndex] = [(x, y)]
            else:
                # Add the tile to need_to check if it exists -> updating the external edges
                need_to_check.add(tile)

    print("valid placements concluded", flush=True)

    # External Edges
    for t in need_to_check:
        if not t:
            continue
        for edge, struct in t.internal_edges.items():
            if t.get_external_tile(edge, t.placed_pos, grid) is None:
                if (struct, edge) not in connectableBoardEdges:
                    connectableBoardEdges[(struct, edge)] = set()
                connectableBoardEdges[(struct, edge)].add(t.placed_pos)
                print("tile", t.tile_type, "has", struct, "at", edge)
            elif (struct, edge) in connectableBoardEdges:
                print("deleting", (struct, edge), "at", t.placed_pos)
                connectableBoardEdges[(struct, edge)].discard(t.placed_pos)
                if len(connectableBoardEdges[(struct, edge)]) == 0:
                    del connectableBoardEdges[(struct, edge)]
        print("\n----------------", flush=True)
        print("connectableBoardEdges for each tile to be checked", flush=True)
        print(connectableBoardEdges, flush=True)
        print("---------------\n", flush=True)
    print("\n----------------", flush=True)
    print("connectable board edge after all tiles checked???", flush=True)
    print(connectableBoardEdges, flush=True)
    print("---------------\n", flush=True)


def main():
    game = Game()
    print("bot started")
    while True:
        print("waiting for query")
        query = game.get_next_query()
        print("got query", query, flush=True)
        findValidPlacements(game)
        print("hereeee", flush=True)

        def choose_move(query: QueryType) -> MoveType:
            match query:
                case QueryPlaceTile() as q:
                    return handle_place_tile(q, game)

                case QueryPlaceMeeple() as q:
                    return handle_place_meeple(q, game)

        game.send_move(choose_move(query))

def handle_place_tile(query: QueryPlaceTile, game: Game) -> MovePlaceTile:
    print("handle place tile called", flush=True)
    #Donalds hello world!!!
    hand = game.state.my_tiles
    # Keep track of the last placed from OUR BOT ONLYs
    global lastPlaced
    global immediateClaim
    global claimingEdge
    global wantToClaim
    global lastPlacedTile
    immediateClaim = False
    claimingEdge = ""
    wantToClaim = False
    riverTurn:bool = False

    optimalTile:Tile | None = None
    optimalPos:tuple[int, int] | None = None
    placingEmblem:bool = False
    extendingOurs:bool = False
    emblemCards:list[Tile] = []

    
    latest_tile:Tile = game.state.map.placed_tiles[-1]
    latest_pos:tuple[int, int] | None = latest_tile.placed_pos

    print("hand length", len(hand), flush=True)
    for card in hand:
        print("exampling card", card.tile_type, "with modifiers", card.modifiers, flush=True)
        if TileModifier.EMBLEM in card.modifiers:
            print("card has emblem", flush=True)
            emblemCards.append(card)
        
        for edge in card.get_edges():
            if card.internal_edges[edge] == StructureType.RIVER:
                riverTurn = True
                print("card has river at", edge, flush=True)
                print("properly set here on edge", edge, flush=True)
                for e in latest_tile.get_edges():
                    if latest_tile.internal_edges[e] == StructureType.RIVER:
                        print("latest tile at", latest_pos, "has river at", e, ":", latest_tile.tile_type, flush=True)
    
    print()
    print("latest tile of type ", latest_tile.tile_type, "has edges:", flush=True)
    for e in latest_tile.get_edges():
        print(e, latest_tile.internal_edges[e])
    print()

            
    for (structType, edge), positions in connectableBoardEdges.items():
        for (x, y) in positions:
            if riverTurn and structType != StructureType.RIVER:
                continue

            startTile = game.state.map._grid[y][x]

            if not startTile:
                continue

            # First complete anything with just 1 incomplete edge
            returnDict = countIncompleteEdges(game, startTile, edge)
            incompleteEdges = returnDict[dfsEnums.INCOMPLETEEDGES]
            claims: dict[int, int] = returnDict[dfsEnums.CLAIMS] # type: ignore
            
            print("\n\nIncomplete Edges from tile:", startTile.tile_type, "at", (x, y), "is", incompleteEdges, structType, "\n\n")
            ours:bool = game.state.me.player_id in claims
            unclaimed:bool = len(claims) == 0

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
                print("empty pos is None, think this might be a problem. skipping to next possible edge", edge, flush=True)
                continue
            print("empty square pos is", emptySquarePos[1], emptySquarePos[0], "for edge", edge, flush=True)

            print("\ncurrently examining:", edge, "at position", x, y, flush=True)
            print("hand is", hand, len(hand), flush=True)
            for i, card in enumerate(hand):
                if game.can_place_tile_at(card, emptySquarePos[1], emptySquarePos[0]):
                    # Dont help others lmao
                    if not ours and not unclaimed:
                        print("curr card is", card.tile_type)
                        continue

                    if riverTurn:
                        print("its a riverrrr")
                        nextEmptySquarePos: tuple[int, int] | None = None
                        nextEdge = None
                        currentEdge = Tile.get_opposite(edge)
                        for e in Tile.get_edges():
                            if e == currentEdge:
                                continue

                            if card.internal_edges[e] != StructureType.RIVER:
                                continue
                            nextEdge = e
                            match e:
                                case "left_edge":
                                    nextEmptySquarePos = (emptySquarePos[0], emptySquarePos[1] - 1)
                                case "right_edge":
                                    nextEmptySquarePos = (emptySquarePos[0], emptySquarePos[1] + 1)
                                case "top_edge":
                                    nextEmptySquarePos = (emptySquarePos[0] - 1, emptySquarePos[1])
                                case "bottom_edge":
                                    nextEmptySquarePos = (emptySquarePos[0] + 1, emptySquarePos[1])

                        
                        if nextEmptySquarePos is None:
                            print("next empty square pos is None, skipping to next possible edge", edge, flush=True)
                            continue
                        print("next empty square pos is", nextEmptySquarePos[1], nextEmptySquarePos[0], "for edge", nextEdge, flush=True)
                        #if 2 or more immediate neighbours then has to be immediate u turn so illegal, swap directions and hope
                        numAdj = countSurroundingTiles(game, nextEmptySquarePos[1], nextEmptySquarePos[0])
                        print("Placed tile at", nextEmptySquarePos[1], nextEmptySquarePos[0], "would have", numAdj, "adjacent tiles", flush=True)
                        if numAdj >= 2:
                            card.rotate_clockwise(1) # flips otherway
                            # Either needs to flip once or thrice
                            if card.internal_edges[Tile.get_opposite(edge)] != StructureType.RIVER:
                                card.rotate_clockwise(2)
                            print("flipped", card.tile_type, ", edges are now:", card.internal_edges)
                            #TODO: check if this is actually a valid placement if not then panic cuz should always be valid after rotation if initial invalid

                        #should only ever have one river tile card in hand so can just return?
                        card.placed_pos = emptySquarePos[1], emptySquarePos[0]
                        lastPlaced = card._to_model()
                        lastPlacedTile = card

                        #TODO immediate claim meeple logic??
                        print("placing tile", card.tile_type, "at", edge, "at position:", emptySquarePos[1], emptySquarePos[0], "with rotation", card.rotation, flush=True)
                        print()
                        return game.move_place_tile(query, card._to_model(), i)
                            


                    # From here, everything is either already ours or unclaimed and not  in river turns
                    # Immediately place the card if we can finish a structure THAT IS OURS OR UNCLAIMED
                    elif incompleteEdges == 1 and structType != StructureType.GRASS:
                        print("can be immediate finished, finishing a", structType, flush=True)
                        card.placed_pos = emptySquarePos[1], emptySquarePos[0]
                        lastPlaced = card._to_model()
                        lastPlacedTile = card

                        # Set immediate claim flag to place a meeple
                        if unclaimed:
                            immediateClaim = True
                            claimingEdge = Tile.get_opposite(edge)
                            print("unclaimed tile, setting immediate claim to", claimingEdge, flush=True)
                        return game.move_place_tile(query, card._to_model(), i)

                    # Then set priority to extending our cities with emblems
                    elif card in emblemCards:
                        print("card has emblem, placing it", flush=True)
                        optimalTile = card
                        optimalPos = emptySquarePos[1], emptySquarePos[0]
                        placingEmblem = True

                        if unclaimed:
                            wantToClaim = True
                            claimingEdge = Tile.get_opposite(edge)
                            print("unclaimed tile, setting want to claim to", claimingEdge, flush=True)
                        
                        print(optimalTile.tile_type, "I AM INEVITABLE (claiming emblem card tile)", claimingEdge, flush=True)

                    # If we arent placing an emblem then focus on extending anything we have
                    elif not placingEmblem:
                        if ours:
                            print("extending our structure", structType, "at edge", edge, flush=True)
                            optimalTile = card
                            optimalPos = emptySquarePos[1], emptySquarePos[0]
                            extendingOurs = True
                            print("its...ours?")
                        elif not extendingOurs:
                            print("extending unclaimed structure", structType, "at edge", edge, flush=True)
                            optimalTile = card
                            optimalPos = emptySquarePos[1], emptySquarePos[0]

                            # If we havent already found a tile that is ours and the current structure is unclaimed
                            wantToClaim = True
                            claimingEdge = Tile.get_opposite(edge)
                            print("\ntrying to claim tile", optimalTile.tile_type, "with claiming edge", claimingEdge, "\n", flush=True)
    print("finished examining possible tile placements", flush=True)

    if optimalTile:
        optimalTile.placed_pos = optimalPos
        print("\nplacing tile ", optimalTile.tile_type, "at ", optimalTile.placed_pos, "\n", flush=True)
        lastPlaced = optimalTile._to_model()
        lastPlacedTile = optimalTile
        return game.move_place_tile(query, optimalTile._to_model(), hand.index(optimalTile))
    
    print("no optimal tile found, placing first valid placement", flush=True)
    # Only returns here if there is no way to extend either our OWN or UNCLAIMED structures
    firstTileIndex = next(iter(validPlacements))
    firstTile = hand[firstTileIndex]
    firstCoords = validPlacements[firstTileIndex][0]   #TODO double check x y order for this is correct as x y
    firstTile.placed_pos = firstCoords
    lastPlaced = firstTile._to_model()
    lastPlacedTile = firstTile
    print("placing first tile", firstTile.tile_type, "at", firstTile.placed_pos, "with rotation", firstTile.rotation, flush=True)
    return game.move_place_tile(query, firstTile._to_model(), firstTileIndex)

def countSurroundingTiles(game: Game, x: int, y: int, countCorners:bool = True) -> int:
    """
    Count the number of tiles surrounding a given position (x, y) on the game map.
    """
    count = 0
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue # dont count start center tile

            if not countCorners and abs(dx) + abs(dy) == 2:
                continue  # skip corners if not counting them

            newx, newy = x + dx, y + dy
            if 0 <= newx <= MAXCOLINDEX and 0 <= newy <= MAXROWINDEX:
                if game.state.map._grid[newy][newx] is not None:
                    count += 1
    return count

class dfsEnums(Enum):
    INCOMPLETEEDGES = auto()
    CURRENTPOINTS = auto()
    COMPLETEDPOINTS = auto()
    CLAIMS = auto()

def countIncompleteEdges(game:Game, startTile: Tile, startEdge: str) -> dict[dfsEnums, int | dict[int, int]]:
    '''
    is this how descriptions are made
    '''
    returnDict:dict[dfsEnums, int | dict[int, int]] = {
        dfsEnums.INCOMPLETEEDGES: 0,
        dfsEnums.CURRENTPOINTS: 0, # current points of the structure
        dfsEnums.COMPLETEDPOINTS: 0, # points if structure is completed (should only be different for cities for now)
        dfsEnums.CLAIMS: {}, #player_id: number of meeples on this structure

    }
    seen = set()
    desiredType = startTile.internal_edges[startEdge]

    #skips grass TODO grass logic
    if desiredType == StructureType.GRASS:
        return returnDict
    
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


claimedStructures:dict[StructureType, int] = {
    StructureType.CITY: 0,
    StructureType.ROAD: 0,
    StructureType.GRASS: 0,
    StructureType.MONASTARY: 0,
}

MAXCLAIMEDCITIES = 4
MAXCLAIMEDROADS = 3
MAXCLAIMEDGRASS = 0 #ignore grass for now TODO: grass logic
MAXCLAIMEDMONASTARIES = 10 #we always like monastaries, except probably some edge case logic
def handle_place_meeple(query: QueryPlaceTile, game: Game) -> MovePlaceMeeple | MovePlaceMeeplePass:
    print("HELLOOO MEEPLES\n", flush=True)
    print("CURRENT CLAIMED STRUCTURES", claimedStructures, flush=True)
    # if game.state.num_placed_tiles < 3:
    #     print("PASSING", flush=True)
    #     return game.move_place_meeple_pass(query)

    x, y = lastPlaced.pos
    tile = game.state.map._grid[y][x]

    assert tile is not None

    if immediateClaim:
        print("MEEPLE IMMEDIATE CLAIM ON", lastPlaced.tile_type, claimingEdge, flush=True)
        return game.move_place_meeple(query, lastPlaced, claimingEdge)

    print("GOT TO HERE ON", lastPlaced.tile_type, claimingEdge, flush=True)

    if game.state.me.num_meeples < 2:
        print("NEED TO KEEP ONE MEEPLE. PASSING", flush=True)
        return game.move_place_meeple_pass(query)
    
    if wantToClaim:
        structure = lastPlacedTile.internal_edges[claimingEdge]
        print("MEEPLE WANT CLAIM ON", lastPlaced.tile_type, claimingEdge, "FOR", structure, flush=True)

        if structure == StructureType.CITY and claimedStructures[StructureType.CITY] < MAXCLAIMEDCITIES:
            claimedStructures[StructureType.CITY] += 1
            print("claiming city", flush=True)
            return game.move_place_meeple(query, lastPlaced, claimingEdge)
        elif structure == StructureType.ROAD and claimedStructures[StructureType.ROAD] < MAXCLAIMEDROADS:
            claimedStructures[StructureType.ROAD] += 1
            print("claiming road", flush=True)
            return game.move_place_meeple(query, lastPlaced, claimingEdge)
        elif structure == StructureType.GRASS and claimedStructures[StructureType.GRASS] < MAXCLAIMEDGRASS:
            claimedStructures[StructureType.GRASS] += 1
            print("claiming grass", flush=True)
            return game.move_place_meeple(query, lastPlaced, claimingEdge)
        elif structure == StructureType.MONASTARY and claimedStructures[StructureType.MONASTARY] <  MAXCLAIMEDMONASTARIES:
            claimedStructures[StructureType.MONASTARY] += 1
            print("claiming monastary", flush=True)
            return game.move_place_meeple(query, lastPlaced, claimingEdge)

    print("meeple pass,", flush=True)
    return game.move_place_meeple_pass(query)

print("test bot.py loaded", flush=True)

if __name__ == "__main__":
    main()
