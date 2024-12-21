# -*- coding: utf-8 -*-
"""Battle boats:
    Place 10 boats of various lengths on a ten by ten grid.
    Boats may not touch, not even diagonally.
    Row and column sums count the number of boat parts in row/column.
    Partial placement is provided (see constraints below).

variables - the grid cells
domains - boat part or empty

more variables but much smaller domains than battleboats.py

Constraints defined:
    NoOccedDiag - extention of ExactSum
    BoatCounts

Other constraints used:
    ExactSum
    InValues


Created on Thu May 11 18:53:28 2023
@author: Ann"""


# %% imports

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '../..')))

import csp_solver as csp
from csp_solver import constraint as cnstr
from csp_solver import experimenter
from csp_solver import solver
from csp_solver import var_chooser


# %% constants

SIZE = 10

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

UNASSIGNED = -1
EMPTY = 0
BOAT_PART = 1



# %%  grid printers


def print_grid(grid):
    """print the grid"""

    for x in range(0, 10):

        print(x, end='  ')
        for y in range(0, 10):

            if grid[x][y] == BOAT_PART:
                print(' x ', end='')
            elif grid[x][y] == EMPTY:
                print(' . ', end='')
            else:
                print('   ', end='')
        print()

    print('    0  1  2  3  4  5  6  7  8  9\n')


def print_assign_grid(assignments, _=None):
    """Convert the assignments to a grid and print it."""

    grid = [[UNASSIGNED] * 10 for _ in range(10)]

    for (x, y), value in assignments.items():
        grid[x][y] = value

    print_grid(grid)


# %%  variable sets


def diagonals():
    """Generate the diagonals for each cell.
    Only include locations on the grid.
    Include the center location as the first location."""

    crosses = [(0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]

    for x in range(SIZE):
        for y in range(SIZE):
            yield [(x + dx, y + dy) for dx, dy in crosses
                   if 0 <= x + dx < 10 and 0 <= y + dy < 10]


# %%

class NoOccedDiag(cnstr.ExactSum):
    """If there is a boat part at center_loc,
    no diagonal cells may be occupied."""

    def __init__(self, center_loc):

        super().__init__(0)
        self._loc = center_loc

    def __repr__(self):
        return f'NoOccedDiag{self._loc}'

    def satisfied(self, assignments):
        """Test the constraint."""

        if self._loc in assignments and assignments[self._loc]:
            lassign = assignments.copy()
            del lassign[self._loc]
            return super().satisfied(lassign)

        return True

    def preprocess(self):
        """The exact sum constraint only applies if the center
        is occupied, so don't let it's preprocessor run."""

        return False


class BoatCounts(cnstr.Constraint):
    """Count the number of boats and """

    RLIM_BLEN = 5
    INVALID = -1
    BOUNDED = 1
    UNBOUNDED = 2

    TOO_FEW = 10


    def __repr__(self):
        return 'BoatCount()'


    @staticmethod
    def make_grid(assignments):
        """Convert the assignments to a grid."""

        grid = [[UNASSIGNED] * SIZE for _ in range(SIZE)]

        for (x, y), value in assignments.items():
            grid[x][y] = value

        return grid


    @staticmethod
    def count_vert(grid, covered, x, y):
        """There is an uncountd boat part at x, y.
        If there are too many boat parts, return INVALID.
        If the boat is bounded by the puzzle edge or an empty cell,
        return BOUNDED and length, otherwise UNBOUNDED and length."""

        if x == SIZE - 1:
            return BoatCounts.BOUNDED, 1

        for dx in range(1, min(BoatCounts.RLIM_BLEN, SIZE - x)):
            if covered[x + dx][y]:
                return BoatCounts.INVALID, 0

            if grid[x + dx][y] != BOAT_PART:
                break
        else:
            bound = x + dx + 1
            if 4 < bound < SIZE and grid[bound][y] == BOAT_PART:
                return BoatCounts.INVALID, 0

            if bound == SIZE:
                return BoatCounts.BOUNDED, dx + 1

        if grid[x + dx][y] == EMPTY:
            return BoatCounts.BOUNDED, dx

        return BoatCounts.UNBOUNDED, dx


    @staticmethod
    def count_horz(grid, covered, x, y):
        """There is an uncounted boat part at x, y.
        If the boat is bounded by the puzzle edge or an empty cell,
        return BOUNDED and length, otherwise UNBOUNDED and length."""

        if y == SIZE - 1:
            return BoatCounts.BOUNDED, 1

        for dy in range(1, min(BoatCounts.RLIM_BLEN, SIZE - y)):
            if covered[x][y + dy]:
                return BoatCounts.INVALID, 0

            if grid[x][y + dy] != BOAT_PART:
                break
        else:
            bound = y + dy + 1
            if 4 < bound < SIZE and grid[x][bound] == BOAT_PART:
                return BoatCounts.INVALID, 0

            if bound == SIZE:
                return BoatCounts.BOUNDED, dy + 1

        if grid[x][y + dy] == EMPTY:
            return BoatCounts.BOUNDED, dy

        return BoatCounts.UNBOUNDED, dy


    @staticmethod
    def mark_covered(covered, x, y, vlen, hlen):
        """Mark the cells as covered."""

        for i in range(y, y + hlen):
            covered[x][i] = True

        for i in range(x + 1, x + vlen):
            covered[i][y] = True


    @staticmethod
    def update_counts(counts, vlen, hlen):
        """We have a bounded boat, count it."""

        if vlen == 1 and hlen == 1:
            counts[0] += 1

        elif vlen > 1 and hlen == 1:
            counts[vlen - 1] += 1

        elif hlen > 1 and vlen == 1:
            counts[hlen - 1] += 1


    def count_boats(self, assignments):
        """Count the number of boats.

        covered are cells with boats that have been included in
        another boat count.

        Index of counts is boat_length - 1."""

        counts = [0] * len(BOATS)
        limits = [4, 3, 2, 1]

        covered = [[False] * SIZE for _ in range(SIZE)]
        grid = self.make_grid(assignments)

        for x in range(SIZE):
            for y in range(SIZE):

                if covered[x][y] or grid[x][y] != BOAT_PART:
                    continue

                vcond, vlen = self.count_vert(grid, covered, x, y)
                if vcond == BoatCounts.INVALID:
                    return BoatCounts.INVALID

                hcond, hlen = self.count_horz(grid, covered, x, y)

                if hlen == BoatCounts.INVALID:
                    return BoatCounts.INVALID

                if hlen > 1 and vlen > 1:
                    return BoatCounts.INVALID

                self.mark_covered(covered, x, y, vlen, hlen)

                if BoatCounts.UNBOUNDED in [vcond, hcond]:
                    continue

                self.update_counts(counts, vlen, hlen)

                if any(cnt > limits[i] for i, cnt in enumerate(counts)):
                    return BoatCounts.INVALID

        return counts


    def satisfied(self, assignments):
        """Test the assignments for boat counts.

        If we have a small number of assignments or no boat parts:
            don't do any work, return True wait for more assignments

        If don't have all 100 assignements:
            return False IF
                1. there are too many assigned boat parts
                2. any boat is longer than 4
                3. there are too many of any size of 'bounded' boats

        Once we have all 100 assignments, test the counts."""

        bparts = list(assignments.values()).count(BOAT_PART)

        if len(assignments) < BoatCounts.TOO_FEW or not bparts:
            return True

        if bparts > NCELLS:
            return False

        counts = self.count_boats(assignments)
        if counts == BoatCounts.INVALID:
            return False

        if len(assignments) < 100:
            return True
        return counts == [4, 3, 2, 1]



# %%

def build(problem):
    """Battleship/Commodore problem from Games Magazine September 2019."""

    problem.solver = solver.NonRecBacktracking()
    problem.var_chooser = var_chooser.MinDomain

    variables = [(x, y)
                 for x in range(SIZE)
                 for y in range(SIZE)]
    problem.add_variables(variables, [BOAT_PART, EMPTY])

    # basic puzzle info --
    #  number of required boats & boats should not overlap or touch

    problem.add_constraint(cnstr.ExactSum(NCELLS), variables)

    for vlist in diagonals():
        problem.add_constraint(NoOccedDiag(vlist[0]), vlist)

    problem.add_constraint(BoatCounts(), variables)

    # row/col sums
    rsums = [3, 1, 2, 1, 1, 2, 1, 1, 4, 4]
    for row, rsum in enumerate(rsums):

        rvars = [(row, y) for y in range(SIZE)]
        if rsum:
            problem.add_constraint(cnstr.ExactSum(rsum), rvars)
        else:
            problem.add_constraint(cnstr.InValues([EMPTY]), rvars)

    csums = [5, 0, 2, 1, 2, 0, 2, 4, 1, 3]
    for col, csum in enumerate(csums):

        cvars = [(x, col) for x in range(SIZE)]
        if csum:
            problem.add_constraint(cnstr.ExactSum(csum), cvars)
        else:
            problem.add_constraint(cnstr.InValues([EMPTY]), cvars)

    # partial solutions:   boat start/end, middle, sub, or empty loc
    problem.add_constraint(cnstr.InValues([EMPTY]), [(0, 9)])

    # Boat ends - the location and the one in the continue direction are boats
    problem.add_constraint(cnstr.InValues([BOAT_PART]), [(1, 0), (0, 0)])
    problem.add_constraint(cnstr.InValues([EMPTY]),
                           [(2, 0), (2, 1), (1, 1), (0, 1)])
    problem.add_constraint(cnstr.InValues([BOAT_PART]), [(8, 6), (9, 6)])
    problem.add_constraint(cnstr.InValues([EMPTY]),
                           [(9, 5), (8, 5), (7, 5), (7, 6),
                            (9, 7), (8, 7), (7, 7)])


# %%   main

if __name__ == '__main__':

    experimenter.do_stuff(build, print_assign_grid)


if __name__ == '__test_example__':

    bprob = csp.Problem()
    build(bprob)
    sol = bprob.get_solution()
    print()
    print_assign_grid(sol)
