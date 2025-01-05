# -*- coding: utf-8 -*-
"""A simple math problem:

    a != c   and   2a = b  and   b**a == c

    two solutions should be found

Created on Wed May  3 14:11:36 2023
@author: Ann"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '..')))

from csp_solver import constraint as cnstr
from csp_solver import solver
from csp_solver import problem


def solve(slvr):
    """Create a solve a simple math problem."""

    prob = problem.Problem(slvr)

    prob.add_variable('a', [1, 2, 3, 4])
    prob.add_variable('b', [1, 2, 5, 6])
    prob.add_variable('c', [2, 23, 216])

    prob.add_constraint(cnstr.AllDifferent(), ['a', 'c'])
    prob.add_constraint(lambda a, b : a*2 == b, ['a', 'b'])
    prob.add_constraint(lambda a, b, c: b**a == c, ['a', 'b', 'c'])

    if 'MinConflictsSolver' == slvr.__class__.__name__:
        print('\nUsing', slvr.__class__.__name__, '(only one solution)')
        print(prob.get_solution())
    else:
        print('\nUsing', slvr.__class__.__name__)
        print(prob.get_all_solutions())


if __name__ in ('__main__', '__test_example__'):

    print('\n')
    for s in [solver.Backtracking(forward_check=True),
              solver.NonRecBacktracking(),
              solver.MinConflictsSolver()
              ]:

        solve(s)
