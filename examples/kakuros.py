# -*- coding: utf-8 -*-
"""A Kakuros solver.
Puzzles and rules at https://www.kakuros.com/

Created on Wed Dec 18 06:47:04 2024
@author: Ann"""


# %%   imports

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '..')))

import csp_solver as csp
from csp_solver import constraint as cnstr
from csp_solver import experimenter


# %%   constants

DIGITS = list(range(1, 10))
ROWS = 'ABCDE'
COLS = '12345'


# %%  problem definition

def build(prob):
    """Example Kakuros problem as CSP."""

    sums = [(3, 'B2', 'C2'),
            (10, 'B3', 'C3', 'D3', 'E3'),
            (29, 'B4', 'C4', 'D4', 'E4'),
            (16, 'D5', 'E5'),

            (13, 'B2', 'B3', 'B4'),
            (9, 'C2', 'C3', 'C4'),
            (19, 'D3', 'D4', 'D5'),
            (17, 'E3', 'E4', 'E5'),
            ]

    variables = list({var for _, *svars in sums for var in svars})

    prob.add_variables(variables, list(DIGITS))

    for ttl, *svars in sums:
        prob.add_constraint(cnstr.AllDifferent(), svars)
        prob.add_constraint(cnstr.ExactSum(ttl), svars)


def show_solution(solution, _=None):
    """Print the solution as a grid"""

    for row in ROWS:
        for col in COLS:
            print(solution.get(row + col, '.'), end=' ')
        print()


# %%   main

if __name__ == '__main__':

    experimenter.do_stuff(build, show_solution)

if __name__ == '__test_example__':

    print('\n')
    kprob = csp.Problem()
    build(kprob)
    sol = kprob.get_solution()
    show_solution(sol)
