# -*- coding: utf-8 -*-
"""Battle boats:
    Place 10 boats of various lengths on a ten by ten grid.
    Boats may not touch, not even diagonally.
    Row and column sums count the number of boat parts in row/column.
    Partial placement is provided (see constraints below).

variables - boats
domains are locations that boats can be placed as tuples: (x, y, orientation)

Constraints:
    cnstr.Constraint - base class for other constraints
    BoatBoundaries
    IncOrder
    RowSum - from clues
    ColSum - from clues
    CellEmpty - from clues
    BoatEnd - from clues
    BoatMid - from clues
    BoatSub - from clues

Uses the extra data feature of the constraint engine:
    BBExtra(extra_data.ExtraDataIF)

Created on Fri May  5 03:40:16 2023
@author: Ann"""


# %% imports

import collections
import copy
import enum
import json

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '.')))

from csp_solver import constraint as cnstr
from csp_solver import experimenter
from csp_solver import extra_data
from csp_solver import problem
from csp_solver import solver
from csp_solver import variable
from csp_solver import var_chooser

from battleboats import PUZ_PATH
from battleboats import SIZE
from battleboats import SIZE_P1
from battleboats import BOAT_LENGTH
from battleboats import BOATS
from battleboats import B_CNT
from battleboats import VERT
from battleboats import HORZ
from battleboats import INCS
from battleboats import UP
from battleboats import RIGHT
from battleboats import DOWN
from battleboats import LEFT

from battleboats import get_end_loc
from battleboats import grids_occed
from battleboats import grids_bounding
# from battleboats import grids_mid
from battleboats import grids_bound_end
# from battleboats import cache_clear
from battleboats import cache_info
from battleboats import pos_locs
from battleboats import empty_cells
# from battleboats import decode_to_constraints
from battleboats import read_puzzle


# %%  enums

class EGrid(enum.IntEnum):
    """Values for the grid of the extra data."""

    UNKNOWN = enum.auto()
    BOUNDARY = enum.auto()

    WATER = enum.auto()

    BPART_START = enum.auto()
    ROUND = BPART_START
    END_TOP = enum.auto()
    END_BOT = enum.auto()
    END_LFT = enum.auto()
    END_RGT = enum.auto()
    MID = enum.auto()
    UNK_PART = enum.auto()
    BPART_END = UNK_PART


    def ok_to_assign(self):
        """Is it ok to assign a boat part."""
        return self in [self.UNKNOWN, self.UNK_PART]


    def is_boat_part(self):
        """Return True if self if a boat part"""
        return self.BPART_START <= self <= self.BPART_END

    def no_new_parts(self):
        """Return True if the a new part must not be assigned."""
        return (self == self.BOUNDARY
                or self.BPART_START <= self <= self.BPART_END)


    def is_marked_empty(self):
        """self should be a boundary condition. is it ok?"""
        return self not in [self.BOUNDARY, self.WATER]

    def char(self):
        """Return a char to print for self."""

        return ['q', '.', '-', 'w',
                'o',
                '\u02c4',
                '\u02c5',
                '\u02c2',
                '\u02c3',
                'x',
                'p'][self]



ENDS = [(EGrid.END_TOP, EGrid.END_BOT), (EGrid.END_LFT, EGrid.END_RGT)]


# %% extra data

class BBExtra(extra_data.ExtraDataIF):
    """The extra data for battleboats

    grid - stores the information that we know from clues; info that
    the current assignments imply (boat parts and boarders);
    and some data that we can infer, e.g. there's boat part but we don't
    know what type."""

    def __init__(self):

        self.grid =  [[EGrid.UNKNOWN] * (SIZE_P1) for _ in range(SIZE_P1)]
        self.bad = False

        self._queue = collections.deque()


    def __str__(self):
        """Return the grid string."""

        ostr = '     1  2  3  4  5  6  7  8  9 10\n'
        for x in range(1, SIZE_P1):

            rstr = f'{x:2}  '
            for y in range(1, SIZE_P1):
                rstr += ' ' + self.grid[x][y].char() + ' '
            ostr += rstr + '\n'

        return ostr


    @staticmethod
    def _assign_bpart(temp_grid, x, y, part):
        """Assign the boat part if it's ok and return True,
        else return False"""

        if temp_grid[x][y] == part:
            return True

        if temp_grid[x][y].ok_to_assign():
            temp_grid[x][y] = part
            return True

        return False


    @classmethod
    def _place_boat(cls, temp_grid, loc, length):
        """Place the boat.
        Return True if placed ok, False otherwise."""

        x, y, orient = loc

        if length == 1:
            if not cls._assign_bpart(temp_grid, x, y, EGrid.ROUND):
                return False
            return True

        dx, dy = INCS[orient]
        ul_end, lr_end = ENDS[orient]

        if not cls._assign_bpart(temp_grid, x, y, ul_end):
            return False

        for i in range(1, length - 1):
            if not cls._assign_bpart(temp_grid, x + i*dx, y + i*dy, EGrid.MID):
                return False

        i = length - 1
        if not cls._assign_bpart(temp_grid, x + i*dx, y + i*dy, lr_end):
            return False

        return True


    def assign(self, vname, val):
        """Update the grid with the boat (vname) assigned to
        location (val=(x, y, orient)).
        Update a copy of the grid in case an error is found.

        If a conflict is detected return False, otherwise True."""

        self._queue.append(self.grid)

        length = BOAT_LENGTH[vname]
        temp_grid = copy.deepcopy(self.grid)
        self.bad = True

        if not self._place_boat(temp_grid, val, length):
            return False

        for x, y in grids_bounding(*val, length):

            if temp_grid[x][y] == EGrid.UNKNOWN:
                temp_grid[x][y] = EGrid.BOUNDARY

            elif not temp_grid[x][y].is_marked_empty():
                return False

        self.grid = temp_grid
        self.bad = False

        return True


    def pop(self):
        """Undo the last assignment."""

        self.grid = self._queue.pop()



# %% boat overlaps


class BoatBoundaries(cnstr.Constraint):
    """Boats must not overlap and no boat may be in the boundary
    of another."""

    def __init__(self):

        super().__init__()
        self.extra = None

    def __repr__(self):
        return 'BoatBoundaries()'

    def set_extra(self, extra):
        """Save the extra data."""
        self.extra = extra

    def satisfied(self, boat_dict):
        """Test the constraint."""

        _ = boat_dict

        return not self.extra.bad

    def forward_check(self, assignments):
        """Hide all values that are in the boundary or already
        occupied."""

        hide_list = [(x, y) for x in range(1, SIZE_P1)
                     for y in range(1, SIZE_P1)
                     if self.extra.grid[x][y].no_new_parts()]

        unassigned= [vobj for vobj in self._vobjs
                     if vobj.name not in assignments]

        return empty_cells(hide_list, unassigned, variable.Variable.hide)


class IncOrder(cnstr.OneOrder, cnstr.Constraint):
    """Boats must be assigned in increasing order sorted by location.

    Variable lists should be matching boat types, e.g. all submarines."""

    def __init__(self):

        super().__init__()
        self.extra = None

    def set_extra(self, extra):
        """Save the extra data."""
        self.extra = extra

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
        self.extra = None

    def __repr__(self):
        return f'RowSum({self._row}, {self._row_sum})'

    def set_extra(self, extra):
        """Save the extra data."""
        self.extra = extra

    def satisfied(self, boat_dict):
        """Test the constraint."""

        cur_sum = sum(1 for y in range(1, SIZE_P1)
                      if self.extra.grid[self._row][y].is_boat_part())

        if len(boat_dict) == B_CNT:
            return cur_sum == self._row_sum

        return cur_sum <= self._row_sum

    def preprocess(self):
        """If the row_sum is zero remove any boat start location
        that would occupy the row."""

        if not self._row_sum:

            for y in range(1, SIZE_P1):
                self.extra.grid[self._row][y] = EGrid.WATER

            row_coords = [(self._row, y) for y in range(1, SIZE_P1)]
            if not empty_cells(row_coords, self._vobjs,
                               variable.Variable.remove_dom_val):
                raise cnstr.PreprocessorConflict(f'{self} is overconstrained.')
            return True

        return False

    def forward_check(self, assignments):
        """If the row sum is exactly satisfied; make certain that
        there are not any boats crossing row.
        If the row sum and empty sum equals required sum, put generic
        boat parts in the grid.

        Return - False if any domain has been eliminated, True otherwise."""

        occed_cols = [False] * SIZE

        cur_sum = unk_cnt = 0
        for y in range(1, SIZE_P1):

            cell_val = self.extra.grid[self._row][y]

            if cell_val == EGrid.UNKNOWN:
                unk_cnt += 1

            elif cell_val.is_boat_part():
                cur_sum += 1
                occed_cols[y - 1] = True

            if cur_sum > self._row_sum:
                return True

        empty_cols = [(self._row, y)
                      for y in range(1, SIZE+1) if not occed_cols[y]]

        if cur_sum == self._row_sum:

            for x, y in empty_cols:
                self.extra.grid[x][y] = EGrid.WATER

            unassigned= [vobj for vobj in self._vobjs
                          if vobj.name not in assignments]
            return empty_cells(empty_cols, unassigned, variable.Variable.hide)

        if cur_sum + unk_cnt == self._row_sum:
            for x, y in empty_cols:
                self.extra.grid[x][y] = EGrid.UNK_PART

        return True


class ColSum(cnstr.Constraint):
    """The number of boats parts in clm is <= csum until all variables
    are boat locations then they must be equal."""

    def __init__(self, col, csum):

        super().__init__()
        self._col = col
        self._col_sum = csum
        self.extra = None

    def __repr__(self):
        return f'ColSum({self._col}, {self._col_sum})'

    def set_extra(self, extra):
        """Save the extra data."""
        self.extra = extra

    def satisfied(self, boat_dict):
        """Test the constraint."""

        cur_sum = sum(1 for x in range(1, SIZE_P1)
                      if self.extra.grid[x][self._col].is_boat_part())

        if len(boat_dict) == B_CNT:
            return cur_sum == self._col_sum

        return cur_sum <= self._col_sum

    def preprocess(self):
        """If the col_sum is zero remove any boat start location
        that would occupy the column."""

        if not self._col_sum:

            for x in range(1, SIZE_P1):
                self.extra.grid[x][self._col] = EGrid.WATER

            col_coords = [(x, self._col) for x in range(1, SIZE_P1)]
            if not empty_cells(col_coords, self._vobjs,
                               variable.Variable.remove_dom_val):
                raise cnstr.PreprocessorConflict(f'{self} is overconstrained.')
            return True

        return False

    def forward_check(self, assignments):
        """If the col sum is exactly satisfied; make certain that
        there are not any boats crossing col.
        If the col sum and empty sum equals required sum, put generic
        boat parts in the grid.

        Return - False if any domain has been eliminated, True otherwise."""

        occed_rows = [False] * (SIZE_P1)

        cur_sum = unk_cnt = 0
        for x in range(1, SIZE_P1):

            cell_val = self.extra.grid[x][self._col]

            if cell_val == EGrid.UNKNOWN:
                unk_cnt += 1

            elif cell_val.is_boat_part():
                cur_sum += 1
                occed_rows[x - 1] = True

            if cur_sum > self._row_sum:
                return True

        empty_cols = [(x, self._col)
                      for x in range(1, SIZE+1) if not occed_rows[x]]

        if cur_sum == self._row_sum:
            for x, y in empty_cols:
                self.extra.grid[x][y] = EGrid.WATER

            unassigned = [vobj for vobj in self._vobjs
                          if vobj.name not in assignments]
            return empty_cells(empty_cols, unassigned, variable.Variable.hide)

        if cur_sum + unk_cnt == self._row_sum:
            for x, y in empty_cols:
                self.extra.grid[x][y] = EGrid.UNK_PART

        return True


# %%  partial solution


class CellEmpty(cnstr.Constraint):
    """The cell at row, col must be empty."""

    def __init__(self, row, col):

        super().__init__()
        self._loc = (row, col)
        self.extra = None

    def __repr__(self):
        return f'CellEmpty({self._loc[0]}, {self._loc[1]})'

    def set_extra(self, extra):
        """Save the extra data."""
        self.extra = extra

    def satisfied(self, boat_dict):
        """Preprocess is overriddent, doesn't use _test_over_satis
        and it always fully applies the constraint: no test needed."""
        _ = boat_dict

        return True

    def preprocess(self):
        """Remove any domain values (start locations) that
        would include (row, col). Contraint will be fully satisfied."""

        if not empty_cells([self._loc], self._vobjs,
                           variable.Variable.remove_dom_val):
            raise cnstr.PreprocessorConflict(f'{self} is overconstrained.')

        self.extra.grid[self._loc[0]][self._loc[1]] = EGrid.WATER
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
        self.extra = None

    def __repr__(self):
        return f'BoatEnd({self._loc[0]}, {self._loc[1]}, {self._cont_dir})'

    def set_extra(self, extra):
        """Save the extra data."""
        self.extra = extra

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

    def _update_grid(self, empties):
        """Update the grid with the BoatEnd constraint info.
        Put water in the bounding cells and an UNKnown PART
        in the CONTinue DIRection."""

        for x, y in empties:
            self.extra.grid[x][y] = EGrid.WATER

        x, y = self._loc
        if self._cont_dir == UP:
            self.extra.grid[x][y] = EGrid.END_BOT
            self.extra.grid[x - 1][y] = EGrid.UNK_PART

        elif self._cont_dir == DOWN:
            self.extra.grid[x][y] = EGrid.END_TOP
            self.extra.grid[x + 1][y] = EGrid.UNK_PART

        elif self._cont_dir == RIGHT:
            self.extra.grid[x][y] = EGrid.END_LFT
            self.extra.grid[x][y + 1] = EGrid.UNK_PART

        elif self._cont_dir == LEFT:
            self.extra.grid[x][y] = EGrid.END_RGT
            self.extra.grid[x][y - 1] = EGrid.UNK_PART

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

        self._update_grid(empties)

        # TODO special case of destroyers when end is one away from edge

        for bobj in self._vobjs:
            length = BOAT_LENGTH[bobj.name]

            if length == 1:
                loc = (*self._loc, VERT)
                if loc in bobj.get_domain():
                    if not bobj.remove_dom_val(loc):
                        raise cnstr.PreprocessorConflict(
                            f'{self} is overconstrained.')
                continue

            if length == 2:
                continue

            for value in bobj.get_domain()[:]:
                x, y, orient = value

                if self._loc in grids_occed(x, y, orient, length)[1:-1]:
                    if not bobj.remove_dom_val(value):
                        raise cnstr.PreprocessorConflict(
                            f'{self} is overconstrained.')

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
        self.extra = None

    def __repr__(self):
        return f'BoatMid({self._loc[0]}, {self._loc[1]})'

    def set_extra(self, extra):
        """Save the extra data."""
        self.extra = extra

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

            mids = grids_occed(x, y, orient, length)[1:-1]
            if self._loc in mids:
                return True

        return len(boat_dict) < B_CNT

    def _update_grid(self, diags):
        """Update the grid with the BoatMid constraint info.
        Put water in the diag cells and MID part."""

        for x, y in diags:
            self.extra.grid[x][y] = EGrid.WATER

        x, y = self._loc
        self.extra.grid[x][y] = EGrid.MID

    def preprocess(self):
        """Remove the diagonals from the domains of all the
        variables. Constraint is never fully applied here."""

        # TODO a boat mid with a row,col sum of 3 is a
        # cruiser (if know which, e.g. edge or 0 row/col)

        # TODO a boat mid one cell away from a boat end is
        # the battleship

        x, y = self._loc
        diags = [(x-1, y-1), (x-1, y+1), (x+1, y-1), (x+1, y+1)]

        if not empty_cells(diags, self._vobjs,
                           variable.Variable.remove_dom_val):
            raise cnstr.PreprocessorConflict(f'{self} is overconstrained.')

        self._update_grid(diags)

        return False

    # TODO write BoatMid.forward_check
    # place UNK_PART s when we know where they should go


class BoatSub(cnstr.Constraint):
    """A submarine must be at (row, col).

    For any boat longer than a submarine, if it occupies (row, col)
    return False.

    If all 4 subs are assigned but none at (row, col) return False,
    otherwise True."""

    def __init__(self, row, col):

        super().__init__()
        self._loc = (row, col)
        self.extra = None

    def __repr__(self):
        return f'BoatSub({self._loc[0]}, {self._loc[1]})'

    def set_extra(self, extra):
        """Save the extra data."""
        self.extra = extra

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

    def _update_grid(self, bounds):
        """Update the grid with the BoatSub constraint info.
        Put water in the bounding cells and place the sub."""

        for x, y in bounds:
            self.extra.grid[x][y] = EGrid.WATER

        x, y = self._loc
        self.extra.grid[x][y] = EGrid.ROUND

    def preprocess(self):
        """Remove (row, col) and bounding cells from all boats longer
        than 1."""

        empties = grids_bounding(*self._loc, VERT, 1)
        self._update_grid(empties)

        empties |= {self._loc}
        for bobj in self._vobjs:

            length = BOAT_LENGTH[bobj.name]

            if length == 1:
                continue

            if not empty_cells(empties, [bobj],
                               variable.Variable.remove_dom_val):
                raise cnstr.PreprocessorConflict(f'{self} is overconstrained.')

        return False


# %%  boat order var chooser

class BoatOrder(var_chooser.VarChooser):
    """Choose the variable assignment order based on boat length.
    do longest boats first."""

    @staticmethod
    def choose(vobjs, prob_spec, assignments):
        """var chooser"""

        _ = prob_spec, assignments

        return max(vobjs, key = lambda var : BOAT_LENGTH[var.name])



# %% problem statement  (BOATS)

def add_basic(boatprob):
    """Add the basic constraints common to all battle boats problems."""

    extra = BBExtra()
    boatprob.extra = extra
    boatprob.solver = solver.NonRecBacktracking()
    boatprob.var_chooser = BoatOrder()
    boatprob.forward_check = True

    # add boat location variables and domains
    for bname, length in BOAT_LENGTH.items():
        boatprob.add_variable(bname, pos_locs(length))

    # reduces solutions from 2! * 3! * 4! = 288 to 1
    boatprob.add_constraint(IncOrder(), ['cruiser1', 'cruiser2'])
    boatprob.add_constraint(IncOrder(), ['destroyer1', 'destroyer2', 'destroyer3'])
    boatprob.add_constraint(IncOrder(), ['sub1', 'sub2', 'sub3', 'sub4'])

    #  boats should not overlap or touch
    boatprob.add_constraint(BoatBoundaries(), BOATS)

    for con in boatprob._spec.constraints:
        con.set_extra(extra)

    return extra


def build_one(boatprob):
    """Battleship/Commodore problem from Games Magazine September 2019."""

    extra = add_basic(boatprob)

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

    for con in boatprob._spec.constraints:
        con.set_extra(extra)


def build_two(boatprob):
    """Battleship/Seaman problem from Games Magazine September 2019."""

    extra = add_basic(boatprob)
    cons = read_puzzle(PUZ_PATH + "puzzles/seaman_sept2019.txt")

    for con in cons:
        boatprob.add_constraint(con, BOATS)
        con.set_extra(extra)


def build_three(boatprob):
    """Battleship/Admiral problem from Games Magazine September 2019."""

    extra = add_basic(boatprob)
    cons = read_puzzle(PUZ_PATH + "puzzles/admiral_sept2019.txt")

    for con in cons:
        boatprob.add_constraint(con, BOATS)
        con.set_extra(extra)


def build_four(boatprob):
    """Battleship/Petty Officer problem from Games Magazine September 2019."""

    extra = add_basic(boatprob)
    cons = read_puzzle(PUZ_PATH + "puzzles/p_officer_sept2019.txt")

    for con in cons:
        boatprob.add_constraint(con, BOATS)
        con.set_extra(extra)


def build_five(boatprob):
    """Randomly generated build."""

    extra = add_basic(boatprob)
    cons = read_puzzle(PUZ_PATH + "puzzles/test.txt")

    for con in cons:
        boatprob.add_constraint(con, BOATS)
        con.set_extra(extra)


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

    print()
    cache_info()


# %%  test constraints against correct answer

def test_answer(boatprob, correct):
    """Test the correct answer against the constraints."""

    boatprob.set_var_chooser(BoatOrder)
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
    with open(PUZ_PATH + "puzzles/answer.txt", encoding='UTF-8') as file:
        answer = json.load(file)
    print_grid(answer)
    print()

    test_answer(boatprob, answer)


# %%   main

builds = [build_one, build_two, build_three, build_four, build_five]


if __name__ == '__main__':

    experimenter.do_stuff(builds, print_grid)


if __name__ == '__test_example__':

    # for build in builds:
    #     bprob = problem.Problem()
    #     build(bprob)
    #     bprob.var_chooser = BoatOrder
    #     sol = bprob.get_solution()
    #     print_grid(sol)

    skipped = True
    reason = 'Has errors and slow.'
