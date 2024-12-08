# -*- coding: utf-8 -*-
"""Solve the eight queens problem.

Created on Mon May  8 13:30:37 2023
@author: Ann"""

import functools as ft
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '..')))

from csp_solver import experimenter


SIZE = 8

def build(queen_prob):
    """Eights queens problem -
    place 8 queens on a chess board so that they cannot capture eachother."""

    def no_capture(queen1, queen2, rank1, rank2):
        return abs(rank1 - rank2) != abs(queen1 - queen2) and rank1 != rank2

    queens = list(range(SIZE))   # variables
    ranks = list(range(SIZE))    # domain

    queen_prob.add_variables(queens, ranks)

    # MinConflictsSolver doesn't find solutions with this (redundant with func)
    # still sometimes doesn't
    # queen_prob.add_constraint(cnstr.AllDifferent(), queens)

    for qidx, q1 in enumerate(queens):
        for q2 in queens[qidx + 1:]:
            queen_prob.add_constraint(ft.partial(no_capture, q1, q2),
                                      (q1, q2))  # these are ranks


def show(solution):
    """Print the solution grid."""

    sep_row = '   ' + '-' * ((SIZE * 4) - 1)

    print(sep_row)
    for i in range(SIZE):
        print('  |', end='')
        for j in range(SIZE):
            if solution[j] == i:
                print(f' {j} |', end='')
            else:
                print('   |', end='')
        print()
        if i != SIZE - 1:
            print(sep_row)
    print(sep_row)


# %% main

if __name__ == '__main__':

    experimenter.do_stuff(build, show)
