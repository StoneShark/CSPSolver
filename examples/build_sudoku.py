# -*- coding: utf-8 -*-
"""An example of using constraints to find sudoku
puzzles with unique solutions.

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


def display_grid(thing):
    """Display these values as a 2D grid."""
    sep_sqrs = '36'
    sep_rows = 'CF'


    print()
    width = 1 + max(len(thing[squ]) for squ in SQUARES)
    line = '+'.join(['-' * (width*3)] * 3)

    for row in ROWS:
        print(''.join(thing[row + c].center(width) +
                      ('|' if c in sep_sqrs else '') for c in COLS))
        if row in sep_rows:
            print(line)
    print()


# %%

def build_constraints(puzzle):
    """Get the solutions to the puzzle,
    which is a parital set of assignements"""

    prob_inst = problem.Problem(solver.NonRecBacktracking())
    prob_inst.set_var_chooser(var_chooser.MinDomain())
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


def generate_puzzle():
    """Generate a grid and then remove numbers to find a single solution."""

    best_count = 0
    best = None
    for tries in range(10):
        print('Generating new grid.')
        puzzle = generate_grid()
        squares = SQUARES.copy()
        random.shuffle(squares)

        for count in range(1, 81):
            for squ in squares:

                val = puzzle.pop(squ)
                if has_unique_solution(puzzle):
                    print(count % 10, end='', flush=True)
                    squares.remove(squ)
                    break
                else:
                    puzzle[squ] = val

            else:
                # can't remove anymore while maintianing a unique solution
                print('\nCant remove more')
                if count > 40:
                    return puzzle

        if count > best_count:
            print('\nSaving best at {count}')
            best = puzzle.copy()
            best_count = count

    return best
