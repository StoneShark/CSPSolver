# -*- coding: utf-8 -*-
"""An example sudoku puzzle and solver.

Created on Tue May 14 11:55:32 2024
@author: Ann"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '..')))

from csp_solver import constraint as cnstr
from csp_solver import experimenter

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


# %%  problem spec

def build(eproblem):

    for squ in SQUARES:
        eproblem.add_variable(squ, list(DIGITS))

    for ugroup in UNITLIST:
        eproblem.add_constraint(cnstr.AllDifferent(), ugroup)

    # add specific puzzle constraints here
    puzzle = {"A1": "0", "A2": "3", "A3": "6", "A4": "7", "A5": "0",
              "A6": "8", "A7": "5", "A8": "2", "A9": "9", "B1": "0",
              "B2": "0", "B3": "5", "B4": "0", "B5": "9", "B6": "0",
              "B7": "4", "B8": "6", "B9": "8", "C1": "0", "C2": "0",
              "C3": "0", "C4": "0", "C5": "0", "C6": "6", "C7": "7",
              "C8": "1", "C9": "3", "D1": "8", "D2": "4", "D3": "3",
              "D4": "1", "D5": "7", "D6": "2", "D7": "6", "D8": "9",
              "D9": "5", "E1": "9", "E2": "6", "E3": "1", "E4": "0",
              "E5": "0", "E6": "0", "E7": "2", "E8": "8", "E9": "7",
              "F1": "5", "F2": "0", "F3": "0", "F4": "6", "F5": "8",
              "F6": "9", "F7": "1", "F8": "3", "F9": "4", "G1": "0",
              "G2": "5", "G3": "0", "G4": "0", "G5": "6", "G6": "0",
              "G7": "3", "G8": "4", "G9": "2", "H1": "6", "H2": "0",
              "H3": "4", "H4": "0", "H5": "3", "H6": "5", "H7": "8",
              "H8": "7", "H9": "1", "I1": "3", "I2": "0", "I3": "0",
              "I4": "0", "I5": "0", "I6": "0", "I7": "9", "I8": "5",
              "I9": "6"}
    for var, val in puzzle.items():
        if val != '0':
            eproblem.add_constraint(cnstr.InValues([val]), [var])


def show_solution(solution):

    for row in ROWS:
        for col in COLS:
            print(solution[row + col], end=' ')
            if col in 'CF':
                print(' | ', end='')
        print()


if __name__ == '__main__':

    experimenter.do_stuff(build, show_solution)
