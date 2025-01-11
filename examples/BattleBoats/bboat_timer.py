# -*- coding: utf-8 -*-
"""A test that sums up the run time of bboat CSP
into a single number.  All of the human curated
puzzles are used.

Created on Thu Jan  9 15:57:39 2025
@author: Ann"""

import argparse
import functools as ft
import os
import sys
import timeit

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '../..')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import bboat_cnstr
import bboat_extra
import csp_solver as csp

RUN_FIRST = 13
NBR_RUNS_PER = 3


def parse_command_line():
    """Define and parse the command line options.
    Return the cargs."""

    parser = argparse.ArgumentParser(
        usage='%(prog)s [--help] [options]',
        description="""%(prog)s accumulates the total solve time
        of running the first 13 puzzles 3 times each.
        Prints the average solve time.
        """)

    parser.add_argument('--extra', action='store_true',
                        help="""Run bboat_extra instead of bboat_cnstr.""")

    parser.add_argument('--all', action='store_true',
                        help="""Find all solutions.""")

    parser.add_argument('--progress', action='store_true',
                        help="""Show progress prints.""")

    try:
        cargs = parser.parse_args()
    except argparse.ArgumentError:
        parser.print_help()
        sys.exit()

    return cargs


if __name__ == '__main__':

    total = 0
    cargs = parse_command_line()

    if cargs.extra:
        bb_puz_def = bboat_extra.builds
        puz = 'extra'
    else:
        bb_puz_def =  bboat_cnstr.builds
        puz = 'cnstr'

    if cargs.all:
        solve_method = csp.Problem.get_all_solutions
    else:
        solve_method = csp.Problem.get_solution


    for bnbr, build_func in enumerate(bb_puz_def[:RUN_FIRST]):

        if cargs.progress:
            print(f'\n{bnbr + 1} {puz}: ', build_func.__doc__)

        for nbr in range(NBR_RUNS_PER):

            # the problem must be rebuilt for each solve
            # don't include that time
            prob = csp.problem.Problem()
            build_func(prob)
            solve_func = ft.partial(solve_method, prob)
            time = timeit.timeit(solve_func, number=1)
            total += time

            if cargs.progress:
                print(f'Run {nbr}: {time}')

    ave_run_time = total / RUN_FIRST / NBR_RUNS_PER
    print(f'\nAverage time per solve {ave_run_time} ({puz})')


if __name__ == '__test_example__':

    skipped = True
    reason = 'Analysis module'
