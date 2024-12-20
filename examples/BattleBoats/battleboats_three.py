# -*- coding: utf-8 -*-
"""Battle boats:
    Place 10 boats of various lengths on a ten by ten grid.
    Boats may not touch, not even diagonally.
    Row and column sums count the number of boat parts in row/column.
    Partial placement is provided (see constraints below).

variables - boats
domains - locations

Constraints:
    BBoatCnstr - base class for other constraints
    NoOccedDiag
    NbrParts
    BoatCounts
    RowSum - from clues
    ColSum - from clues
    CellEmpty - from clues
    BoatEnd - from clues
    BoatMid - from clues
    BoatSub - from clues

Uses the extra data feature of the constraint engine:
    BBExtra(extra_data.ExtraDataIF)


Created on Thu May 11 18:53:28 2023
@author: Ann"""

# %% imports

import collections
import copy
import enum
import functools as ft
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '../..')))

from csp_solver import arc_consist
from csp_solver import constraint as cnstr
from csp_solver import experimenter
from csp_solver import extra_data
from csp_solver import problem
from csp_solver import var_chooser


# %%  enums

class BoatVals(enum.IntEnum):
    """Values for the boat grid."""

    UNKNOWN = enum.auto()
    WATER = enum.auto()

    ROUND = enum.auto()
    BPART_START = ROUND
    END_TOP = enum.auto()
    END_BOT = enum.auto()
    END_LFT = enum.auto()
    END_RGT = enum.auto()
    MID = enum.auto()
    UNK_PART = enum.auto()
    BPART_END = UNK_PART


    def ok_to_assign(self, val):
        """Is it ok to assign a boat part."""

        if self == self.WATER and val == self.WATER:
            return True

        return self in [self.UNKNOWN, self.UNK_PART]

    def is_boat_part(self):
        """Return True if self if a boat part"""
        return self.BPART_START <= self <= self.BPART_END

    def no_new_parts(self):
        """Return True if the a new part must not be assigned."""
        return (self == self.WATER
                or self.BPART_START <= self <= self.BPART_END)

    def opp_end(self):
        """Return opposite end part."""

        if self == BoatVals.END_BOT:
            return BoatVals.END_TOP

        if self == BoatVals.END_TOP:
            return BoatVals.END_BOT

        if self == BoatVals.END_LFT:
            return BoatVals.END_RGT

        return BoatVals.END_LFT

    def char(self):
        """Return a char to print for self."""

        return BoatVals.grid_chars[self]


BoatVals.grid_chars = ['q', '.', 'w', 'o',
                       '\u02c4', '\u02c5', '\u02c2', '\u02c3',
                       'x', 'p']

BoatVals.assign_vals = [BoatVals.ROUND, BoatVals.END_TOP,
                        BoatVals.END_BOT, BoatVals.END_LFT, BoatVals.END_RGT,
                        BoatVals.MID, BoatVals.WATER]
BoatVals.boat_parts = [BoatVals.ROUND, BoatVals.END_TOP,
                       BoatVals.END_BOT, BoatVals.END_LFT, BoatVals.END_RGT,
                       BoatVals.MID]


# %% constants

PUZ_PATH ="./BB_Puzzles/"

SIZE = 10

BOAT_VARS =  [(x, y)
              for x in range(SIZE)
              for y in range(SIZE)]


BOATS = ['battleship', 'cruiser', 'destroyer', 'sub']


BOAT_NBR = {'battleship' : 1,
            'cruiser' : 2,
            'destroyer' : 3,
            'sub' : 4}

BOAT_LEN = {'battleship' : 4,
            'cruiser' : 3,
            'destroyer' : 2,
            'sub' : 1}

NBOATS = sum(BOAT_NBR.values())
NCELLS = sum(nbr * BOAT_LEN[boat] for boat, nbr in BOAT_NBR.items())

# orientations
VERT = 0
HORZ = 1

INCS = [(1, 0), (0, 1)]


# %%

def print_grid(assignments, _=None):
    """Convert the assignments to a grid and print it."""

    grid = [[-1] * SIZE for _ in range(SIZE)]

    for (x, y), value in assignments.items():
        grid[x][y] = value

    print('    0  1  2  3  4  5  6  7  8  9\n')
    for x in range(0, SIZE):

        print(x, end='  ')
        for y in range(0, SIZE):
            print(f' {grid[x][y]} ', end='')
        print()


# %%  variable sets

def neigh_cells(x, y):
    """Create a list of the neighboring cells of x, y"""

    return [(x + dx, y + dy) for dx, dy in neigh_cells.locs
            if 0 <= x + dx < SIZE and 0 <= y + dy < SIZE]

neigh_cells.locs = [(-1, -1), (-1, 0), (-1, 1),
                    (0, -1), (0, 1),
                    (1, -1), (1, 0), (1, 1)]


def cell_diags(x, y):
    """Return the list of diagonal cells for x, y limiting
    to those on the grid."""

    return [(x + dx, y + dy) for dx, dy in cell_diags.crosses
            if 0 <= x + dx < SIZE and 0 <= y + dy < SIZE]

cell_diags.crosses = [(0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]


def diagonals():
    """Generate the diagonals for each cell.
    Only list locations on the grid.
    Include the center location as the first location."""

    for x in range(SIZE):
        for y in range(SIZE):
            yield cell_diags(x, y)


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

    bnd_ul = (max(0, box_ul[0]), max(0, box_ul[1]))
    bnd_lr = (min(9, box_lr[0]), min(9, box_lr[1]))

    if 0 <= box_ul[1] < SIZE:   # top
        cells += [(nx, box_ul[1]) for nx in range(bnd_ul[0], bnd_lr[0] + 1)]

    if 0 <= box_lr[1] < SIZE:   # bottom
        cells += [(nx, box_lr[1]) for nx in range(bnd_ul[0], bnd_lr[0] + 1)]

    if 0 <= box_ul[0] < SIZE:   # left side
        cells += [(box_ul[0], ny) for ny in range(bnd_ul[1], bnd_lr[1] + 1)]

    if 0 <= box_lr[0] < SIZE:   # right side
        cells += [(box_lr[0], ny) for ny in range(bnd_ul[1], bnd_lr[1] + 1)]

    return set(cells)


def grids_bound_end(x, y, boat_end):
    """Return a set of cells that cannot contain boats based
    upon an end constraint.

    Compute the orientation and start location (if we don't have it).
    Collect the boundaries cells of a boat of length 2.
    Remove the center spots on the side opposite the constraint."""

    if boat_end in [BoatVals.END_TOP, BoatVals.END_LFT]:
        orient = VERT if boat_end == BoatVals.END_TOP else HORZ
        cells = grids_bounding(x, y, orient, 2)
    else:
        orient = VERT if boat_end == BoatVals.END_BOT else HORZ
        dx, dy = INCS[orient]
        cells = grids_bounding(x - dx, y - dy, orient, 2)

    if boat_end == BoatVals.END_BOT:
        far_end = (x - 2, y)
    elif boat_end == BoatVals.END_TOP:
        far_end = (x + 2, y)
    elif boat_end == BoatVals.END_LFT:
        far_end = (x, y + 2)
    elif boat_end == BoatVals.END_RGT:
        far_end = (x, y - 2)

    if far_end in cells:
        cells.remove(far_end)

    return cells


def grids_bend_cont_cell(x, y, boat_end):
    """Return the cell in which the boat must continue."""

    if boat_end == BoatVals.END_BOT:
        return (x - 1, y)

    if boat_end == BoatVals.END_TOP:
        return (x + 1, y)

    if boat_end == BoatVals.END_LFT:
        return (x, y + 1)

    return (x, y - 1)



# %% extra data

class BBExtra(extra_data.ExtraDataIF):
    """The extra data for battleboats.

    grid - stores the information that we know from clues; info that
    the current assignments imply (boat parts and boarders);
    and some data that we can infer, e.g. there's boat part but we don't
    know what type.

    counts - list number of boats of each length. Index is boat_length - 1

    var_dict - the overall variable dictionary from the problem spec
    """

    def __init__(self, variables):

        self.grid =  [[BoatVals.UNKNOWN] * SIZE for _ in range(SIZE)]
        self.counts = [0] * NBOATS
        self.var_dict = variables

        self._queue = collections.deque()


    def __str__(self):
        """Return the grid string."""

        ostr = '     0  1  2  3  4  5  6  7  8  9\n'
        for x in range(SIZE):

            rstr = f'{x:2}  '
            for y in range(SIZE):
                rstr += ' ' + self.grid[x][y].char() + ' '
            ostr += rstr + '\n'

        ostr += '\n'
        ostr += f'Battleship {self.counts[3]}\n'
        ostr += f'Cruisers   {self.counts[2]}\n'
        ostr += f'Destroyer  {self.counts[1]}\n'
        ostr += f'Subs       {self.counts[0]}\n'

        return ostr


    def assign(self, vname, val):
        """Update the grid.
        If a conflict is detected return False, otherwise True."""

        x, y = vname
        if not self.grid[x][y].ok_to_assign(val):
            return False

        self._queue.append((copy.deepcopy(self.grid), self.counts.copy()))

        self.grid[x][y] = val
        self.counts = self._count_boats()
        return True


    def pop(self):
        """Undo the last assignment."""

        self.grid, self.counts = self._queue.pop()


    def _count_vert(self, x, y):
        """There is a boat top at x, y.
        See if the rest of a boat is there and return it's length."""


        for dx in range(1, min(5, SIZE - x)):
            if self.grid[x + dx][y] != BoatVals.MID:
                break
        else:
            return False

        if x + dx < SIZE and self.grid[x + dx][y] == BoatVals.END_BOT:
            return dx + 1

        return False


    def _count_horz(self, x, y):
        """There is a boat left end at x, y.
        See if the rest of a boat is there and return it's length."""

        for dy in range(1, min(5, SIZE - y)):
            if self.grid[x][y + dy] != BoatVals.MID:
                break
        else:
            return False

        if y + dy < SIZE and self.grid[x][y + dy] == BoatVals.END_RGT:
            return dy + 1

        return False


    def _count_boats(self):
        """Count the number of boats.
        Index of counts is boat_length - 1."""

        counts = [0] * NBOATS

        for x in range(SIZE):
            for y in range(SIZE):

                if self.grid[x][y] == BoatVals.ROUND:
                    counts[0] += 1
                    continue

                if self.grid[x][y] == BoatVals.END_TOP:
                    if (length := self._count_vert(x, y)):
                        counts[length - 1] += 1

                    continue

                if self.grid[x][y] == BoatVals.END_LFT:
                    if (length := self._count_horz(x, y)):
                        counts[length - 1] += 1

        return counts


# %% bboats base constraint

class BBoatCnstr(cnstr.Constraint):
    """Base battleboats constraint.
    __init__  saves the 'extra' data.
    Turns off arc consistency checking (no binary constraints).
    Disables preprocessor (no unary or binary constraints)."""

    ARC_CONSIST_CHECK_OK = arc_consist.ArcConCheck.NEVER

    def __init__(self, extra):

        super().__init__()
        self.extra = extra

    def preprocess(self):
        """Disable preprocessor."""
        # pylint: disable=no-self-use

        return False

    def remove_bparts(self, obj_list):
        """Remove all boat parts from the domain of each variable,
        possibly leaving water.
        Use only in preprocessor."""

        for vobj in obj_list:
            for val in vobj.get_domain()[:]:
                if val in BoatVals.boat_parts:
                    if not vobj.remove_dom_val(val):
                        raise cnstr.PreprocessorConflict(
                            f'{self} is overconstrained.')

    def remove_to(self, vobj, save_val):
        """Reduce the domain of vobj to val.
        Use only in preprocessor."""

        for val in vobj.get_domain()[:]:
            if val is save_val:
                continue

            if not vobj.remove_dom_val(val):
                raise cnstr.PreprocessorConflict(f'{self} is overconstrained.')


    def hide_bparts_ex(self, excludes):
        """Hide boat parts from unassigned variables,
        excluding those listed.
        Use only in forward check"""

        ch_names = set()
        for vobj in self._vobjs:
            if vobj.name in excludes:
                continue

            change = False
            for val in vobj.get_domain()[:]:
                if val in BoatVals.boat_parts:
                    change = True
                    if not vobj.hide(val):
                        return False

            if change:
                ch_names |= {vobj.name}

        return ch_names or True


    def hide_water_ex(self, excludes):
        """Hide water from unassigned variables,
        excluding those listed.
        Use only in forward check."""

        ch_names = set()
        for vobj in self._vobjs:
            if vobj.name in excludes:
                continue

            if BoatVals.WATER in vobj.get_domain():
                if not vobj.hide(BoatVals.WATER):
                    return False
                ch_names |= {vobj.name}

        return ch_names or True

    @staticmethod
    def hide_to(vobj, save_val):
        """Hide domain values of vobj that are not save_val.
        Use only in forward check."""

        ch_name = None
        for val in vobj.get_domain()[:]:
            if val is save_val:
                continue

            if not vobj.hide(val):
                return False
            ch_name = vobj.name

        return ch_name or True


    def hide_diags_to_water(self, loc):
        """Hide domain values of the diagonals that are not WATER.
        Use only in forward check."""

        ch_names = set()
        for x, y in cell_diags(*loc):
            changes = self.hide_to(self.extra.var_dict[(x, y)], BoatVals.WATER)
            if changes is False:
                return False

            ch_names |= changes
            self.extra.grid[x][y] = BoatVals.WATER

        return ch_names or True


# %%   bboat constraints

class NoOccedDiag(BBoatCnstr):
    """If there is a boat part at center_loc,
    no diagonal cells may be occupied."""

    def __init__(self, extra, center_loc):

        super().__init__(extra)
        self._loc = center_loc

    def __repr__(self):
        return f'NoOccedDiag({self._loc})'

    def satisfied(self, assignments):
        """Test the constraint."""

        if self._loc in assignments and assignments[self._loc].is_boat_part():

            for x, y in assignments.keys():
                if (x, y) == self._loc:
                    continue

                if self.extra.grid[x][y].is_boat_part():
                    return False

        return True

    def foreward_check(self, assignments):
        """Constraint passed, remove boat parts from diags."""

        changes = True
        if self._loc in assignments and assignments[self._loc].is_boat_part():

            for x, y in assignments.keys():
                if (x, y) == self._loc:
                    continue
                self.extra.grid[x][y] = BoatVals.WATER

            changes = self.hide_bparts_ex(assignments.keys | self._loc)

        return changes


class NbrParts(BBoatCnstr):
    """Maximum number of boat parts allowed in a solution."""

    def __init__(self, extra, nbr_parts):

        super().__init__(extra)
        self._nbr_parts = nbr_parts

    def __repr__(self):
        return f'NbrParts({self._nbr_parts})'

    def satisfied(self, assignments):
        """Test the constraint."""

        parts = sum(1 for what in assignments.values() if what.is_boat_part())

        if len(assignments) == self._params:
            return parts == self._nbr_parts

        return parts <= self._nbr_parts


class BoatCounts(BBoatCnstr):
    """The number of boats of each type must match the expected counts."""

    def __init__(self, extra, exp_parts):

        super().__init__(extra)
        self._exp_parts = exp_parts

    def __repr__(self):
        return f'BoatCounts({self._exp_parts})'

    def satisfied(self, assignments):
        """Test the constraint."""

        for actual, expect in zip(self.extra.counts, self._exp_parts):
            if actual > expect:
                return False

        if len(assignments) < self._params:
            return True
        return self.extra.counts == self._exp_parts



class RowSum(BBoatCnstr):
    """The number of boats parts in row is <= rsum until all variables
    are boat locations then they must be equal."""

    def __init__(self, extra, row, rsum):

        super().__init__(extra)
        self._row = row
        self._row_sum = rsum

    def __repr__(self):
        return f'RowSum({self._row}, {self._row_sum})'

    def satisfied(self, assignments):
        """Test the constraint."""

        cur_sum = sum(1 for y in range(SIZE)
                      if self.extra.grid[self._row][y].is_boat_part())

        if len(assignments) == self._params:
            return cur_sum == self._row_sum

        return cur_sum <= self._row_sum

    def preprocess(self):
        """If the row_sum is zero, remove all boat parts from the domains
        of row variables (this fully applies the constraint)."""

        if not self._row_sum:

            for y in range(SIZE):
                self.extra.grid[self._row][y] = BoatVals.WATER
            self.remove_bparts(self._vobjs)
            return True

        return False

    def forward_check(self, assignments):
        """If the row sum is exactly satisfied; remove all but water
        from unassigned cells.
        If the row sum and empty sum equals required sum, put generic
        boat parts in the grid."""

        cur_sum = unk_cnt = 0
        for y in range(SIZE):
            if self.extra.grid[self._row][y].is_boat_part():
                cur_sum += 1
            elif self.extra.grid[self._row][y] == BoatVals.UNKNOWN:
                unk_cnt += 1

        if cur_sum == self._row_sum:
            return self.hide_bparts_ex(assignments)

        if cur_sum + unk_cnt == self._row_sum:
            for y in range(SIZE):
                if self.extra.grid[self._row][y] == BoatVals.UNKNOWN:
                    self.extra.grid[self._row][y] = BoatVals.UNK_PART

            return self.hide_water_ex(assignments)

        return True


class ColSum(BBoatCnstr):
    """The number of boats parts in clm is <= csum until all variables
    are boat locations then they must be equal."""

    def __init__(self, extra, col, csum):

        super().__init__(extra)
        self._col = col
        self._col_sum = csum

    def __repr__(self):
        return f'ColSum({self._col}, {self._col_sum})'

    def satisfied(self, assignments):
        """Test the constraint."""

        cur_sum = sum(1 for x in range(SIZE)
                      if self.extra.grid[x][self._col].is_boat_part())

        if len(assignments) == self._params:
            return cur_sum == self._col_sum

        return cur_sum <= self._col_sum

    def preprocess(self):
        """If the col_sum is zero remove any boat start location
        that would occupy the column."""

        if not self._col_sum:

            for x in range(SIZE):
                self.extra.grid[x][self._col] = BoatVals.WATER

            self.remove_bparts(self._vobjs)
            return True

        return False

    def forward_check(self, assignments):
        """If the col sum is exactly satisfied; make certain that
        there are not any boats crossing col.
        If the col sum and empty sum equals required sum, put generic
        boat parts in the grid."""

        cur_sum = unk_cnt = 0
        for x in range(SIZE):

            if self.extra.grid[x][self._col].is_boat_part():
                cur_sum += 1
            elif self.extra.grid[x][self._col] == BoatVals.UNKNOWN:
                unk_cnt += 1

        if cur_sum == self._row_sum:
            return self.hide_bparts_ex(assignments)

        if cur_sum + unk_cnt == self._row_sum:

            for x in range(SIZE):
                if self.extra.grid[x][self._col] == BoatVals.UNKNOWN:
                    self.extra.grid[x][self._col] = BoatVals.UNK_PART

            return self.hide_water_ex(assignments)

        return True


class CellEmpty(BBoatCnstr):
    """The cell at row, col must be empty.

    Assign all variables to this constraint."""

    def __init__(self, extra, row, col):
        super().__init__(extra)
        self._loc = (row, col)

    def __repr__(self):
        return f'CellEmpty({self._loc[0]}, {self._loc[1]})'

    @staticmethod
    def satisfied(_):
        """Preprocess is overridden, doesn't use _test_over_satis
        and it always fully applies the constraint: no test needed."""
        return True

    def preprocess(self):
        """Update the domain of the appropriate variable
        and the set the grid value."""

        self.remove_bparts([self.extra.var_dict[self._loc]])

        x, y = self._loc
        self.extra.grid[x][y] = BoatVals.WATER
        return True


class BoatEnd(BBoatCnstr):
    """A boat end must be at (row, col) and must continue in
    the specified direction.

    The preprocessor handles (row, col) aka self._loc
    Look up the names for the next 4 cells.
    The preporocessor can fill in UNK_PART in the 0th and possibly
    the 1st (there is water or an edge in the 2nd).
    Forward_check TODO

    Assign all variables to this constraint."""

    _nbr_cdirs = 4

    def __init__(self, extra, row, col, end):
        super().__init__(extra)
        self._loc = (row, col)
        self._end = end

        self._cd_names = []
        pname = self._loc
        for _ in range(self._nbr_cdirs):
            self._cd_names += [grids_bend_cont_cell(*pname, self._end)]
            pname = self._cd_names[-1]

    def __repr__(self):
        return f'BoatEnd({self._loc[0]}, {self._loc[1]}, {self._end})'

    @staticmethod
    def satisfied(_):
        """The preprocessor fully applies but doesn't always
        return True so that forward_check can be called."""
        return True

    def preprocess(self):
        """Preprocess the boat end constraint:
            1. Reduce my domain to _end
            2. Reduce the domain of the boundaries to water
            3. Check to see if we know it's a destroyer, adjust
            domains and the grid.

        Return True if we've fully marked a destroyer,
        otherwise return False so forward check can do more."""

        my_obj = self.extra.var_dict[self._loc]
        self.remove_to(my_obj, self._end)

        bounds = [self.extra.var_dict[loc]
                  for loc in grids_bound_end(*self._loc, self._end)]
        self.remove_bparts(bounds)

        cd_obj = self.extra.var_dict[self._cd_names[0]]
        cd0x, cd0y = self._cd_names[0]
        cd1x, cd1y = self._cd_names[1]

        if (cd1x not in range(SIZE) or cd1y not in range(SIZE)
            or self.extra.grid[cd1x][cd1y] == BoatVals.WATER):

            # one away from edge/water, make destoryer and done
            opp_end = self._end.opp_end()
            self.remove_to(cd_obj, opp_end)
            return True

        # mark as an unknown part, let forward_check do more
        if BoatVals.WATER in cd_obj.get_domain():
            cd_obj.remove_dom_val(BoatVals.WATER)
        if BoatVals.ROUND in cd_obj.get_domain():
            cd_obj.remove_dom_val(BoatVals.ROUND)
        self.extra.grid[cd0x][cd0y] = BoatVals.UNK_PART

        return False


    def forward_check(self, assignments):
        """Refine what the boat is as we learn more.

        If cd1 is off grid, the preprocessor handled everything
        and this wont be called.

        """
        #TODO return list of changed objects or True

        cd_obj = self.extra.var_dict[self._cd_names[0]]
        cd0x, cd0y = self._cd_names[0]
        cd1x, cd1y = self._cd_names[1]

        if (cd1x not in range(SIZE) or cd1y not in range(SIZE)
            or self.extra.grid[cd1x][cd1y] == BoatVals.WATER):

            # one away from edge/water, make destoryer and done
            opp_end = self._end.opp_end()
            self.extra.grid[cd0x][cd0y] = opp_end
            self.hide_to(cd_obj, opp_end)

            self.hide_diags_to_water(self._cd_names[0])

        # TODO this condition is wrong!  what are we doing??
        if (self.extra.grid[cd0x][cd0y] == BoatVals.MID and
            self.extra.grid[cd1x][cd1y] == BoatVals.WATER):

            opp_end = self._end.opp_end()
            cd1_obj = self.extra.var_dict[self._cd_names[1]]
            self.extra.grid[cd1x][cd1y] = opp_end
            if not self.hide_to(cd1_obj, opp_end):
                return False

            # TODO have we reduced the right stuff to water
            return self.hide_diags_to_water(self._cd_names[1])


        if self.extra.grid[cd1x][cd1y] == BoatVals.WATER:

            opp_end = self._end.opp_end()
            self.extra.grid[cd0x][cd0y] = opp_end
            return self.hide_to(cd_obj, opp_end)

        # if self.extra.grid[cd1x][cdy1] == BoatVals.MID:
        #     pass
            # TODO battleship

        return True


class BoatMid(BBoatCnstr):
    """A boat mid part must be at (row, col).

    Assign all variables to this constraint."""

    def __init__(self, extra, row, col):
        super().__init__(extra)
        self._loc = (row, col)

    def __repr__(self):
        return f'BoatMid({self._loc[0]}, {self._loc[1]})'

    @staticmethod
    def satisfied(_):
        """Test the constraint."""
        return True

    def preprocess(self):
        """Remove the diagonals from the domains of all the
        variables. Constraint is never fully applied here."""

        my_obj = self.extra.var_dict[self._loc]
        self.remove_to(my_obj, BoatVals.MID)

        diags = [self.extra.var_dict[loc] for loc in cell_diags(*self._loc)]
        self.remove_bparts(diags)

        return False

    # TODO write BoatMid.forward_check to refine what the boat is as we learn more
    # as soon as we know orientation can limit kcontinue part
    # to boat continue parts (not ROUND (sub))


class BoatSub(BBoatCnstr):
    """A submarine must be at (row, col). Remove all but ROUND from
    domain of own variable and all but WATER from bounding variables.

    Assign all variables to this constraint."""

    def __init__(self, extra, row, col):
        super().__init__(extra)
        self._loc = (row, col)

    def __repr__(self):
        return f'BoatSub({self._loc[0]}, {self._loc[1]})'

    @staticmethod
    def satisfied(_):
        """Preprocess is overridden, doesn't use _test_over_satis
        and it always fully applies the constraint: no test needed."""
        return True

    def preprocess(self):
        """Adjust domains to satify BoatSub."""

        my_obj = self.extra.var_dict[self._loc]
        self.remove_to(my_obj, BoatVals.ROUND)

        bounds = [self.extra.var_dict[loc] for loc in neigh_cells(*self._loc)]
        self.remove_bparts(bounds)

        return True


# %% var chooser

class BBoatChooser(var_chooser.MaxAssignedNeighs):
    """BBoat var choooser."""

    # pylint: disable=too-few-public-methods

    def choose(self, vobjs, prob_spec, assignments):
        """Select the next variable to set from vobjs."""

        for vobj in vobjs:
            if vobj.nbr_values() == 1:
                return vobj

        return super().choose(vobjs, prob_spec, assignments)


# TODO write a solver that assigns the whole boats at once
# i.e. multiple variables at once


# %%   read the file

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

BOATEND = {BOATTOP : BoatVals.END_TOP,
           BOATBOTTOM : BoatVals.END_BOT,
           BOATLEFT : BoatVals.END_LFT,
           BOATRIGHT : BoatVals.END_RGT
           }


def decode_to_constraints(extra, pairs):
    """Use as object_pairs_hook in json.loads
    because key names will not be unique."""

    cons = []

    for name, value in pairs:

        if name == ROWSUM:
            for row, rsum in enumerate(value):
                cons += [RowSum(extra, row + 1, rsum)]
            continue

        if name == COLSUM:
            for col, csum in enumerate(value):
                cons += [ColSum(extra, col + 1, csum)]
            continue

        con_class = BOAT_CNSTR[name]
        row, col = value

        if issubclass(con_class, BoatEnd):
            cons += [con_class(extra, row, col, BOATEND[name])]
        else:
            cons += [con_class(extra, row, col)]

    return cons

def read_puzzle(filename, extra):
    """Read the puzzle and return a BoatGrid."""

    with open(PUZ_PATH + filename, 'r', encoding='UTF-8') as file:
        lines = file.readlines()

    raw_data = ''.join(lines)

    if len(raw_data) > MAX_INPUT:
        return None

    return json.loads(raw_data,
                      object_pairs_hook=ft.partial(decode_to_constraints,
                                                   extra))


# %%

def add_basic(boatprob):
    """Add the variables and basic constraints (true for all puzzles)."""


    boatprob.var_chooser = BBoatChooser()
    boatprob.enable_forward_check()
    boatprob.add_variables(BOAT_VARS, BoatVals.assign_vals)

    extra = BBExtra(boatprob._spec.variables)
    boatprob.extra = extra

    boatprob.add_constraint(NbrParts(extra, NCELLS), BOAT_VARS)

    for vlist in diagonals():
        boatprob.add_constraint(NoOccedDiag(extra, vlist[0]), vlist)

    boatprob.add_constraint(BoatCounts(extra, [4, 3, 2, 1]), BOAT_VARS)

    return extra


def build_one(boatprob):
    """Battleship/Commodore problem from Games Magazine September 2019."""

    extra = add_basic(boatprob)

    # row/col sums
    rsums = [3, 1, 2, 1, 1, 2, 1, 1, 4, 4]
    for row, rsum in enumerate(rsums):
        rvars = [(row, y) for y in range(SIZE)]
        boatprob.add_constraint(RowSum(extra, row, rsum), rvars)

    csums = [5, 0, 2, 1, 2, 0, 2, 4, 1, 3]
    for col, csum in enumerate(csums):
        cvars = [(x, col) for x in range(SIZE)]
        boatprob.add_constraint(ColSum(extra, col, csum), cvars)

    # partial solutions:   boat start/end, middle, sub, or empty loc
    boatprob.add_constraint(CellEmpty(extra, 0, 9), BOAT_VARS)
    boatprob.add_constraint(BoatEnd(extra, 1, 0, BoatVals.END_BOT), BOAT_VARS)
    boatprob.add_constraint(BoatEnd(extra, 8, 6, BoatVals.END_TOP), BOAT_VARS)


def build_two(boatprob):
    """Battleship/Seaman problem from Games Magazine September 2019."""

    extra = add_basic(boatprob)

    cons = read_puzzle("seaman_sept2019.txt", extra)

    for con in cons:
        boatprob.add_constraint(con, BOATS)


def build_three(boatprob):
    """Battleship/Admiral problem from Games Magazine September 2019."""

    extra = add_basic(boatprob)

    cons = read_puzzle("admiral_sept2019.txt", extra)

    for con in cons:
        boatprob.add_constraint(con, BOATS)


def build_four(boatprob):
    """Battleship/Petty Officer problem from Games Magazine September 2019."""

    extra = add_basic(boatprob)

    cons = read_puzzle("p_officer_sept2019.txt", extra)

    for con in cons:
        boatprob.add_constraint(con, BOATS)


def build_five(boatprob):
    """Randomly generated build."""

    extra = add_basic(boatprob)

    cons = read_puzzle("test.txt", extra)

    for con in cons:
        boatprob.add_constraint(con, BOATS)


# %%  test constraints against correct answer

def test_answer(boatprob, correct):
    """Test the correct answer against the constraints."""

    boatprob.set_var_chooser(BBoatChooser())
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

    experimenter.do_stuff(builds,  print_grid)


if __name__ == '__test_example__':

    # for build in [build_two]:
    #     bprob = problem.Problem()
    #     build(bprob)
    #     sol = bprob.get_solution()
    #     if sol:
    #         print_grid(sol)
    #     else:
    #         print(build.__name__, "- no solutions.")

    skipped = True
    reason = 'Has errors and slow.'
