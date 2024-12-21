# -*- coding: utf-8 -*-
"""Battle boats:
    Place 10 boats of various lengths on a ten by ten grid.
    Boats may not touch, not even diagonally.
    Row and column sums count the number of boat parts in row/column.
    Partial placement is provided (see constraints below).

variables are boat types, see BOAT_LENGTH.keys()
domains are locations that boats can be placed as tuples: (x, y, orientation)

Constraints defined:
        BoatBoundaries
        RowSum
        ColSum
        CellEmpty - puzzle specifies an empty cell
        BoatEnd - puzzle specifies a boat end part
                  with opening up, down, left, right
        BoatMid - puzzle specifies a boat mid part,
                  boat may extend in either direction
        BoatSub - puzzle specifies a submarine (boat length of 1)

lru cache is used for common analysis functions.

Created on Fri May  5 03:40:16 2023
@author: Ann"""

# %% imports

import functools as ft
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '../..')))

from csp_solver import constraint as cnstr
from csp_solver import experimenter
from csp_solver import problem
from csp_solver import var_chooser
from csp_solver import variable


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


# %%  boat helper functions

@ft.lru_cache(maxsize=64)
def get_end_loc(x, y, orient, boat_len):
    """Return the coord's of the end of the boat.
    RETURN int, int"""

    dx, dy = INCS[orient]
    xend = x + (dx * (boat_len - 1))
    yend = y + (dy * (boat_len - 1))

    return xend, yend

@ft.lru_cache(maxsize=64)
def grids_occed(x, y, orient, boat_len):
    """return a list of the cells occupied by boat."""

    cells = [(x, y)]

    if boat_len == 1:
        return cells

    if orient == VERT:
        for nx in range(x + 1, x + boat_len):
            cells += [(nx, y)]

    else:
        for ny in range(y + 1, y + boat_len):
            cells += [(x, ny)]

    return cells


@ft.lru_cache(maxsize=64)
def grids_bounding(x, y, orient, boat_len):
    """Return a set of the cells around the boat,
    but not the cells of the boat itself."""

    cells = []

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
        cells += [(nx, box_ul[1]) for nx in range(bnd_ul[0], bnd_lr[0] + 1)]

    if 1 <= box_lr[1] <= SIZE:   # bottom
        cells += [(nx, box_lr[1]) for nx in range(bnd_ul[0], bnd_lr[0] + 1)]

    if 1 <= box_ul[0] <= SIZE:   # left side
        cells += [(box_ul[0], ny) for ny in range(bnd_ul[1], bnd_lr[1] + 1)]

    if 1 <= box_lr[0] <= SIZE:   # right side
        cells += [(box_lr[0], ny) for ny in range(bnd_ul[1], bnd_lr[1] + 1)]

    return set(cells)


@ft.lru_cache(maxsize=64)
def grids_mid(x, y, orient, boat_len):
    """Return a list of the mid parts occupied by boat."""

    # pylint: disable=magic-value-comparison

    if boat_len <= 2:
        return None

    dx, dy = INCS[orient]

    if boat_len == 3:
        return [(x + dx, y + dy)]

    if boat_len == 4:
        return [(x + dx, y + dy), (x + 2 * dx, y + 2 * dy)]

    return None

def grids_bound_end(x, y, direct):
    """Return a set of cells that cannot contain boats based
    upon an end constraint.

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

def empty_cells(empty_list, vobjs_list, func):
    """Remove/Hide any domain values (start locations) that
    would include any location in the empty_list.

    Call with func as one of:
      variable.Variable.remove_dom_val for preprocessor
      variable.Variable.hide for forward_check

    Return False if overconstrainted (e.g. any domain is emptied),
    True otherwise.  Forward check can return the return value.
    Preprocess should raise PreprocessorConflict."""

    for bobj in vobjs_list:
        blength = BOAT_LENGTH[bobj.name]

        for value in bobj.get_domain()[:]:
            x, y, orient = value

            if (x, y) in empty_list:
                if not func(bobj, value):
                    return False
                continue

            needed = grids_occed(x, y, orient, blength)

            if any(coord in empty_list for coord in needed):
                if not func(bobj, value):
                    return False

    return True


# %% boat overlaps


class BoatBoundaries(cnstr.Constraint):
    """Boats must not overlap and no boat may be in the boundary
    of another.

    If only one boat is assigned, return True."""

    def __repr__(self):
        return 'BoatBoundaries()'

    @staticmethod
    def satisfied(boat_dict):
        """Test the constraint."""

        if len(boat_dict) == 1:
            return True

        occupied = set()
        bounds = set()
        for bname, location in boat_dict.items():

            x, y, orient = location
            length = BOAT_LENGTH[bname]
            bcells = grids_occed(x, y, orient, length)

            if (occupied and
                any(coord in occupied or coord in bounds
                    for coord in bcells)):
                return False

            occupied |= set(bcells)
            bounds |= grids_bounding(x, y, orient, length)

        return True


    def forward_check(self, assignments):
        """Hide all values that are in the boundary or already
        occupied."""

        hide_list = set()
        for bname, (x, y, orient) in assignments.items():
            length = BOAT_LENGTH[bname]

            hide_list |= set(grids_occed(x, y, orient, length))
            hide_list |= grids_bounding(x, y, orient, length)

        unassigned= [vobj for vobj in self._vobjs
                     if vobj.name not in assignments]

        return empty_cells(hide_list, unassigned, variable.Variable.hide)


class IncOrder(cnstr.OneOrder):
    """Boats must be assigned in increasing order sorted by location.

    Variable lists should be matching boat types, e.g. all submarines."""

    def forward_check(self, assignments):
        """If any of our variables are assigned, limit any unassigned
        ones to be > that the last assigned one.

        The boat order var chooser assures that sub1 is assigned
        before sub2, etc.

        The domains are generated in a sorted order, so we can exit
        when we find one > """

        last_bname = None
        for bname in self._vnames:
            if bname in assignments:
                last_bname = bname

        if not last_bname or last_bname == self._vnames[-1]:
            return True

        unassigned = self._vobjs[self._vnames.index(last_bname) + 1:]
        min_loc = assignments[last_bname]

        for vobj in unassigned:
            for val in vobj.get_domain()[:]:
                if val[:2] <= min_loc:

                    if not vobj.hide(val):
                        return False
                else:
                    break

        return True



# %%  row column sums

class RowSum(cnstr.Constraint):
    """The number of boats parts in row is <= rsum until all variables
    are boat locations then they must be equal."""

    def __init__(self, row, rsum):
        super().__init__()
        self._row = row
        self._row_sum = rsum

    def __repr__(self):
        return f'RowSum({self._row}, {self._row_sum})'

    def satisfied(self, boat_dict):
        """Test the constraint."""
        cur_sum = 0

        for bname, (x, _, orient) in boat_dict.items():
            blength = BOAT_LENGTH[bname]

            if orient == HORZ and x == self._row:
                cur_sum += blength

            elif orient == VERT and x <= self._row <= x + blength - 1:
                cur_sum += 1

            if cur_sum > self._row_sum:
                return False

        if len(boat_dict) == B_CNT:
            return cur_sum == self._row_sum

        return cur_sum <= self._row_sum

    def preprocess(self):
        """If the row_sum is zero remove any boat start location
        that would occupy the row."""

        if not self._row_sum:

            row_coords = [(self._row, y) for y in range(1, SIZE_P1)]
            if not empty_cells(row_coords, self._vobjs,
                               variable.Variable.remove_dom_val):
                raise cnstr.PreprocessorConflict(f'{self} is overconstrained.')
            return True

        # TODO how can we know if the problem meets the constraint?

        return False


    def forward_check(self, assignments):
        """If the row sum is exactly satisfied; make certain that
        there are not any boats crossing row.

        Return - False if any domain has been eliminated, True otherwise."""

        occed_cols = [False] * (SIZE_P1)
        cur_sum = 0

        for bname, (x, y, orient) in assignments.items():
            blength = BOAT_LENGTH[bname]

            if orient == HORZ and x == self._row:
                cur_sum += blength
                occed_cols[x:x + blength] = [True] * blength

            elif orient == VERT and x <= self._row <= x + blength - 1:
                cur_sum += 1
                occed_cols[self._row] = True

            if cur_sum > self._row_sum:
                return False

        if cur_sum < self._row_sum:
            return True

        empty_cols = [(self._row, y)
                      for y in range(1, SIZE+1) if not occed_cols[y]]

        unassigned= [vobj for vobj in self._vobjs
                      if vobj.name not in assignments]

        return empty_cells(empty_cols, unassigned, variable.Variable.hide)



class ColSum(cnstr.Constraint):
    """The number of boats parts in col is <= csum until all variables
    are boat locations then they must be equal."""

    def __init__(self, col, csum):
        super().__init__()
        self._col = col
        self._col_sum = csum

    def __repr__(self):
        return f'ColSum({self._col}, {self._col_sum})'

    def satisfied(self, boat_dict):
        """Test the constraint."""

        cur_sum = 0

        for bname, (_, y, orient) in boat_dict.items():
            blength = BOAT_LENGTH[bname]

            if orient == VERT and y == self._col:
                cur_sum += blength

            elif orient == HORZ and y <= self._col <= y + blength - 1:
                cur_sum += 1

            if cur_sum > self._col_sum:
                return False

        if len(boat_dict) == B_CNT:
            return cur_sum == self._col_sum

        return cur_sum <= self._col_sum

    def preprocess(self):
        """If the col_sum is zero remove any boat start location
        that would occupy the column."""

        if not self._col_sum:

            col_coords = [(x, self._col) for x in range(1, SIZE_P1)]
            if not empty_cells(col_coords, self._vobjs,
                               variable.Variable.remove_dom_val):
                raise cnstr.PreprocessorConflict(f'{self} is overconstrained.')
            return True

        # TODO how can we know if the problem meets the constraint?

        return False


    def forward_check(self, assignments):
        """If the col sum is exactly satisfied; make certain that
        there are not any boats crossing col.

        Return - False if any domain has been eliminated, True otherwise."""

        occed_rows = [False] * (SIZE_P1)
        cur_sum = 0

        for bname, (x, y, orient) in assignments.items():
            blength = BOAT_LENGTH[bname]

            if orient == VERT and y == self._col:
                cur_sum += blength
                occed_rows[y:y + blength] = [True] * blength

            elif orient == HORZ and y <= self._col <= y + blength - 1:
                cur_sum += 1
                occed_rows[self._col] = True

            if cur_sum > self._col_sum:
                return False

        if cur_sum < self._col_sum:
            return True

        empty_rows = [(x, self._col)
                      for x in range(1, SIZE+1) if not occed_rows[x]]

        unassigned= [vobj for vobj in self._vobjs
                      if vobj.name not in assignments]

        return empty_cells(empty_rows, unassigned, variable.Variable.hide)



# %%  partial solution


class CellEmpty(cnstr.Constraint):
    """The cell at row, col must be empty."""

    def __init__(self, row, col):
        super().__init__()
        self._loc = (row, col)

    def __repr__(self):
        return f'CellEmpty({self._loc[0]}, {self._loc[1]})'

    def satisfied(self, boat_dict):
        """Test the constraint."""

        for bname, (x, y, orient) in boat_dict.items():

            length = BOAT_LENGTH[bname]

            if self._loc in grids_occed(x, y, orient, length):
                return False

        return True

    def preprocess(self):
        """Remove any domain values (start locations) that
        would include (row, col). Contraint will be fully satisfied,
        but call _test_over_satis to make certain it is not over
        contsrainted (it will raise exception)."""

        if not empty_cells([self._loc], self._vobjs,
                           variable.Variable.remove_dom_val):
            raise cnstr.PreprocessorConflict(f'{self} is overconstrained.')

        return True


class BoatEnd(cnstr.Constraint):
    """A boat must end at (row, col) and continue in the direction of
    cont_dir.

    This constraint prohibits submarines from being at (row, col),
    return False if a sub is assigned to (row, col).

    If not, True is returned anyway; until all boats are assigned."""

    def __init__(self, row, col, cont_dir):
        super().__init__()
        self._loc = (row, col)
        self._cont_dir = cont_dir

    def __repr__(self):
        return f'BoatEnd({self._loc[0]}, {self._loc[1]}, {self._cont_dir})'

    def satisfied(self, boat_dict):
        """Test the constraint.

        x, y are the upper/left corner of the boat.
        If continue direction is UP or RIGHT we need to compare to the
        end location of the boat (lower/right)."""

        for bname, (x, y, orient) in boat_dict.items():

            coord = (x, y)
            blength = BOAT_LENGTH[bname]

            if blength == 1:
                if self._loc == coord:
                    return False
                continue

            end = get_end_loc(x, y, orient, blength)

            if self._cont_dir == DOWN:
                good = self._loc == coord and orient == VERT

            elif self._cont_dir == LEFT:
                good = self._loc == end and orient == HORZ

            elif self._cont_dir == UP:
                good = self._loc == end and orient == VERT

            elif self._cont_dir == RIGHT:
                good = self._loc == coord and orient == HORZ

            if good:
                return True

        return len(boat_dict) < B_CNT

    def preprocess(self):
        """Given boat end and direction, we know which cells opposite of
        continue direction and sides (plus +1 in cont_dir) can be
        removed from the domains of all variables.

        Remove (row, col, VERT) from the domain of submarines,
        they can't be put at (row, col).

        For boats longer than 2, remove any values that put a middle
        part of the boat at (row, col)."""

        empties = grids_bound_end(*self._loc, self._cont_dir)
        if not empty_cells(empties, self._vobjs,
                           variable.Variable.remove_dom_val):
            raise cnstr.PreprocessorConflict(f'{self} is overconstrained.')


        for bobj in self._vobjs:

            length = BOAT_LENGTH[bobj.name]

            # TODO special case of destroyers when end is one away from edge
            #  can't assign, but remove all but one value from domain

            if length == 1:
                loc = (*self._loc, VERT)
                if loc in bobj.get_domain():
                    bobj.remove_dom_val(loc)
                continue

            if length == 2:
                continue

            for value in bobj.get_domain()[:]:

                x, y, orient = value
                end = get_end_loc(x, y, orient, length)

                if self._loc in [(x, y), end]:
                    continue

                if self._loc in grids_occed(x, y, orient, length):
                    bobj.remove_dom_val(value)

        self._test_over_satis()
        return False

    # TODO is a forward check for BoatEnd useful?
    # once constraint is met, remove boat end from other domains?


class BoatMid(cnstr.Constraint):
    """A boat mid part must be at (row, col).

    This constraint prohibits submarines and destroyers from
    using (row, col).

    If not, True is returned anyway; until all boats are assigned."""

    def __init__(self, row, col):
        super().__init__()
        self._loc = (row, col)

    def __repr__(self):
        return f'BoatMid({self._loc[0]}, {self._loc[1]})'

    def satisfied(self, boat_dict):
        """Test the constraint."""

        for bname, (x, y, orient) in boat_dict.items():
            length = BOAT_LENGTH[bname]

            if length == 1:
                if self._loc == (x, y):
                    return False
                continue

            if length == 2:
                if self._loc in grids_occed(x, y, orient, length):
                    return False
                continue

            mids = grids_mid(x, y, orient, length)
            if self._loc in mids:
                return True

        return len(boat_dict) < B_CNT

    def preprocess(self):
        """Remove the diagonals from the domains of all the
        variables. Constraint is never fully applied here."""

        # TODO a boat mid with a row,col sum of 3 is a
        # cruiser (if know which, e.g. edge or 0 row/col)

        x, y = self._loc
        diags = [(x-1, y-1), (x-1, y+1), (x+1, y-1), (x+1, y+1)]

        if not empty_cells(diags, self._vobjs,
                           variable.Variable.remove_dom_val):
            raise cnstr.PreprocessorConflict(f'{self} is overconstrained.')

        return False

    # TODO write forward_check for BoatMid?
    # once constraint is met, remove boat mid from other domains?


class BoatSub(cnstr.Constraint):
    """A submarine must be at (row, col).

    For any boat longer than a submarine, if it occupies (row, col)
    return False.

    If all 4 subs are assigned but none at (row, col) return False,
    otherwise True."""

    def __init__(self, row, col):
        super().__init__()
        self._loc = (row, col)

    def __repr__(self):
        return f'BoatSub({self._loc[0]}, {self._loc[1]})'

    def satisfied(self, boat_dict):
        """Test the constraint."""

        sub_cnt = 0

        for bname, (x, y, orient) in boat_dict.items():
            length = BOAT_LENGTH[bname]

            if length > 1:
                if self._loc in grids_occed(x, y, orient, length):
                    return False
                continue

            sub_cnt += 1
            if self._loc == (x, y):
                return True

        return sub_cnt < 4

    def preprocess(self):
        """Remove (row, col) from all boats longer than 1."""

        for bobj in self._vobjs:

            length = BOAT_LENGTH[bobj.name]

            if length > 1:
                if not empty_cells([self._loc], [bobj],
                                   variable.Variable.remove_dom_val):
                    raise cnstr.PreprocessorConflict(f'{self} is overconstrained.')
                continue

        return False


    # TODO BoatSub forward_check, what should it do?


# %%

MAX_INPUT = 500

ROWSUM = "RowSum"
COLSUM = "ColSum"

EMPTYCELL = "EmptyCell"
SUMBARINE = "Sumbarine"
BOATTOP = "BoatTop"
BOATBOTTOM = "BoatBottom"
BOATLEFT = "BoatLeft"
BOATRIGHT = "BoatRight"
BOATMID = "BoatMid"


BOAT_CNSTR = {EMPTYCELL : CellEmpty,
              SUMBARINE : BoatSub,
              BOATTOP : BoatEnd,
              BOATBOTTOM : BoatEnd,
              BOATLEFT : BoatEnd,
              BOATRIGHT : BoatEnd,
              BOATMID : BoatMid
              }

ORIENT = {BOATTOP : DOWN,
          BOATBOTTOM : UP,
          BOATLEFT : RIGHT,
          BOATRIGHT : LEFT
          }


def decode_to_constraints(pairs):
    """Use as object_pairs_hook in json.loads
    because key names will not be unique."""

    cons = []

    for name, value in pairs:

        if name == ROWSUM:
            for row, rsum in enumerate(value):
                cons += [RowSum(row + 1, rsum)]
            continue

        if name == COLSUM:
            for col, csum in enumerate(value):
                cons += [ColSum(col + 1, csum)]
            continue

        con_class = BOAT_CNSTR[name]
        row, col = value

        if issubclass(con_class, BoatEnd):
            cons += [con_class(row, col, ORIENT[name])]
        else:
            cons += [con_class(row, col)]

    return cons

def read_puzzle(filename):
    """Read the puzzle and return a BoatGrid."""

    with open(filename, 'r', encoding='UTF-8') as file:
        lines = file.readlines()

    raw_data = ''.join(lines)

    if len(raw_data) > MAX_INPUT:
        return None

    return json.loads(raw_data, object_pairs_hook=decode_to_constraints)



# %% problem statement  (BOATS)

def add_basic(boatprob):
    """Add the basic constraints common to all battle boats problems."""

    boatprob.var_chooser = BoatOrder

    # add boat location variables and domains
    for bname, length in BOAT_LENGTH.items():
        boatprob.add_variable(bname, pos_locs(length))

    # reduces solutions from 2! * 3! * 4! = 288 to 1
    boatprob.add_constraint(IncOrder(), ['cruiser1', 'cruiser2'])
    boatprob.add_constraint(IncOrder(), ['destroyer1', 'destroyer2', 'destroyer3'])
    boatprob.add_constraint(IncOrder(), ['sub1', 'sub2', 'sub3', 'sub4'])

    #  boats should not overlap or touch
    boatprob.add_constraint(BoatBoundaries(), BOATS)


def build_one(boatprob):
    """Battleship/Commodore problem from Games Magazine September 2019."""

    add_basic(boatprob)

    # row/col sums
    rsums = [3, 1, 2, 1, 1, 2, 1, 1, 4, 4]
    for row, rsum in enumerate(rsums):
        boatprob.add_constraint(RowSum(row + 1, rsum), BOATS)

    csums = [5, 0, 2, 1, 2, 0, 2, 4, 1, 3]
    for col, csum in enumerate(csums):
        boatprob.add_constraint(ColSum(col + 1, csum), BOATS)

    # partial solutions:   boat start/end, middle, sub, or empty loc
    boatprob.add_constraint(CellEmpty(1, 10), BOATS)

    boatprob.add_constraint(BoatEnd(2, 1, UP), BOATS)
    boatprob.add_constraint(BoatEnd(9, 7, DOWN), BOATS)


def build_two(boatprob):
    """Battleship/Seaman problem from Games Magazine September 2019."""

    add_basic(boatprob)

    cons = read_puzzle(PUZ_PATH + "seaman_sept2019.txt")

    for con in cons:
        boatprob.add_constraint(con, BOATS)


def build_three(boatprob):
    """Battleship/Admiral problem from Games Magazine September 2019."""

    add_basic(boatprob)

    cons = read_puzzle(PUZ_PATH + "admiral_sept2019.txt")

    for con in cons:
        boatprob.add_constraint(con, BOATS)


def build_four(boatprob):
    """Battleship/Petty Officer problem from Games Magazine September 2019."""

    add_basic(boatprob)

    cons = read_puzzle(PUZ_PATH + "p_officer_sept2019.txt")

    for con in cons:
        boatprob.add_constraint(con, BOATS)


def build_five(boatprob):
    """Randomly generated build."""

    add_basic(boatprob)

    cons = read_puzzle(PUZ_PATH + "test.txt")

    for con in cons:
        boatprob.add_constraint(con, BOATS)


# %%  boat order var chooser

class BoatOrder(var_chooser.VarChooser):
    """Choose the variable assignment order based on boat length."""

    @staticmethod
    def choose(vobjs, _1, _2):
        """var chooser"""
        return max(vobjs, key = lambda var : BOAT_LENGTH[var.name])

BoatOrder()  # to catch any interface changes


# %%  print the grid

def print_grid(solution, _=None):
    """print the solution grid"""

    grid = [[' . '] * SIZE for _ in range(SIZE)]
    for bname, location in solution.items():
        for x, y in grids_occed(*location, BOAT_LENGTH[bname]):
            grid[x - 1][y - 1] = ' x '

    print('    1  2  3  4  5  6  7  8  9 10')
    for ridx, row in enumerate(grid):
        print(f'{ridx+1:2}', ''.join(row))


# %%  test constraints against correct answer

def test_answer(boatprob, correct):
    """Test the correct answer against the constraints."""

    boatprob.var_chooser = BoatOrder
    boatprob._spec.prepare_variables()

    good = True
    for con in boatprob._spec.constraints:

        con_assign = {vname : correct[vname] for vname in con.get_vnames()
                        if vname in correct}

        if not con.satisfied(con_assign):
            print('False', con, con.get_vnames())
            good = False

    if good:
        print('\nAll good.')

def test_wrapper():
    """Get the data from last UI generated puzzle and answer."""

    boatprob = problem.Problem()
    build_five(boatprob)

    print('Reading answer:')
    with open(PUZ_PATH + "answer.txt", encoding='UTF-8') as file:
        answer = json.load(file)
    print_grid(answer)
    print()

    test_answer(boatprob, answer)


# %%   main

builds = [build_one, build_two, build_three, build_four, build_five]

if __name__ == '__main__':

    experimenter.do_stuff(builds, print_grid)


if __name__ == '__test_example__':

    for build in builds:

        print(f'\nSolving build {build.__name__}:\n', build.__doc__)
        bprob = problem.Problem()
        build(bprob)
        bprob.var_chooser = BoatOrder
        sol = bprob.get_solution()
        print_grid(sol)
