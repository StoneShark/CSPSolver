# -*- coding: utf-8 -*-
"""Battle boats:
    Place 10 boats of various lengths on a ten by ten grid.
    Boats may not touch, not even diagonally.
    Row and column sums count the number of boat parts in row/column.
    Partial placement is provided (see constraints below).

variables - boats
domains are locations that boats can be placed as tuples: (x, y, orientation)
Uses the extra data feature of the constraint engine:
    BBExtra(extra_data.ExtraDataIF)

Constraints:
    BBoatConstraint - base class for other constraints using extra data

    * PropagateBBoat

    These are all built on top of the bboat_cnstr contraint of the
    same name:

    * RowSum - puzzle specifies row sums
    * ColSum - puzzles specifies column sumes
    * CellEmpty - puzzle specifies an empty cell
    * BoatEnd - puzzle specifies a boat end part
                with opening up, down, left, right
    * BoatMid - puzzle specifies a boat mid part,
                boat may extend in either direction
    * BoatSub - puzzle specifies a submarine (boat length of 1)


Created on Fri May  5 03:40:16 2023
@author: Ann"""


# %% imports

import collections
import enum

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '../..')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import battleboats as bboat
import bboat_cnstr

from csp_solver import constraint as cnstr
from csp_solver import experimenter
from csp_solver import extra_data
from csp_solver import problem
from csp_solver import variable

# nicknames to shorten code (remember to send var object as first param)
HIDE_FUNC = variable.Variable.hide
REMOVE_FUNC = variable.Variable.remove_dom_val


# %%  enums

class EGrid(enum.Flag):
    """Values for the grid of the extra data.

    Done as flags so
        - WATER is always set even for BOUNDARIES.
        - Unassigned boat parts are clear (e.g. boat end from clues).
        - Unidentified boat parts are clear (cells known to have
        a boat part, but not what part)."""

    UNKNOWN = 0
    NONE = 0

    WATER = enum.auto()      # is water
    BOAT_PART = enum.auto()  # contains a boat part (either assigned or not)
    ASSIGNED = enum.auto()   # has been assigned with a full boat
    REDUCED = enum.auto()    # a domain var has been reduced for this cell

    # individual flag values -- but use the non-private ones below
    _BOUNDARY = enum.auto()
    _ROUND = enum.auto()
    _END_TOP = enum.auto()
    _END_BOT = enum.auto()
    _END_LFT = enum.auto()
    _END_RGT = enum.auto()
    _MID = enum.auto()

    BOUNDARY = _BOUNDARY | WATER

    ROUND = _ROUND | BOAT_PART
    END_TOP = _END_TOP | BOAT_PART
    END_BOT = _END_BOT | BOAT_PART
    END_LFT = _END_LFT | BOAT_PART
    END_RGT = _END_RGT | BOAT_PART
    MID = _MID | BOAT_PART


    if not __debug__:

        def __contains__(self, other):
            """Returns True if self has at least the same flags set as other.
            We don't need no stinking type checking!!!"""
            return other._value_ & self._value_ == other._value_

        def _get_value(self, flag):
            """Return the value.
            We don't need no stinking type checking!!!"""
            return flag._value_


    def ok_to_assign(self, what):
        """Is it ok to assign a boat part:
            1. have no value
            2. a domain has been reduced for this location for
               future assignment (i.e. now)
            3. are an unassigned boat part that matches what
            4. are a unidentified boat part"""

        return (not self
                or EGrid.REDUCED in self
                or (EGrid.ASSIGNED not in self
                    and EGrid.BOAT_PART in self
                    and what == self)
                or (self == EGrid.BOAT_PART
                    and EGrid.BOAT_PART in what))


    def no_new_parts(self):
        """Return True if a new part must not be assigned."""

        return EGrid.WATER in self or EGrid.ASSIGNED in self


    def char(self):
        """Return a char to print for self."""
        # pylint: disable=multiple-statements

        if EGrid._BOUNDARY in self:       rchar = '~'
        elif EGrid.WATER in self:         rchar = 'w'
        elif EGrid._ROUND in self:        rchar = 'o'
        elif EGrid._END_TOP in self:      rchar = '\u02c4'
        elif EGrid._END_BOT in self:      rchar = '\u02c5'
        elif EGrid._END_LFT in self:      rchar = '\u02c2'
        elif EGrid._END_RGT in self:      rchar = '\u02c3'
        elif EGrid._MID in self:          rchar = 'x'
        elif EGrid.BOAT_PART in self:     rchar = 'p'
        else:                             rchar = '.'

        return rchar


ENDS = [(EGrid.END_TOP, EGrid.END_BOT), (EGrid.END_LFT, EGrid.END_RGT)]

BPART_FROM_DIRECT = [EGrid.END_BOT,    # cont_dir == UP
                     EGrid.END_LFT,    # cont_dir == RIGHT
                     EGrid.END_TOP,    # cont_dir == DOWN
                     EGrid.END_RGT,    # cont_dir == LEFT
                     ]

OPP_END_FROM_DIRECT = [EGrid.END_TOP,    # cont_dir == UP
                       EGrid.END_RGT,    # cont_dir == RIGHT
                       EGrid.END_BOT,    # cont_dir == DOWN
                       EGrid.END_LFT,    # cont_dir == LEFT
                       ]

# %% extra data

class BBExtra(extra_data.ExtraDataIF):
    """A grid of the partial solution. It is updated
           1. by the preprocessing of constraints
           2. as extra_data when assignments are made in the solver
           3. by the forward_checking of constraints

    grid - stores the information that we know from clues; info that
    the current assignments imply (boat parts and boarders);
    and some data that we can infer, e.g. there's boat part but we don't
    know what type.

    row_sums, col_sums - row and column sums lists

    queue - a queue of tuples (vname, grid) where vname is the last variable
    that was assigned to make the grid."""

    def __init__(self):

        self.grid =  [[EGrid.UNKNOWN] * bboat.SIZE_P1
                      for _ in range(bboat.SIZE_P1)]
        self.row_sums = None
        self.col_sums = None

        self._queue = collections.deque()


    def __str__(self):
        """Return the grid string."""

        ostr = '     1  2  3  4  5  6  7  8  9 10\n'
        for x in range(1, bboat.SIZE_P1):

            rstr = f'{x:2}  '
            for y in range(1, bboat.SIZE_P1):
                rstr += ' ' + self.grid[x][y].char() + ' '
            ostr += rstr + '\n'

        return ostr


    def assign_grid(self, x, y, what):
        """Assign the EGrid value if it's ok and return True,
        else return False.

        This may be used by
          1. the preprocessor -- assignments are permanent.
          2. forward checks -- assignments will be popped along
             with
                a. any primary variable re-assignment, that is,
                   the updates are kept until the next
                   BBExtra.assign (that does a re-assignment)
                b. BBExtra.pop."""

        if self.grid[x][y] == what:
            return True

        if self.grid[x][y].ok_to_assign(what):
            self.grid[x][y] = what
            return True

        return False


    @staticmethod
    def _show(grid):
        """Return the grid string."""

        ostr = '     1  2  3  4  5  6  7  8  9 10\n'
        for x in range(1, bboat.SIZE_P1):

            rstr = f'{x:2}  '
            for y in range(1, bboat.SIZE_P1):
                rstr += ' ' + grid[x][y].char() + ' '
            ostr += rstr + '\n'

        return ostr


    @staticmethod
    def assign_bpart(grid, x, y, part, flags=EGrid.NONE):
        """Assign the boat part and boundary if it's ok and return True,
        else return False.
        grid might be self.grid or a temporary grid.
        Don't overwrite water cells with boundary cells."""

        if part == EGrid.BOUNDARY and EGrid.WATER in grid[x][y]:
            return True

        if grid[x][y].ok_to_assign(part):
            grid[x][y] = part | flags
            if EGrid.ASSIGNED in flags:
                grid[x][y] &= ~EGrid.REDUCED
            return True

        return False


    @staticmethod
    def place_boat(grid, loc, length, flags=EGrid.NONE):
        """Place the boat and fill the boundary.
        grid might be self.grid or a temporary grid.
        Return True if placed ok, False otherwise."""

        x, y, orient = loc

        if length == 1:
            if not BBExtra.assign_bpart(grid, x, y, EGrid.ROUND, flags=flags):
                return False
            for tx, ty in bboat.grids_bounding(x, y, orient, length):
                if not BBExtra.assign_bpart(grid, tx, ty, EGrid.BOUNDARY):
                    return False
            return True

        dx, dy = bboat.INCS[orient]
        ul_end, lr_end = ENDS[orient]

        if not BBExtra.assign_bpart(grid, x, y, ul_end, flags=flags):
            return False

        for i in range(1, length - 1):
            if not BBExtra.assign_bpart(grid,
                                        x + i * dx, y + i * dy,
                                        EGrid.MID, flags=flags):
                return False

        i = length - 1
        if not BBExtra.assign_bpart(grid,
                                    x + i * dx, y + i * dy,
                                    lr_end, flags=flags):
            return False

        for tx, ty in bboat.grids_bounding(x, y, orient, length):
            if not BBExtra.assign_bpart(grid, tx, ty, EGrid.BOUNDARY):
                return False
        return True


    def assign(self, vname, val):
        """Update the grid with the boat (vname) assigned to
        location (val=(x, y, orient)).
        The assignment might be a change of values for one
        variable, so if the top of the queue has the same
        variable then pop and try to reassign a new value.
        Update a copy of the grid in case an error is found.

        If a conflict is detected return False, otherwise True."""

        if self._queue and vname == self._queue[-1][0]:
            self.pop()

        length = bboat.BOAT_LENGTH[vname]
        temp_grid = [row.copy() for row in self.grid]

        if not self.place_boat(temp_grid, val, length, flags=EGrid.ASSIGNED):
            return False

        self._queue.append((vname, self.grid))
        self.grid = temp_grid

        return True


    def pop(self):
        """Undo the last assignment."""

        _, self.grid = self._queue.pop()


# %% constraints

class BBoatConstraint(cnstr.Constraint):
    """Common handling of extra data.
    This is mixed with constraints from bboat_cnstr, don't
    define methods that will confuse the MRO."""

    def __init__(self, *args):

        super().__init__(*args)
        self.extra = None


    def set_extra(self, extra):
        """Save the extra data."""
        self.extra = extra


    def reduce_to(self, boat_loc, boat_len,
                  func=REMOVE_FUNC,  assignments=None):
        """Reduce one of the boat domains to boat_loc;
        the selected boat must be boat_len long.

        This MUST be called before the grid cells are set to REDUCED!

        Call with func as one of:
          variable.Variable.remove_dom_val for preprocessor
          variable.Variable.hide for forward_check

        Default parameters are set for preprocessor.

        Return False if a domain is eliminated,
        otherwise return True."""

        x, y, _ = boat_loc

        for bobj in self._vobjs:
            length = bboat.BOAT_LENGTH[bobj.name]

            if ((assignments and bobj.name in assignments)
                    or length != boat_len
                    or EGrid.REDUCED in self.extra.grid[x][y]
                    or bobj.nbr_values() <= 1
                    or boat_loc not in bobj.get_domain()):
                continue
            # print(f"{self} reducing domain for {bobj.name} to {boat_loc}")

            for value in bobj.get_domain()[:]:
                if value == boat_loc:
                    continue

                if not func(bobj, value):
                    return False
            return True

        return True


    def set_reduced(self, boat_loc, boat_len):
        """Set the grid cells for a boat of length boat_len
        at boat_loc to REDUCED. boat_loc is always the
        upper-left end of the boat.

        This must be done after reduce_to is called."""

        for x, y in bboat.grids_occed(*boat_loc, boat_len):

            if 0 < x < bboat.SIZE_P1 and 0 < y < bboat.SIZE_P1:
                self.extra.grid[x][y] |= EGrid.REDUCED


    def check_the_sum(self, sidx, usum, orient, assignments):
        """For a given row (orient = HORZ) or a column (orient = VERT)
        adjust the grid based on assigned boats and the unit sum (usum).

        Algorithm:
            1. count the occupied cells
               and collect the open cells' coordinates
            2. if the occupied cells equals the unit sum,
               fill the collected open cells with water
            3. if open cells plus the occupied cells
               (not water cells) equals the unit sum,
               mark all open cells as unidentified
               boat parts.

        sidx is the index of the row or column being
             check (static index; vidx is variable index)

        Call only from forward_check.

        Return False as soon as we know the row/sum constraint
        cannot be met, otherwise return True.
        """

        open_cells = set()
        cur_sum = 0

        for vidx in range(1, bboat.SIZE_P1):

            x, y = (vidx, sidx) if orient == bboat.VERT else (sidx, vidx)
            cell_val = self.extra.grid[x][y]

            if not cell_val:
                open_cells |= {(x, y)}

            elif EGrid.BOAT_PART in cell_val:
                cur_sum += 1

            if cur_sum > usum:
                return False

        if cur_sum == usum:
            for x, y in open_cells:
                if not self.extra.assign_grid(x, y, EGrid.WATER):
                    return False

            unassigned = [vobj for vobj in self._vobjs
                          if vobj.name not in assignments]
            return bboat.empty_cells(open_cells,
                                     unassigned,
                                     variable.Variable.hide)

        if cur_sum + len(open_cells) == usum:
            for x, y in open_cells:
                if not self.extra.assign_grid(x, y, EGrid.BOAT_PART):
                    return False

        return True


    def boat_scan(self, sidx, orient, assignments):
        """Scan for boats in either a row (orient = HORZ)
        or a column (orient = VERT). This is done but
        find runs of unreduced and unassigned boat_parts.

        Cannot place subs here because a run of 1
        could be a crossing boat.

        sidx is the index of the row or column being
             scanned (static index)

        Call only from forward_check.

        Return False as soon as we know the row/sum constraint
        cannot be met, otherwise return True.
        """

        blen = 0
        bstart = None
        for vidx in range(1, bboat.SIZE_P1):

            x, y = (vidx, sidx) if orient == bboat.VERT else (sidx, vidx)
            cell_val = self.extra.grid[x][y]

            if (EGrid.BOAT_PART in cell_val
                    and EGrid.REDUCED not in cell_val
                    and EGrid.ASSIGNED not in cell_val):
                if not blen:
                    bstart = (x, y, orient)
                blen += 1

            elif blen > 1:
                if not self.reduce_to(bstart, blen, HIDE_FUNC, assignments):
                    return False
                self.set_reduced(bstart, blen)
                blen = 0

            else:
                blen = 0

        return True


class PropagateBBoat(BBoatConstraint):
    """Propagate what we know about the bboat grid.
    Extra_data cannot adjust variable domains,
    the forward_check here does that."""

    def satisfied(self, boat_dict):
        """Checked by BBExtra, return True."""

        _ = boat_dict
        return True


    def forward_check(self, assignments):
        """Hide all values that are in the boundary or already
        occupied."""

        # TODO expand PropagateBBoat

        hide_set = {(x, y) for x in range(1, bboat.SIZE_P1)
                    for y in range(1, bboat.SIZE_P1)
                    if self.extra.grid[x][y].no_new_parts()}

        unassigned= [vobj for vobj in self._vobjs
                      if vobj.name not in assignments]

        rval = bboat.empty_cells(hide_set,
                                 unassigned,
                                 variable.Variable.hide)

        return rval


class RowSum(BBoatConstraint, bboat_cnstr.RowSum):
    """The number of boats parts in row is <= rsum until all variables
    are boat locations then they must be equal."""

    def satisfied(self, boat_dict):
        """Test the constraint."""

        cur_sum = sum(1 for part in self.extra.grid[self._row]
                      if EGrid.BOAT_PART in part)

        if len(boat_dict) == bboat.B_CNT:
            return cur_sum == self._row_sum

        return cur_sum <= self._row_sum


    def preprocess(self):
        """Preprocess row sum the constraint: base constraint
        does everything except update the grid."""

        rval = super().preprocess()

        if not self._row_sum:
            for y in range(1, bboat.SIZE_P1):
                if not self.extra.assign_grid(self._row, y, EGrid.WATER):
                    raise cnstr.PreprocessorConflict(str(self))

        return rval


    def forward_check(self, assignments):
        """If the row sum is exactly satisfied; make certain that
        there are not any boats crossing row.
        If the row sum and empty sum equals required sum, put generic
        boat parts in the grid.

        Return - False if any domain has been eliminated or the
        constraint can't be met, True otherwise."""

        if not self.check_the_sum(self._row, self._row_sum,
                                  bboat.HORZ, assignments):
            return False

        return self.boat_scan(self._row, bboat.HORZ, assignments)


class ColSum(BBoatConstraint, bboat_cnstr.ColSum):
    """The number of boats parts in clm is <= csum until all variables
    are boat locations then they must be equal."""

    def satisfied(self, boat_dict):
        """Test the constraint."""

        cur_sum = sum(1 for x in range(1, bboat.SIZE_P1)
                      if EGrid.BOAT_PART in self.extra.grid[x][self._col])

        if len(boat_dict) == bboat.B_CNT:
            return cur_sum == self._col_sum

        return cur_sum <= self._col_sum


    def preprocess(self):
        """Preprocess col sum the constraint: base constraint
        does everything except update the grid."""

        rval = super().preprocess()

        if not self._col_sum:
            for x in range(1, bboat.SIZE_P1):
                if not self.extra.assign_grid(x, self._col, EGrid.WATER):
                    raise cnstr.PreprocessorConflict(str(self))

        return rval


    def forward_check(self, assignments):
        """If the col sum is exactly satisfied; make certain that
        there are not any boats crossing col.
        If the col sum and empty sum equals required sum, put generic
        boat parts in the grid.

        Return - False if any domain has been eliminated or the
        constraint can't be met, True otherwise."""

        if not self.check_the_sum(self._col, self._col_sum,
                                  bboat.VERT, assignments):
            return False

        return self.boat_scan(self._col, bboat.VERT, assignments)


class CellEmpty(BBoatConstraint, bboat_cnstr.CellEmpty):
    """The cell at row, col must be empty."""

    def preprocess(self):
        """Remove any domain values (start locations) that
        would include (row, col). Contraint will be fully satisfied."""

        super().preprocess()

        if not self.extra.assign_grid(*self._loc, EGrid.WATER):
            raise cnstr.PreprocessorConflict(str(self))

        return True


class BoatEnd(BBoatConstraint, bboat_cnstr.BoatEnd):
    """A boat must end at (row, col) and continue in the direction of
    cont_dir.

    This constraint prohibits submarines from being at (row, col),
    return False if a sub is assigned to (row, col).

    If not, True is returned anyway; until all boats are assigned."""

    def _update_grid(self, empties):
        """Update the grid with the BoatEnd constraint info.
        Put water in the bounding cells and an UNKnown PART
        in the CONTinue DIRection.

        Call only from preprocessor!"""

        for x, y in empties:
            if not self.extra.assign_grid(x, y, EGrid.WATER):
                raise cnstr.PreprocessorConflict(str(self))

        cx, cy = bboat.cont_pos(self._loc, self._cont_dir)
        x, y = self._loc
        bpart = BPART_FROM_DIRECT[self._cont_dir]

        if not self.extra.assign_grid(x, y, bpart):
            raise cnstr.PreprocessorConflict(str(self))

        if not self.extra.assign_grid(cx, cy, EGrid.BOAT_PART):
            raise cnstr.PreprocessorConflict(str(self))


    def _deduce_boat(self):
        """If there is an opposite end 1, 2 or 3 cells
        from the open end; we can place a boat.

        Placing a boat means filling the grid and
        reducing the domain of one variable to the
        assignment location.

        Call only from preprocessor!

        If we place a boat without conflict the contraint
        is fully processed, return True!"""

        x, y = self._loc
        if EGrid.REDUCED in self.extra.grid[x][y]:
            return True

        dx, dy = bboat.CONT_INCS[self._cont_dir]
        opp_end = OPP_END_FROM_DIRECT[self._cont_dir]

        for delta in (1, 2, 3):
            end_x = x + delta * dx
            end_y = y + delta * dy
            if (0 < end_x < bboat.SIZE_P1
                    and 0 < end_y < bboat.SIZE_P1
                    and opp_end in self.extra.grid[end_x][end_y]):
                break
        else:
            # if there is a mid part 1 away from the end we have a battleship
            # adjust the vars to place it
            # this will only be caught if the mid constraint was preproc'ed 1st
            mid_x = x + 2 * dx
            mid_y = y + 2 * dy
            if (0 < mid_x < bboat.SIZE_P1
                    and 0 < mid_y < bboat.SIZE_P1
                    and EGrid.MID in self.extra.grid[mid_x][mid_y]):
                delta = 3
                end_x = x + delta * dx
                end_y = y + delta * dy
            else:
                # can't deduce the boat type
                return False

        boat_loc = bboat.assign_loc(x, y, end_x, end_y)
        boat_val =(*boat_loc, bboat.CONT_ORIENT[self._cont_dir])
        boat_len = delta + 1
        # print(f"{self}: Deduced boat {boat_len} at {boat_val}.")

        if not self.reduce_to(boat_val, boat_len):
            raise cnstr.PreprocessConflict(str(self))

        if not self.extra.place_boat(self.extra.grid, boat_val, boat_len,
                                     flags=EGrid.REDUCED):
            raise cnstr.PreprocessConflict(str(self))
        return True


    def preprocess(self):
        """Let the base constraint update the variable domains.
        Update the grid and see if have a full position."""

        super().preprocess()

        rval = False
        empties = bboat.grids_bound_end(*self._loc, self._cont_dir)
        self._update_grid(empties)

        rval = self._deduce_boat()

        return rval


    def _destroyer_end(self, assignments):
        """Check for a destroyer at _loc based on water being two
        away from open end.
        There is no boat assigned at _loc.

        Return False if a variable is overconstrained,
        otherwise, return True."""

        # TODO this might never run, the preprocessor places
        # the end and sets an unidentied boat part on the open end; then
        # RowSum/ColSum will forward_check will place the boat.

        x, y = self._loc

        dx, dy = bboat.CONT_INCS[self._cont_dir]
        cx, cy =  bboat.cont_pos(self._loc, self._cont_dir)

        #  checking boat dir first, assures computed loc is on grid
        if (self._cont_dir == bboat.LEFT
                and EGrid.WATER in self.extra.grid[x + 2 * dx][y]):
            destroyer_loc = (x , y, bboat.HORZ)

        elif (self._cont_dir == bboat.RIGHT
                and EGrid.WATER in self.extra.grid[x + 2 * dx][y]):
            destroyer_loc = (cx , y, bboat.HORZ)

        elif (self._cont_dir == bboat.UP
                  and EGrid.WATER in self.extra.grid[x][y + 2 * dy]):
            destroyer_loc = (x, cy, bboat.VERT)

        elif (self._cont_dir == bboat.DOWN
                  and EGrid.WATER in self.extra.grid[x][y + 2 * dy]):
            destroyer_loc = (x, y, bboat.VERT)

        else:
            return True

        # print("BoatEnd reducing domain")
        if not self.reduce_to(destroyer_loc, 2, HIDE_FUNC, assignments):
            return False
        self.extra.grid[x][y] |= EGrid.REDUCED
        self.extra.grid[cx][cy] |= EGrid.REDUCED

        return True


    def forward_check(self, assignments):
        """Forward check for boat ends:

        If there is water cell one away from the open end,
        we have a destoryer location.

        if a boat end, is not on 'edge' of water cells
        (see grid bounds ends)
        """
        # TODO BoatEnd.forward_check what is that 2nd condition

        x, y = self._loc
        if (EGrid.ASSIGNED in self.extra.grid[x][y]
                or EGrid.REDUCED in self.extra.grid[x][y]):
            return True

        rval = self._destroyer_end(assignments)

        return rval

class BoatMid(BBoatConstraint, bboat_cnstr.BoatMid):
    """A boat mid part must be at (row, col).

    This constraint prohibits submarines and destroyers from
    using any cell in (row, col) and it's neighbors.

    If not, True is returned anyway; until all boats are assigned."""

    def preprocess(self):
        """Use the base constraint to update the variables
        then update the grid."""

        super().preprocess()

        # TODO should we be recording which type of empties
        # e.g. if only diagnols it can be refined, but if
        # was on an edge and 5 values -- can't be refined

        for x, y in bboat.grids_bound_mid(*self._loc):
            if (0 < x < bboat.SIZE_P1 and 0 < y < bboat.SIZE_P1
                    and not self.extra.assign_grid(x, y, EGrid.WATER)):
                raise cnstr.PreprocessorConflict(str(self))

        if not self.extra.assign_grid(*self._loc, EGrid.MID):
            raise cnstr.PreprocessorConflict(str(self))

        # TODO if there is a mid part 1 away from an end we have a battleship

        return False


    # TODO write BoatMid.forward_check
    # place BOAT_PART s when we know where they should go
    # if battleship is assigned then a mid must be a cruiser


class BoatSub(BBoatConstraint, bboat_cnstr.BoatSub):
    """A submarine must be at (row, col).

    For any boat longer than a submarine, if it occupies (row, col)
    return False.

    If all 4 subs are assigned but none at (row, col) return False,
    otherwise True."""

    def preprocess(self):
        """Use the base constraint to update the boat variable
        domains then update grid."""

        super().preprocess()

        for x, y in bboat.grid_neighs(*self._loc):
            if (0 < x < bboat.SIZE_P1
                    and 0 < y < bboat.SIZE_P1
                    and not self.extra.assign_grid(x, y, EGrid.WATER)):
                raise cnstr.PreprocessorConflict(str(self))

        if not self.extra.assign_grid(*self._loc, EGrid.ROUND):
            raise cnstr.PreprocessorConflict(str(self))

        return True


# %%  load and define puzzles

# these refer to the contraints in this file not bboat_cnstr
BOAT_CNSTR = {bboat.ROWSUM: RowSum,
              bboat.COLSUM: ColSum,
              bboat.EMPTYCELL: CellEmpty,
              bboat.SUMBARINE: BoatSub,
              bboat.BOATTOP: BoatEnd,
              bboat.BOATBOTTOM: BoatEnd,
              bboat.BOATLEFT: BoatEnd,
              bboat.BOATRIGHT: BoatEnd,
              bboat.BOATMID: BoatMid
              }


def build_puzzle(filename):
    """Return a function that can build boat a problem
    based on an input file."""

    pairs = bboat.read_puzzle(bboat.PUZ_PATH + filename)
    if not pairs:
        return None

    row_sums_value = col_sums_value = None
    for key, value in pairs:
        if key == bboat.ROWSUM:
            row_sums_value = value
        elif key == bboat.COLSUM:
            col_sums_value = value
    if not row_sums_value or not col_sums_value:
        raise cnstr.ConstraintError("Row and Col sums are required")

    doc_str = filename + ':  \n' \
                + '\n'.join(str(c) + '=' + str(v) for c, v in pairs)

    def build_func(boatprob):
        """place holder
        vars from outer scope used:
            row_sums_value, col_sums_value, pairs,
            filename and doc_str"""

        bboat_cnstr.add_basic(boatprob, PropagateBBoat)

        boatprob.extra_data = BBExtra()
        boatprob.extra_data.row_sums = row_sums_value
        boatprob.extra_data.col_sums = col_sums_value

        cons = bboat_cnstr.build_cons(pairs, BOAT_CNSTR)
        for con in cons:
            boatprob.add_constraint(con, bboat.BOATS)
        for con in boatprob.pspec.constraints:
            con.set_extra(boatprob.extra_data)

        bboat_cnstr.add_final(boatprob, uset_cnstr=True)

    build_func.__name__ = f'build_puzzle("{filename}")'
    build_func.__doc__ = doc_str

    return build_func


def build_all_puzzles():
    """Create a list of build functions for the files in
    the puzzle directory."""

    build_funcs = []
    files = sorted(os.listdir(bboat.PUZ_PATH))

    for filename in files:
        func = build_puzzle(filename)
        if func:
            build_funcs += [func]

    return build_funcs


# %%   main

builds = build_all_puzzles()

if __name__ == '__main__':

    experimenter.do_stuff(builds, bboat.print_grid)


if __name__ == '__test_example__':

    # run_slow is defined in the global dict passed to runpy.run_path
    # access through globals so we don't get a syntax error

    if not globals()['run_slow']:
        # pick a small representative set
        builds = [build_puzzle("admiral_sept2019.txt"),
                  build_puzzle("commodore_sept2019.txt"),
                  build_puzzle("seaman_sept2019.txt"),
                  build_puzzle("test.txt"),
                  build_puzzle("test_prep.txt")]

    for build in builds:
        print(f'\nSolving build {build.__name__}:\n', build.__doc__)
        bprob = problem.Problem()
        build(bprob)
        sol = bprob.get_solution()
        bboat.print_grid(sol)


# build = build_puzzle("commodore_aug2021.txt")

# bprob = problem.Problem()
# build(bprob)

# bprob._spec.prepare_variables()
# bprob.print_domains()

# print()
# for name, vobj in bprob.pspec.variables.items():
#     print(name, len(vobj.get_domain()))

# sol = bprob.get_all_solutions()
# bboat.print_grid(sol[0])
