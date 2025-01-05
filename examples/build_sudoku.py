# -*- coding: utf-8 -*-
"""An example of using constraints to find sudoku
puzzles with unique solutions.

Build a puzzle by randomly shuffling the trivial
9 rows of 1 .. 9.

Then remove numbers until the solution isn't unique.

The goal is to remove at least 40 of the numbers.

Ten new grids are tried to see if can get there,
if we don't return the puzzle with the most squares
cleared.

Created on Wed May 15 10:18:26 2024
@author: Ann"""


import os
import random
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '..')))

from csp_solver import constraint as cnstr
from csp_solver import problem
from csp_solver import solver
from csp_solver import var_chooser


# %%

def _cross(unit1, unit2):
    """Cross product of elements in A and elements in B."""
    return [a+b for a in unit1 for b in unit2]

EMPTY = '0'

DIGITS = '123456789'
ROWS = 'ABCDEFGHI'
COLS = DIGITS

SQUARES = _cross(ROWS, COLS)

"""A unit is one of the groups of SQUARES
that must have one each of DIGITS in it"""

ROW_UNITS = [_cross(r, COLS) for r in ROWS]
COL_UNITS = [_cross(ROWS, c) for c in COLS]
BOX_UNITS = [_cross(rs, cs)
             for rs in ('ABC', 'DEF', 'GHI')
             for cs in ('123', '456', '789')]

UNITLIST = ROW_UNITS + COL_UNITS + BOX_UNITS


def display_grid(assigns):
    """Display these values as a 2D grid."""

    sgrid = [[' '] * 9 for _ in range(9)]

    for squ, val in assigns.items():

        row = ROWS.index(squ[0])
        col = int(squ[1]) - 1
        sgrid[row][col] = str(val)

    print()
    for row in range(9):
        for col in range(9):
            print(sgrid[row][col], end=' ')
            if col in [2, 5]:
                print('| ', end='')
        if row in [2, 5]:
            print('\n----- + ----- + -----', end='')
        print()


# %%

def build_constraints(puzzle):
    """Get the solutions to the puzzle,
    which is a parital set of assignements"""

    prob_inst = problem.Problem(solver.NonRecBacktracking())
    prob_inst.var_chooser = var_chooser.MinDomain()
    prob_inst.enable_forward_check()

    for squ in SQUARES:
        if squ in puzzle:
            prob_inst.add_variable(squ, [puzzle[squ]])
        else:
            prob_inst.add_variable(squ, list(DIGITS))

    for ugroup in UNITLIST:
        prob_inst.add_constraint(cnstr.AllDifferent(), ugroup)

    return prob_inst


def generate_grid():
    """Generate a grid.
    This method might create predicatable grids."""

    row = list(DIGITS)
    random.shuffle(row)

    start_puz = dict(zip(ROW_UNITS[0], row))
    prob_inst = build_constraints(start_puz)

    return prob_inst.get_solution()


def has_unique_solution(puzzle):
    """Determine if the puzzle has a unique solution."""

    prob_inst = build_constraints(puzzle)
    return len(prob_inst.more_than_one_solution()) == 1


def generate_puzzle(stop_at=81):
    """Generate a grid and then remove numbers to find a single solution.

    Don't provide the parameter unless run a test of the example."""

    best_count = 0
    best = None
    for tries in range(10):
        print(' Generating new grid.')
        puzzle = generate_grid()
        squares = SQUARES.copy()
        random.shuffle(squares)

        for count in range(1, stop_at):
            for squ in squares:

                val = puzzle.pop(squ)
                if has_unique_solution(puzzle):
                    print(count % 10, end='', flush=True)
                    squares.remove(squ)
                    break

                puzzle[squ] = val

            else:
                # can't remove anymore while maintianing a unique solution
                print('\nCant remove more')
                if count > 40:
                    return puzzle

        if count > best_count:
            print(f'\nSaving best at {count}')
            best = puzzle.copy()
            best_count = count

    return best


if __name__ == '__main__':

    sud_puzzle = generate_puzzle()
    display_grid(sud_puzzle)


if __name__ == '__test_example__':

    # run just enough to exercise most of the code
    print('\n')
    sud_puzzle = generate_puzzle(15)
    print(sud_puzzle)
    display_grid(sud_puzzle)
