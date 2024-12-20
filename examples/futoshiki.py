# -*- coding: utf-8 -*-
"""A Futoshiki solver.
Puzzles and rules at https://www.futoshiki.com/

Created on Tue Dec 17 12:50:17 2024
@author: Ann"""

# %% imports

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '..')))

import csp_solver as csp
from csp_solver import constraint as cnstr
from csp_solver import experimenter


# %%  constants

def _cross(unit1, unit2):
    """Cross product of elements in A and elements in B."""
    return [a+b for a in unit1 for b in unit2]


DIGITS = '12345'
ROWS = 'ABCDE'
COLS = DIGITS

SQUARES = _cross(ROWS, COLS)

ROW_UNITS = [_cross(r, COLS) for r in ROWS]
COL_UNITS = [_cross(ROWS, c) for c in COLS]

UNITLIST = ROW_UNITS + COL_UNITS


# %%  problem definition

def build(prob):

    prob.add_variables(SQUARES, list(DIGITS))

    for ugroup in UNITLIST:
        prob.add_constraint(cnstr.AllDifferent(), ugroup)

    # add the defined values here
    prob.add_constraint(cnstr.InValues('4'), ['B1', 'C3', 'D5'])
    prob.add_constraint(cnstr.InValues('2'), ['B5'])

    # add the less than constraints here
    prob.add_constraint(cnstr.LessThan(), ['A5', 'A4'])
    prob.add_constraint(cnstr.LessThan(), ['A4', 'A3'])
    prob.add_constraint(cnstr.LessThan(), ['A2', 'A1'])
    prob.add_constraint(cnstr.LessThan(), ['D4', 'D5'])
    prob.add_constraint(cnstr.LessThan(), ['E1', 'E2'])
    prob.add_constraint(cnstr.LessThan(), ['E2', 'E3'])


def show_solution(solution, _=None):

    for row in ROWS:
        for col in COLS:
            print(solution[row + col], end=' ')
        print()


# %%   main

if __name__ == '__main__':

    experimenter.do_stuff(build, show_solution)


if __name__ == '__test_example__':

    print('\n')
    prob = csp.Problem()
    build(prob)
    sol = prob.get_solution()
    show_solution(sol)
