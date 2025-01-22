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

python -O bboat_timer.py --extra --runs 20:  0.0539

Note:  x is used for the row number and y is used for
the column number both 1..10.

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

from csp_solver import constraint as cnstr
from csp_solver import experimenter
from csp_solver import extra_data
from csp_solver import problem
from csp_solver import variable

import battleboats as bboat
import bboat_cnstr

# nicknames to shorten code (remember to send var object as first param)
HIDE_FUNC = variable.Variable.hide
REMOVE_FUNC = variable.Variable.remove_dom_val


# %%  enums

class EGrid(enum.Flag):
    """Values for the grid of the extra data.

    Done as flags so
        - WATER is always set even for BOUNDARIES.
        - Unassigned boat parts are clear (e.g. boat end from clues).
        - Reduced boat parts are clear (i.e. we've identified the
          location of a boat and reduced it's variable to that
          domain value, but the solver has not yet assigned it').
          This is used to keep us from reducing more than one
          domain value to the same location.
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

    RA_MASK = ASSIGNED | REDUCED
    ENDS_MASK = _END_TOP | _END_BOT | _END_LFT | _END_RGT
    KNOWN_MASK = WATER | _ROUND | _MID | ENDS_MASK



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
            4. are a unidentified boat part and are
               assigning a known boat part"""

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


ENDS_FROM_ORIENT = [(EGrid.END_TOP, EGrid.END_BOT),
                    (EGrid.END_LFT, EGrid.END_RGT)]

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


CONT_DIR_FROM_END = {EGrid.END_TOP: bboat.DOWN,
                     EGrid.END_BOT: bboat.UP,
                     EGrid.END_RGT: bboat.LEFT,
                     EGrid.END_LFT: bboat.RIGHT}


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
            if self.row_sums:
                rstr += f'{self.row_sums[x - 1]:2}'
            ostr += rstr + '\n'

        ostr += '\n'
        if self.col_sums:
            rstr = '   '
            for csum in self.col_sums:
                rstr += f'{csum:3}'
            ostr += rstr + '\n'

        return ostr


    def assign_grid(self, x, y, what):
        """Assign the EGrid value if it's ok and return True,
        else return False.

        Don't change anything if assigning:
          1. BOUNDARY to WATER (or BOUNDARY)
          2. BOAT_PART to BOAT_PART
          3. to a cell that is already identified as what,
             i.e. don't change the flags

        This may be used by
          1. the preprocessor -- assignments are permanent.
          2. forward checks -- assignments will be popped along
             with
                a. any primary variable re-assignment, that is,
                   the updates are kept until the next
                   BBExtra.assign that does a re-assignment
                b. BBExtra.pop."""

        cell_val = self.grid[x][y]
        if ((what == EGrid.BOUNDARY and EGrid.WATER in cell_val)
                or (what == EGrid.BOAT_PART and EGrid.BOAT_PART in cell_val)
                or cell_val & EGrid.KNOWN_MASK == what):
            return True

        if self.grid[x][y].ok_to_assign(what):
            self.grid[x][y] |= what
            return True

        return False


    @staticmethod
    def assign_bpart(grid, x, y, part, flags=EGrid.NONE):
        """Assign the boat part and boundary if it's ok and return True,
        else return False.
        grid might be self.grid or a temporary grid.
        Don't overwrite water cells with boundary cells.
        If setting the ASSIGNED flag, clear the REDUCED flag."""

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
        ul_end, lr_end = ENDS_FROM_ORIENT[orient]

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


    def set_reduced(self, boat_loc, boat_len):
        """Set the grid cells for a boat of length boat_len
        at boat_loc to REDUCED."""

        for x, y in bboat.grids_occed(*boat_loc, boat_len):
            self.grid[x][y] |= EGrid.REDUCED | EGrid.BOAT_PART


    def empty_cells(self, empty_set, vobjs_list, func):
        """Call empty_cells, but then set reduced if any domains were
        reduced to 1. Don't do extra work if a domain was reduced to 0."""

        if not bboat.empty_cells(empty_set, vobjs_list, func):
            return False

        for bobj in vobjs_list:
            dom = bobj.get_domain()
            bstart = dom[0]
            cell_val = self.grid[bstart[0]][bstart[1]]
            if (len(dom) == 1
                    and EGrid.REDUCED not in cell_val
                    and EGrid.ASSIGNED not in cell_val):

                # print(f"Setting reduced for {bobj.name}")
                self.set_reduced(bstart, bboat.BOAT_LENGTH[bobj.name])

        return True


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
        """Reduce one boat domain to boat_loc;
        the selected boat must be boat_len long.

        Call with func as one of:
          variable.Variable.remove_dom_val for preprocessor
          variable.Variable.hide for forward_check

        Default parameters are set for preprocessor.

        Return False if a domain is eliminated,
        otherwise return True."""

        x, y, _ = boat_loc
        assert not EGrid.RA_MASK & self.extra.grid[x][y]
        assert EGrid.MID not in self.extra.grid[x][y]

        for bobj in self._vobjs:
            length = bboat.BOAT_LENGTH[bobj.name]

            if not ((assignments and bobj.name in assignments)
                        or length != boat_len
                        or EGrid.REDUCED in self.extra.grid[x][y]
                        or bobj.nbr_values() <= 1
                        or boat_loc not in bobj.get_domain()):
                # print(f"{self} reducing domain for {bobj.name} to {boat_loc}")
                break

        else:
            # if we can't place a boat, the current assignments wont work
            # print(f"Reduce_to didn't find boat {self}")
            return False

        for value in bobj.get_domain_copy():
            if value != boat_loc and not func(bobj, value):
                return False

        self.extra.set_reduced(boat_loc, boat_len)
        return True


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

            return self.extra.empty_cells(open_cells,
                                          unassigned,
                                          variable.Variable.hide)

        if cur_sum + len(open_cells) == usum:
            for x, y in open_cells:
                if not self.extra.assign_grid(x, y, EGrid.BOAT_PART):
                    return False

        return True


    def boat_scan(self, sidx, orient, assignments):
        """Scan for boats in either a row (orient = HORZ)
        or a column (orient = VERT). This is done by
        finding runs of unreduced and unassigned boat_parts.

        Cannot place subs here because a run of 1
        could be a crossing boat.

        sidx is the index of the row or column being
             scanned (static index, vidx is variable index)

        Call only from forward_check (or rewrite to pass
        in variable operation hide or remove).

        Return False as soon as we know the row/sum constraint
        cannot be met, otherwise return True.
        """

        blen = 0
        bstart = None
        prev = EGrid.WATER

        for vidx in range(1, bboat.SIZE_P1):

            x, y = (vidx, sidx) if orient == bboat.VERT else (sidx, vidx)
            cell_val = self.extra.grid[x][y]

            if (EGrid.BOAT_PART in cell_val
                    and EGrid.REDUCED not in cell_val
                    and EGrid.ASSIGNED not in cell_val):
                if blen:
                    blen += 1
                elif EGrid.WATER in prev and EGrid.MID not in cell_val:
                    bstart = (x, y, orient)
                    blen = 1

            elif blen > 1 and EGrid.WATER in cell_val:
                if not self.reduce_to(bstart, blen, HIDE_FUNC, assignments):
                    return False
                blen = 0

            else:
                blen = 0
            prev = cell_val

        if blen > 1 and EGrid.BOAT_PART in cell_val:
            if not self.reduce_to(bstart, blen, HIDE_FUNC, assignments):
                return False

        return True


class PropagateBBoat(BBoatConstraint):
    """Propagate what we know about the bboat grid.
    Extra_data cannot adjust variable domains,
    the forward_check here does that.
    It also does some propagation from the grid to new
    domain reductions, that don't make sense anyplace else."""

    def satisfied(self, boat_dict):
        """Checked by BBExtra, return True."""
        # pylint: disable=no-self-use

        _ = boat_dict
        return True


    def forward_check(self, assignments):
        """Hide all values that are in boat boundariers or
        already occupied.

        This is the first constraint, so the call to
        extra.empty_cells will catch any domains reduced to 1
        by the preprocessor methods."""

        # make the domains match the extra data
        hide_set = {(x, y) for x in range(1, bboat.SIZE_P1)
                    for y in range(1, bboat.SIZE_P1)
                    if self.extra.grid[x][y].no_new_parts()}

        unassigned= [vobj for vobj in self._vobjs
                      if vobj.name not in assignments]

        rval = self.extra.empty_cells(hide_set,
                                      unassigned,
                                      variable.Variable.hide)

        # unidentified BOAT_PARTs surrounded by water are subs
        for x in range(1, bboat.SIZE_P1):
            for y in range(1, bboat.SIZE_P1):

                if (self.extra.grid[x][y] == EGrid.BOAT_PART

                        and all(EGrid.WATER in self.extra.grid[tx][ty]
                                    for tx, ty in bboat.grid_neighs(x, y)
                                    if (0 < tx < bboat.SIZE_P1
                                        and 0 < ty < bboat.SIZE_P1))

                        and not self.reduce_to((x, y, bboat.VERT), 1,
                                               HIDE_FUNC, assignments)):
                    return False

        # XXXX unidentified boat parts that are bound by water and 1 bpart,
        #  are ends (watch for errors on corners) - time saved likely not good

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
            raise cnstr.PreprocessorConflict(str(self))

        if not self.extra.place_boat(self.extra.grid, boat_val, boat_len,
                                     flags=EGrid.REDUCED):
            raise cnstr.PreprocessConflict(str(self))
        return True


    def preprocess(self):
        """Let the base constraint update the variable domains.
        Update the grid with the known water cells.
        If base constraint placed a boat, mark it as reduced.
        Otherwise, scan for another end (or mid) to see if have a
        known boat location."""

        rval = super().preprocess()

        empties = bboat.grids_bound_end(*self._loc, self._cont_dir)
        self._update_grid(empties)

        if rval:
            boat_val = self._check_destroyer()
            self.extra.set_reduced(boat_val, 2)
            return True

        rval = self._deduce_boat()

        return rval

    #  No need for BoatEnd.forward_check:

    #  The preprocessor places the end and sets an unidentified
    #  boat part on the open end,
    #  then RowSum/ColSum.forward_check -> boat_scan
    #  will place the boat as soon as it is limited,
    #  thus no need for extra testing

    # BoatEnd.forward_check is in the git history, coverage
    # testing showed that it never placed a boat


class BoatMid(BBoatConstraint, bboat_cnstr.BoatMid):
    """A boat mid part must be at (row, col).

    This constraint prohibits submarines and destroyers from
    using any cell in (row, col) and it's neighbors.

    If not, True is returned anyway; until all boats are assigned."""


    def __init__(self, row, col):
        super().__init__(row, col)
        self._orient = None


    def _bs_mid_open_end(self):
        """Test to see if there is a BOAT END one away from
        this mid part, if so we have a battleship location"""

        x, y = self._loc

        for dx, dy in bboat.CONT_INCS:

            end_x = x + 2 * dx
            end_y = y + 2 * dy
            if not (0 < end_x < bboat.SIZE_P1 and 0 < end_y < bboat.SIZE_P1):
                continue

            part = self.extra.grid[end_x][end_y]
            if not EGrid.ENDS_MASK & part:  # not an end part
                continue

            cont_dir = CONT_DIR_FROM_END[part & ~EGrid.RA_MASK]

            # make certain that the part is facing us
            if ((cont_dir == bboat.LEFT and x < end_x)
                     or (cont_dir == bboat.UP and y < end_y)):

                # need to compute the boat location (it's the other end)
                end_x = x + 4 * dx
                end_y = y + 4 * dy
                break

            if ((cont_dir == bboat.RIGHT and end_x < x)
                    or (cont_dir == bboat.DOWN and end_y < y)):
                break
        else:
            return None

        self._orient =  bboat.CONT_ORIENT[cont_dir]
        return end_x, end_y, self._orient


    def _bs_mid_mid(self):
        """Test to see if there is a BOAT MID next to
        this mid part, if so we have a battleship location"""

        x, y = self._loc

        for dx, dy in bboat.CONT_INCS:

            m2_x = x + dx
            m2_y = y + dy

            if (not (0 < m2_x < bboat.SIZE_P1 and 0 < m2_y < bboat.SIZE_P1)
                    or EGrid.MID not in self.extra.grid[m2_x][m2_y]):
                continue

            if dx == -1:
                self._orient = bboat.VERT
                end_x = x - 2
                end_y = y

            elif dx == 1:
                self._orient = bboat.VERT
                end_x = x - 1
                end_y = y

            elif dy == -1:
                self._orient = bboat.HORZ
                end_x = x
                end_y = y - 2

            elif dy == 1:
                self._orient = bboat.HORZ
                end_x = x
                end_y = y - 1
            break

        else:
            return None

        return end_x, end_y, self._orient


    def _check_battleship(self):
        """Two patterns with a tell us we know the battleship
        location:
              end open mid
              mid mid
        check if we have either, if so reduce the boat."""

        bs_loc = self._bs_mid_open_end()
        if bs_loc is None:
            bs_loc = self._bs_mid_mid()

        if bs_loc and not self.reduce_to(bs_loc,  4):
            return False

        return True


    def preprocess(self):
        """Use the base constraint to update the variables
        then update the grid."""

        super().preprocess()

        dx = dy = 0
        if self._loc[0] == 1 or self._loc[0] == bboat.SIZE:
            self._orient = bboat.HORZ
            dy = 1
        elif self._loc[1] == 1 or self._loc[1] == bboat.SIZE:
            self._orient = bboat.VERT
            dx = 1

        for x, y in bboat.grids_bound_mid(*self._loc):
            if (0 < x < bboat.SIZE_P1 and 0 < y < bboat.SIZE_P1
                    and not self.extra.assign_grid(x, y, EGrid.WATER)):
                raise cnstr.PreprocessorConflict(str(self))

        if not self.extra.assign_grid(*self._loc, EGrid.MID):
            raise cnstr.PreprocessorConflict(str(self))

        # if we know our orientation, set the boat parts on either side
        if self._orient is not None:
            x, y = self._loc
            for cx, cy in ((x - dx, y - dy), (x + dx, y + dy)):
                if not self.extra.assign_grid(cx, cy, EGrid.BOAT_PART):
                    raise cnstr.PreprocessorConflict(str(self))

        if not self._check_battleship():
            raise cnstr.PreprocessorConflict(str(self))

        return False


    def _test_orientation(self):
        """If there are water cell or boat part that tell us
        our direction expand the water cells to 5 on each side and the
        boat part in the two continue spots.

        Don't need to verify neigh is on the grid, because
        we know we are not on an edge (the preproc sets
        _orient if we are and this isn't called).

        Return False if the problem is overconstrained,
        True otherwise."""

        x, y = self._loc

        for dx, dy in bboat.CONT_INCS:

            neigh_x = x + dx
            neigh_y = y + dy

            cell_val = self.extra.grid[neigh_x][neigh_y]
            if EGrid.WATER in cell_val:
                self._orient = bboat.VERT if neigh_x == x else bboat.HORZ
                break
            if EGrid.BOAT_PART in cell_val:
                self._orient = bboat.HORZ if neigh_x == x else bboat.VERT
                break
        else:
            # nothing new to learn
            return True

        # set all 5 water cells on EACH side of us
        if self._orient == bboat.HORZ:
            bounds = {(x + 1, y + dy) for dy in range(-2, 3)}
            bounds |= {(x - 1, y + dy) for dy in range(-2, 3)}
            parts = ((x , y - 1), (x, y + 1))

        else:
            bounds = {(x + dx, y + 1) for dx in range(-2, 3)}
            bounds |= {(x + dx, y - 1) for dx in range(-2, 3)}
            parts = ((x - 1, y), (x + 1, y))

        for tx, ty in bounds:
            if (0 < tx < bboat.SIZE_P1 and 0 < ty < bboat.SIZE_P1
                    and not self.extra.assign_grid(tx, ty, EGrid.BOUNDARY)):
                # print(f"orient can't place water {self}\n", self.extra)
                return False

        # put boat parts in the two non-water spots
        for cx, cy in parts:
            if not self.extra.assign_grid(cx, cy, EGrid.BOAT_PART):
                # print(f"orient can't place parts {self}\n", self.extra)
                return False

        return True


    def forward_check(self, assignments):
        """Forward check for boat mids:

            1. if we don't know our orientation, test for it
               if we can determine orientation then:
                a. place BOAT_PARTs on either side
                b. expand the water cells

            2. if battleship is assigned then an unassigned
            mid must be a cruiser
        """

        x, y = self._loc
        cell_val = self.extra.grid[x][y]
        if EGrid.REDUCED in cell_val or EGrid.ASSIGNED in cell_val:
            return True

        if self._orient is None and not self._test_orientation():
            return False

        if self._orient is not None and 'battleship' in assignments:

            end_x = x
            end_y = y
            if self._orient == bboat.HORZ:
                end_y -= 1
            else:
                end_x -= 1

            if not self.reduce_to((end_x, end_y, self._orient), 3,
                                  HIDE_FUNC, assignments):
                # print(f"fwd {self} failed reduced_to\n", self.extra)
                return False

        return True


class BoatSub(BBoatConstraint, bboat_cnstr.BoatSub):
    """A submarine must be at (row, col).
    Base constraint does most work, here update grid in preprocessor.
    Preprocessor always fully processes this constraint."""

    def preprocess(self):
        """Use the base constraint to update the boat variable
        domains then update grid."""

        super().preprocess()

        if not self.extra.place_boat(self.extra.grid,
                                      (*self._loc, bboat.VERT), 1,
                                      flags=EGrid.REDUCED):
            raise cnstr.PreprocessConflict(str(self))

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
              bboat.BOATMID: BoatMid}


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

        if filename[0] == '_':
            continue

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


# build = build_puzzle("test.txt")

# bprob = problem.Problem()
# build(bprob)

# bprob._spec.prepare_variables()
# bprob.print_domains()

# print()
# for name, vobj in bprob.pspec.variables.items():
#     print(name, len(vobj.get_domain()))

# sol = bprob.get_all_solutions()
# bboat.print_grid(sol[0])
