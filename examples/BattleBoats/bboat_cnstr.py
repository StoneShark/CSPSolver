# -*- coding: utf-8 -*-
"""Battle boats:
    Place 10 boats of various lengths on a ten by ten grid.
    Boats may not touch, not even diagonally.
    Row and column sums count the number of boat parts in row/column.
    Partial placement is provided (see constraints below).

variables are boat types, see bboat.BOAT_LENGTH.keys()
domains are locations that boats can be placed as tuples: (x, y, orientation)

Constraints defined:
        BoatBoundaries
        IncOrder - restrict boats to increasing order
                   removes duplicates caused by 2 cruisers,
                   3 destroyers and 4 subs
        RowSum - puzzle specifies row sums
        ColSum - puzzles specifies column sumes
        CellEmpty - puzzle specifies an empty cell
        BoatEnd - puzzle specifies a boat end part
                  with opening up, down, left, right
        BoatMid - puzzle specifies a boat mid part,
                  boat may extend in either direction
        BoatSub - puzzle specifies a submarine (boat length of 1)

Forward_checks for the constraints do not return changed variables.
Brief testing showed that is much slower.

Created on Fri May  5 03:40:16 2023
@author: Ann"""

# %% imports

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '../..')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import battleboats as bboat
from csp_solver import constraint as cnstr
from csp_solver import experimenter
from csp_solver import problem
from csp_solver import solver
from csp_solver import var_chooser
from csp_solver import variable


# %% constraints

class BoatBoundaries(cnstr.Constraint):
    """Boats must not overlap and no boat may be in the boundary
    of another.

    If only one boat is assigned, return True."""

    @staticmethod
    def satisfied(boat_dict):
        """Test the constraint."""

        if len(boat_dict) == 1:
            return True

        occupied = set()
        bounds = set()
        for bname, location in boat_dict.items():

            x, y, orient = location
            length = bboat.BOAT_LENGTH[bname]
            bcells = bboat.grids_occed(x, y, orient, length)

            if (occupied and
                any(coord in occupied or coord in bounds
                    for coord in bcells)):
                return False

            occupied |= set(bcells)
            bounds |= bboat.grids_bounding(x, y, orient, length)

        return True


    def forward_check(self, assignments):
        """Hide all domain values that are in boat boundaries
        or already occupied."""

        hide_set = set()
        for bname, (x, y, orient) in assignments.items():
            length = bboat.BOAT_LENGTH[bname]

            hide_set |= set(bboat.grids_occed(x, y, orient, length))
            hide_set |= bboat.grids_bounding(x, y, orient, length)

        unassigned= [vobj for vobj in self._vobjs
                     if vobj.name not in assignments]

        return bboat.empty_cells(hide_set, unassigned, variable.Variable.hide)


class IncOrder(cnstr.OneOrder):
    """Boats must be assigned in increasing order sorted by location.
    Variable lists should be matching boat types, e.g. all submarines.

    This constraint assumes that the constraint preprocessor calls
    are made in the order they were assigned to the problem."""

    def preprocess(self):
        """These constraints are added to the constraint list last,
        so this method will be called after all other constraint's
        are preprocessed.

        If any variable has been reduced to one value by the
        preprocessor, remove that variable from this constraint."""

        new_vobjs = [vobj for vobj in self._vobjs
                    if vobj.nbr_values() > 1]

        if new_vobjs:
            self.set_variables(new_vobjs)
            return False

        # all vars have one value, don't need this constraint
        return True


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


class RowSum(cnstr.Constraint):
    """The number of boats parts in row is <= rsum until all variables
    are assigned then they must be equal."""

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
            blength = bboat.BOAT_LENGTH[bname]

            if orient == bboat.HORZ and x == self._row:
                cur_sum += blength

            elif orient == bboat.VERT and x <= self._row <= x + blength - 1:
                cur_sum += 1

            if cur_sum > self._row_sum:
                return False

        if len(boat_dict) == bboat.B_CNT:
            return cur_sum == self._row_sum

        return cur_sum <= self._row_sum


    def preprocess(self):
        """Preprocess row sum the constraint:

            1. If the row_sum is zero remove any boat start location
               that would occupy the row.
               The constraint is then fully processed, return True.

            2. Otherwise, remove domain values for any boats that
               wont fit in the row but only along the row
               (ie. horizontal boats)"""

        if not self._row_sum:
            row_coords = {(self._row, y) for y in range(1, bboat.SIZE_P1)}
            if not bboat.empty_cells(row_coords, self._vobjs,
                                     variable.Variable.remove_dom_val):
                raise cnstr.PreprocessorConflict(str(self))
            return True

        # remove boats that wont fit in row_sum
        for vobj in self._vobjs:

            if bboat.BOAT_LENGTH[vobj.name] <= self._row_sum:
                continue

            for value in vobj.get_domain()[:]:
                x, y, orient = value

                if (x == self._row
                        and orient == bboat.HORZ
                        and not vobj.remove_dom_val(value)):
                    raise cnstr.PreprocessorConflict(str(self))

        return False


    def forward_check(self, assignments):
        """If the row sum is exactly satisfied; make certain that
        there are not any boats crossing row.

        Return - False if any domain has been eliminated, True otherwise."""

        occed_cols = [False] * bboat.SIZE_P1
        cur_sum = 0

        for bname, (x, y, orient) in assignments.items():
            blength = bboat.BOAT_LENGTH[bname]

            if orient == bboat.HORZ and x == self._row:
                cur_sum += blength
                occed_cols[x:x + blength] = [True] * blength

            elif orient == bboat.VERT and x <= self._row <= x + blength - 1:
                cur_sum += 1
                occed_cols[self._row] = True

            if cur_sum > self._row_sum:
                return False

        if cur_sum < self._row_sum:
            return True

        empty_cols = {(self._row, y)
                      for y in range(1, bboat.SIZE_P1) if not occed_cols[y]}
        unassigned= [vobj for vobj in self._vobjs
                      if vobj.name not in assignments]

        return bboat.empty_cells(empty_cols,
                                 unassigned,
                                 variable.Variable.hide)


class ColSum(cnstr.Constraint):
    """The number of boats parts in col is <= csum until all variables
    are assigned then they must be equal."""

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
            blength = bboat.BOAT_LENGTH[bname]

            if orient == bboat.VERT and y == self._col:
                cur_sum += blength

            elif orient == bboat.HORZ and y <= self._col <= y + blength - 1:
                cur_sum += 1

            if cur_sum > self._col_sum:
                return False

        if len(boat_dict) == bboat.B_CNT:
            return cur_sum == self._col_sum

        return cur_sum <= self._col_sum


    def preprocess(self):
        """Preprocess col sum the constraint:

            1. If the col_sum is zero remove any boat start location
               that would occupy the column.
               The constraint is then fully processed, return True.

            2. Otherwise, remove domain values for any boats that
               wont fit in the col but only along the col
               (ie. bboat.VERTical boats)"""

        if not self._col_sum:
            col_coords = {(x, self._col) for x in range(1, bboat.SIZE_P1)}
            if not bboat.empty_cells(col_coords, self._vobjs,
                                     variable.Variable.remove_dom_val):
                raise cnstr.PreprocessorConflict(str(self))
            return True

        # remove boats that wont fit in col_sum
        for vobj in self._vobjs:

            if bboat.BOAT_LENGTH[vobj.name] <= self._col_sum:
                continue

            for value in vobj.get_domain()[:]:
                x, y, orient = value

                if (y == self._col
                        and orient == bboat.VERT
                        and not vobj.remove_dom_val(value)):
                    raise cnstr.PreprocessorConflict(str(self))

        return False


    def forward_check(self, assignments):
        """If the col sum is exactly satisfied; make certain that
        there are not any boats crossing col.

        Return - False if any domain has been eliminated, True otherwise."""

        occed_rows = [False] * (bboat.SIZE_P1)
        cur_sum = 0

        for bname, (x, y, orient) in assignments.items():
            blength = bboat.BOAT_LENGTH[bname]

            if orient == bboat.VERT and y == self._col:
                cur_sum += blength
                occed_rows[y:y + blength] = [True] * blength

            elif orient == bboat.HORZ and y <= self._col <= y + blength - 1:
                cur_sum += 1
                occed_rows[self._col] = True

            if cur_sum > self._col_sum:
                return False

        if cur_sum < self._col_sum:
            return True

        empty_rows = {(x, self._col)
                      for x in range(1, bboat.SIZE_P1) if not occed_rows[x]}
        unassigned= [vobj for vobj in self._vobjs
                      if vobj.name not in assignments]

        return bboat.empty_cells(empty_rows,
                                 unassigned,
                                 variable.Variable.hide)


class CellEmpty(cnstr.Constraint):
    """The cell at row, col must be empty.

    Fully applied by the preprocessor, no use for forward_check."""

    def __init__(self, row, col):
        super().__init__()
        self._loc = (row, col)


    def __repr__(self):
        return f'CellEmpty({self._loc[0]}, {self._loc[1]})'


    def satisfied(self, boat_dict):
        """Test the constraint."""

        for bname, (x, y, orient) in boat_dict.items():

            length = bboat.BOAT_LENGTH[bname]

            if self._loc in bboat.grids_occed(x, y, orient, length):
                return False

        return True


    def preprocess(self):
        """Remove any domain values (start locations) that
        would include (row, col). Contraint will be fully satisfied,
        but call _test_over_satis to make certain it is not over
        contsrainted (it will raise exception)."""

        if not bboat.empty_cells({self._loc}, self._vobjs,
                                 variable.Variable.remove_dom_val):
            raise cnstr.PreprocessorConflict(str(self))

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
            blength = bboat.BOAT_LENGTH[bname]

            if blength == 1:
                if self._loc == coord:
                    return False
                continue

            end = bboat.get_end_loc(x, y, orient, blength)

            if self._cont_dir == bboat.DOWN:
                good = self._loc == coord and orient == bboat.VERT

            elif self._cont_dir == bboat.LEFT:
                good = self._loc == end and orient == bboat.HORZ

            elif self._cont_dir == bboat.UP:
                good = self._loc == end and orient == bboat.VERT

            elif self._cont_dir == bboat.RIGHT:
                good = self._loc == coord and orient == bboat.HORZ

            if good:
                return True

        return len(boat_dict) < bboat.B_CNT


    def _check_destroyer(self):
        """If the boat end is one away from an edge and
        pointed towards that edge, then we know a destroyer
        location return it."""

        destroyer_loc = None

        if self._loc[1] == 2 and self._cont_dir == bboat.LEFT:
            destroyer_loc = (self._loc[0], 1, bboat.HORZ)

        elif self._loc[1] == bboat.SIZE - 1 and self._cont_dir == bboat.RIGHT:
            destroyer_loc = (*self._loc, bboat.HORZ)

        elif self._loc[0] == 2 and self._cont_dir == bboat.UP:
            destroyer_loc = (1, self._loc[1], bboat.VERT)

        elif self._loc[0] == bboat.SIZE - 1 and self._cont_dir == bboat.DOWN:
            destroyer_loc = (*self._loc, bboat.VERT)

        return destroyer_loc


    def preprocess(self):
        """Given boat end and direction, we know which cells opposite of
        continue direction and sides (plus +1 in cont_dir) can be
        removed from the domains of all variables. Those are
        known water cells.

        If the clue specifies a destroyer location (length 2),
        find one that hasn't been reduced to one domain value
        and reduce it to the boat start location. When return,
        report that the constraint is fully processed.

        Remove subs all neighbors and the self location.

        For boats longer than 2,
        remove any boats that would start at the continue position,
        remove any values that put a middle part of the boat at (row, col)."""

        empties = bboat.grids_bound_end(*self._loc, self._cont_dir)
        if not bboat.empty_cells(empties, self._vobjs,
                                 variable.Variable.remove_dom_val):
            raise cnstr.PreprocessorConflict(str(self))

        destroyer_loc = self._check_destroyer()
        fully = False
        cont_pos = bboat.cont_pos(self._loc, self._cont_dir)

        neighs = bboat.grid_neighs(*self._loc)

        for bobj in self._vobjs:
            length = bboat.BOAT_LENGTH[bobj.name]

            if length == 1:
                if not bboat.remove_starts(bobj, neighs | {self._loc}):
                    raise cnstr.PreprocessorConflict(str(self))
                continue

            if length == 2:
                if destroyer_loc and bobj.nbr_values() > 1:
                    bobj.set_domain([destroyer_loc])
                    destroyer_loc = None
                    fully = True
                continue

            # length > 2
            if not bboat.remove_starts_ends(bobj, {cont_pos}):
                raise cnstr.PreprocessorConflict(str(self))

            for value in bobj.get_domain()[:]:
                x, y, orient = value
                if (self._loc in bboat.grids_mid(x, y, orient, length)
                        and not bobj.remove_dom_val(value)):
                    raise cnstr.PreprocessorConflict(str(self))

        if destroyer_loc:
            # this clue specifies a destroyer location but
            # didn't find a destroyer var to reduce to it
            raise cnstr.PreprocessorConflict(
                         f"{self} couldn't place destoryer.")

        return fully

    # XXXX BoatEnd forward_check
    #   very specific cases that require lots of computation
    #   if boat assigned 3 away from open end, then have a desstroyer @ loc


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
            length = bboat.BOAT_LENGTH[bname]

            if length == 1:
                if self._loc == (x, y):
                    return False
                continue

            if length == 2:
                if self._loc in bboat.grids_occed(x, y, orient, length):
                    return False
                continue

            mids = bboat.grids_mid(x, y, orient, length)
            if self._loc in mids:
                return True

        return len(boat_dict) < bboat.B_CNT


    def preprocess(self):
        """Use empty_cells to eliminate any boats that
        would go through the known water cells returned
        by grids_bound_mid.

        Remove subs from all neighboring cells and self loc.
        Remove the starts & ends of all destroyers from
        the neighboring cells and self loc.
        Remove all starts and ends of other boats from self loc.

        Constraint is never fully applied here."""

        if not bboat.empty_cells(bboat.grids_bound_mid(*self._loc),
                                 self._vobjs,
                                 variable.Variable.remove_dom_val):
            raise cnstr.PreprocessorConflict(str(self))

        neighs = bboat.grid_neighs(*self._loc)
        for bobj in self._vobjs:
            length = bboat.BOAT_LENGTH[bobj.name]

            if length == 1:
                if not bboat.remove_starts(bobj, neighs | {self._loc}):
                    raise cnstr.PreprocessorConflict(str(self))

            elif length == 2:
                if not bboat.remove_starts_ends(bobj, neighs | {self._loc}):
                    raise cnstr.PreprocessorConflict(str(self))

            else:
                if not bboat.remove_starts_ends(bobj, {self._loc}):
                    raise cnstr.PreprocessorConflict(str(self))

        return False

    # XXXX  BoatMid forward_check
    #   very specific cases that require lots of computation
    #   if another boat assignment/boat boundary is two away from mid loc
    #   then we know the orientation of the boat though mid and could extend
    #   watter cells to 5 on each side


class BoatSub(cnstr.Constraint):
    """A submarine must be at (row, col). Find one unreduced sub
    variable and reduce it to (row, col, bboat.VERT)
.
    For any boat longer than a submarine, row, col and it's bounding
    box (nieghbor's) from domain.

    If all 4 subs are assigned but none at (row, col) return False,
    otherwise True.

    No forward_check: either a boat was constrained to loc
    and constraint is fully satisfied
    or the constraint is over constrained."""

    def __init__(self, row, col):
        super().__init__()
        self._loc = (row, col)


    def __repr__(self):
        return f'BoatSub({self._loc[0]}, {self._loc[1]})'


    def satisfied(self, boat_dict):
        """Test the constraint."""

        sub_cnt = 0

        for bname, (x, y, orient) in boat_dict.items():
            length = bboat.BOAT_LENGTH[bname]

            if length > 1:
                if self._loc in bboat.grids_occed(x, y, orient, length):
                    return False
                continue

            sub_cnt += 1
            if self._loc == (x, y):
                return True

        return sub_cnt < 4


    def preprocess(self):
        """For all boats longer than 1, use empty_cells to
        eliminate any boats that would go through the known
        water cells (neighbors) and self location.

        Reduce the domain of one sub to this location and return
        that the constraint is fully processed."""

        not_placed = True
        empties = bboat.grid_neighs(*self._loc) | {self._loc}

        for bobj in self._vobjs:
            length = bboat.BOAT_LENGTH[bobj.name]

            if length == 1:
                if not_placed and bobj.nbr_values() > 1:
                    bobj.set_domain([(*self._loc, bboat.VERT)])
                    not_placed = False
                continue

            if not bboat.empty_cells(empties, [bobj],
                                     variable.Variable.remove_dom_val):
                raise cnstr.PreprocessorConflict(str(self))

        if not_placed:
            # didn't find a sub var to reduce to loc
            raise cnstr.PreprocessorConflict(str(self),
                                             "couldn't place sub.")
        return True


# %%  boat order var chooser

class BoatOrder(var_chooser.VarChooser):
    """Choose the variable assignment order based on
        1. any boats reduced to a single location
           (boat1 is always reduced before boat2)
        2. longest unassigned boat by length."""

    @staticmethod
    def choose(vobjs, _1, _2):
        """var chooser"""
        for vobj in vobjs:
            if vobj.nbr_values() == 1:
                return vobj

        return max(vobjs, key = lambda var : bboat.BOAT_LENGTH[var.name])

BoatOrder()  # to catch any interface changes


# %%  load and define puzzles

def add_basic(boatprob, bboat_constraint):
    """Add the basic constraints common to all battle boats problems."""

    boatprob.solver = solver.NonRecBacktracking()
    boatprob.var_chooser = BoatOrder
    boatprob.forward_check = True

    # add boat location variables and domains
    for bname, length in bboat.BOAT_LENGTH.items():
        boatprob.add_variable(bname, bboat.pos_locs(length))

    #  boats should not overlap or touch
    boatprob.add_constraint(bboat_constraint(), bboat.BOATS)


def add_final(boatprob, uset_cnstr=False):
    """IncOne constraints need to be added last so that any variables
    whose domains have been reduced to one value can be excluded by
    the preprocessor.
    Reduces solutions from 2! * 3! * 4! = 288 to 1

    uset_cnstr chooses which method to use for unique solutions.
    IncOrder has a forward check that results in faster solves."""

    var_sets = [['cruiser1', 'cruiser2'],
                ['destroyer1', 'destroyer2', 'destroyer3'],
                ['sub1', 'sub2', 'sub3', 'sub4']]

    if uset_cnstr:
        boatprob.set_unique_sol_constraint(cnstr.UniqueSets(var_sets),
                                           bboat.BOATS)
    else:
        for vset in var_sets:
            boatprob.add_constraint(IncOrder(), vset)


BOAT_CNSTR = {bboat.ROWSUM: RowSum,
              bboat.COLSUM: ColSum,
              bboat.EMPTYCELL : CellEmpty,
              bboat.SUMBARINE : BoatSub,
              bboat.BOATTOP : BoatEnd,
              bboat.BOATBOTTOM : BoatEnd,
              bboat.BOATLEFT : BoatEnd,
              bboat.BOATRIGHT : BoatEnd,
              bboat.BOATMID : BoatMid
              }


def build_cons(pairs, constraints):
    """Convert the pairs of values from the json problem statement
    into constraints and variable assignments. There may be
    duplcate keys, the json reader returns the pairs."""

    cons = []

    for name, value in pairs:

        if name == bboat.ROWSUM:
            for row, rsum in enumerate(value):
                cons += [constraints[name](row + 1, rsum)]
            continue

        if name == bboat.COLSUM:
            for col, csum in enumerate(value):
                cons += [constraints[name](col + 1, csum)]
            continue

        con_class = constraints[name]
        row, col = value

        if issubclass(con_class, BoatEnd):
            cons += [con_class(row, col, bboat.ORIENT[name])]
        else:
            cons += [con_class(row, col)]

    return cons


def build_puzzle(filename):
    """Return a function that can build boat a problem
    based on an input file."""

    # print(f"Reading {filename}")
    pairs = bboat.read_puzzle(bboat.PUZ_PATH + filename)
    if not pairs:
        return None

    def build_func(boatprob):
        """place holder"""

        add_basic(boatprob, BoatBoundaries)

        for con in build_cons(pairs, BOAT_CNSTR):
            boatprob.add_constraint(con, bboat.BOATS)

        add_final(boatprob)

    build_func.__name__ = f'build_puzzle("{filename}")'
    build_func.__doc__ = filename + ':  \n' \
            + '\n'.join(str(c)+ '=' + str(v) for c, v in pairs)

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
    # bboat.cache_info()

if __name__ == '__test_example__':

    # run_slow is defined in the global dict passed to runpy.run_path
    # access through globals so we don't get a syntax error

    # if not run_slow:
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


# build = build_puzzle("test_mid_pre.txt")

# bprob = problem.Problem()
# build(bprob)

# # bprob._spec.prepare_variables()
# # bprob.print_domains()

# sol = bprob.get_all_solutions()
# bboat.print_grid(sol[0])
