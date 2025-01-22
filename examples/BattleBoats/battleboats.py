# -*- coding: utf-8 -*-
"""Support BattleBoats constants and routines.

https://en.wikipedia.org/wiki/Battleship_(puzzle)

Created on Fri May  5 03:40:16 2023
@author: Ann"""

# %% imports

import collections
import functools as ft
import json
import os


# %% constants

# this allows running from tests or BattleBoats,
#  but could get it wrong if examples in the path above CSPSolver
if 'examples' in os.path.abspath(os.curdir):
    PUZ_PATH = "./BB_Puzzles/"
else:
    PUZ_PATH = "./examples/BattleBoats/BB_Puzzles/"


SIZE = 10
SIZE_P1 = SIZE + 1

BOAT_LENGTH = {'battleship' : 4,
               'cruiser1' : 3,
               'cruiser2' : 3,
               'destroyer1' : 2,
               'destroyer2' : 2,
               'destroyer3' : 2,
               'sub1' : 1,
               'sub2' : 1,
               'sub3' : 1,
               'sub4' : 1}

BOATS = list(BOAT_LENGTH.keys())

B_CNT = len(BOATS)

# orientations
VERT = 0
HORZ = 1

INCS = [(1, 0), (0, 1)]

# directions - direction of open end
UP = 0
RIGHT = 1
DOWN = 2
LEFT = 3

CONT_INCS = ((-1, 0),
             (0, 1),
             (1, 0),
             (0, -1))

CONT_ORIENT = (VERT, HORZ, VERT, HORZ)


# %%  grid and boat helper functions

def cont_pos(loc, direction):
    """Return the grid loc for the continue position of a
    boat end at loc in direction."""

    return tuple(a + b for a, b in zip(loc, CONT_INCS[direction]))


def assign_loc(x1, y1, x2, y2):
    """Given the boat ends, return the assignment location
    i.e. the upper left of the two points.
    Either x1 == x2  or  y1 == y2"""

    if x1 < x2 or y1 < y2:
        return x1, y1

    return x2, y2


def grid_diags(x, y):
    """Return the cells diagonal to x, y.
    Can ignore edges if this is used in empty_cells,
    because it checks if actual boat locations are in this
    set."""

    return {(x - 1, y - 1), (x - 1, y + 1),
            (x + 1, y - 1), (x + 1, y + 1)}


def grid_cross(x, y):
    """Return the neighbors in the same row/col as x, y.
    Can ignore edges if this is used in empty_cells,
    because it checks if actual boat locations are in this
    set."""

    return {(x, y - 1), (x, y + 1), (x + 1, y), (x - 1, y)}


@ft.lru_cache(maxsize=64)
def grid_neighs(x, y):
    """Return the cells that are neighbors to x, y.
    Can ignore edges if this is used in empty_cells,
    because it checks if actual boat locations are in this
    set."""

    return {(x - 1, y - 1), (x - 1, y), (x - 1, y + 1),
            (x, y - 1), (x, y + 1),
            (x + 1, y - 1), (x + 1, y), (x + 1, y + 1)}


@ft.lru_cache(maxsize=64)
def get_end_loc(x, y, orient, boat_len):
    """Return the coord's of the end of the boat.
    This will be the lower-rightmost point.
    RETURN int, int"""

    dx, dy = INCS[orient]
    xend = x + (dx * (boat_len - 1))
    yend = y + (dy * (boat_len - 1))

    return xend, yend


@ft.lru_cache(maxsize=64)
def grids_occed(x, y, orient, boat_len):
    """Return the set of the cells occupied by boat."""

    cells = {(x, y)}

    if boat_len == 1:
        return cells

    if orient == VERT:
        for nx in range(x + 1, x + boat_len):
            cells |= {(nx, y)}

    else:
        for ny in range(y + 1, y + boat_len):
            cells |= {(x, ny)}

    return cells


@ft.lru_cache(maxsize=64)
def grids_bounding(x, y, orient, boat_len):
    """Return the set of the cells around the boat,
    but not the cells of the boat itself."""

    cells = set()

    if orient == VERT:
        xend = x + boat_len - 1
        yend = y
    else:
        xend = x
        yend = y + boat_len - 1

    box_ul = (x - 1, y - 1)
    box_lr = (xend + 1, yend + 1)

    bnd_ul = (max(1, box_ul[0]), max(1, box_ul[1]))
    bnd_lr = (min(10, box_lr[0]), min(10, box_lr[1]))

    if 1 <= box_ul[1] <= SIZE:   # top
        cells |= {(nx, box_ul[1]) for nx in range(bnd_ul[0], bnd_lr[0] + 1)}

    if 1 <= box_lr[1] <= SIZE:   # bottom
        cells |= {(nx, box_lr[1]) for nx in range(bnd_ul[0], bnd_lr[0] + 1)}

    if 1 <= box_ul[0] <= SIZE:   # left side
        cells |= {(box_ul[0], ny) for ny in range(bnd_ul[1], bnd_lr[1] + 1)}

    if 1 <= box_lr[0] <= SIZE:   # right side
        cells |= {(box_lr[0], ny) for ny in range(bnd_ul[1], bnd_lr[1] + 1)}

    return cells


@ft.lru_cache(maxsize=64)
def grids_mid(x, y, orient, boat_len):
    """Return a set of the mid parts occupied by boat."""

    if boat_len <= 2:
        return None

    dx, dy = INCS[orient]

    if boat_len == 3:
        return {(x + dx, y + dy)}

    if boat_len == 4:
        return {(x + dx, y + dy), (x + 2 * dx, y + 2 * dy)}

    return None


def grids_bound_end(x, y, direct):
    """Return a set of cells that cannot contain boats based
    upon an end constraint. These are known water cells.

    Compute the orientation and start location (if we don't have it).
    Collect the boundaries cells of a boat of length 2.
    Remove the center spots on the side opposite the constraint.

    No cache needed called in only in preprocessor."""

    if direct in [DOWN, RIGHT]:
        orient = VERT if direct == DOWN else HORZ
        cells = grids_bounding(x, y, orient, 2)
    else:
        orient = VERT if direct == UP else HORZ
        dx, dy = INCS[orient]
        cells = grids_bounding(x - dx, y - dy, orient, 2)

    if direct == UP:
        far_end = (x - 2, y)
    elif direct == DOWN:
        far_end = (x + 2, y)
    elif direct == RIGHT:
        far_end = (x, y + 2)
    elif direct == LEFT:
        far_end = (x, y - 2)

    if far_end in cells:
        cells.remove(far_end)

    return cells


def grids_bound_mid(x, y):
    """Return a set of cells that cannot contain boats based
    upon an mid boat part. These are known water cells.

    If it's on an edge, we know the boat orientation and return
    5 cells. Otherwise only the diagonals.

    No cache needed called in only in preprocessor."""

    cells = None

    if x == 1:
        cells = {(x + 1, y + dy) for dy in range(-2, 3)}

    elif x == SIZE:
        cells = {(x - 1, y + dy) for dy in range(-2, 3)}

    elif y == 1:
        cells = {(x + dx, y + 1) for dx in range(-2, 3)}

    elif x == SIZE:
        cells = {(x + dx, y - 1) for dx in range(-2, 3)}

    else:
        cells = grid_diags(x, y)

    return cells


# %%  cache management

def cache_clear():
    """clear the cache of the functions with caches"""
    get_end_loc.cache_clear()
    grids_occed.cache_clear()
    grids_bounding.cache_clear()
    grids_mid.cache_clear()


def cache_info():
    """print the cache_info of the functions with caches"""

    print('get_end_loc:\n   ', get_end_loc.cache_info())
    print('grids_occed\n   ', grids_occed.cache_info())
    print('grids_bounding\n   ', grids_bounding.cache_info())
    print('grids_mid\n   ', grids_mid.cache_info())
    print()


# %% boat positions

def pos_locs(boat_len):
    """Return the possible start locations and orientations of the boats.
    These are the 'values' or domain of the variable assignments.
    Orientation of boat length one doesn't matter (pick one).

    IncOrder requires that these be sorted."""

    if boat_len == 1:
        return [(x, y, VERT)
                for x in range(1, SIZE_P1)
                for y in range(1, SIZE_P1)]

    return sorted([(x, y, VERT)
                   for x in range(1, SIZE - boat_len + 2)
                   for y in range(1, SIZE_P1)] +  \
                  [(x, y, HORZ)
                   for x in range(1, SIZE_P1)
                   for y in range(1, SIZE - boat_len + 2)])


# %%  prop empty cells

def empty_cells(empty_set, vobjs_list, func):
    """Remove/Hide any domain values (start locations) that
    would include any location in the empty_set.

    Call with func as one of:
      variable.Variable.remove_dom_val for preprocessor
      variable.Variable.hide for forward_check

    This does not collect a list of changed variables
    because it is significantly slower.
    Could be different with new implementation.

    Return False if overconstrainted (e.g. any domain is emptied),
    True otherwise.  Forward check can return the return value.
    Preprocess should raise PreprocessorConflict."""

    for bobj in vobjs_list:
        blength = BOAT_LENGTH[bobj.name]
        change = collections.deque()

        for value in bobj.get_domain():
            x, y, orient = value

            if (x, y) in empty_set:
                change.append(value)
                continue

            needed = grids_occed(x, y, orient, blength)
            if empty_set & needed:
                change.append(value)

        for value in change:
            if not func(bobj, value):
                return False

    return True


def remove_starts(bobj, no_start):
    """Remove any domain values whose location is in no_start.
    Not sure this is useful for any bobj other than subs."""

    for value in bobj.get_domain_copy():
        if (value[0], value[1]) in no_start:

            if not bobj.remove_dom_val(value):
                return False

    return True


def remove_starts_ends(bobj, no_ends):
    """Remove domain values that start or end in no_ends."""

    domain = bobj.get_domain()

    for x, y in no_ends:

        # if value is invalid, it will fail the domain test below
        end_list = ((x, y, VERT),
                    (x, y, HORZ),
                    (x, y - 1, VERT),
                    (x - 1, y, HORZ))

        for end in end_list:
            if end in domain and not bobj.remove_dom_val(end):
                return False

    return True


# %% puzzle reader

MAX_INPUT = 500

ROWSUM = "RowSum"
COLSUM = "ColSum"

EMPTYCELL = "EmptyCell"
SUMBARINE = "Submarine"
BOATTOP = "BoatTop"
BOATBOTTOM = "BoatBottom"
BOATLEFT = "BoatLeft"
BOATRIGHT = "BoatRight"
BOATMID = "BoatMid"

ORIENT = {BOATTOP : DOWN,
          BOATBOTTOM : UP,
          BOATLEFT : RIGHT,
          BOATRIGHT : LEFT
          }

def read_puzzle(filename):
    """Read the puzzle a list of the constraints.

    Use object_pairs_hook in json.loads
    because key names might not be unique."""

    with open(filename, 'r', encoding='UTF-8') as file:
        lines = file.readlines()

    raw_data = ''.join(lines)

    if len(raw_data) > MAX_INPUT:
        return None

    return json.loads(raw_data, object_pairs_hook=lambda pairs: pairs)


# %% print grid from assigns

def print_grid(solution, _=None):
    """print the solution grid from the assignment dictionary"""

    grid = [[' . '] * SIZE for _ in range(SIZE)]
    for bname, location in solution.items():
        for x, y in grids_occed(*location, BOAT_LENGTH[bname]):
            grid[x - 1][y - 1] = ' x '

    print('    1  2  3  4  5  6  7  8  9 10')
    for ridx, row in enumerate(grid):
        print(f'{ridx+1:2}', ''.join(row))
    print()
    for var, val in sorted(solution.items()):
        if var in ('cruiser1', 'destroyer1', 'sub1'):
            print()
        print(var, val, end=', ')
    print()


# %%   main

if __name__ == '__test_example__':

    skipped = True
    reason = 'Support module'
