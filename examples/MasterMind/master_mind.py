# -*- coding: utf-8 -*-
"""Use constraints to solve MasterMind puzzles.

The example solutions make required use of SetConstraints
and ListConstraint classes.

Created on Sun Dec 15 07:30:15 2024
@author: Ann"""

import csp_solver as csp


POSITIONS = '123456'

# red, yellow, green, cyan, blue, purple, orange, blacK and white
COLORS = 'rygcbpokw'


def setup(positions, colors):
    """Create a mastermind problem with positions and colors"""

    mmind = csp.Problem()

    mmind.add_variables(POSITIONS[:positions],
                        COLORS[:colors])
    return mmind


def get_print_sols(mmind):
    """Get the solutions, print how many remain
    and possibly print them."""

    sols =  mmind.get_all_solutions()

    if sols:
        nsols = len(sols)
        print(f"Print {nsols} solutions remain.")

    if sols and nsols:
        nvars= len(sols[0]) + 1

        if nsols < 20:
            for sol in sols:
                print(''.join(sol[str(i)] for i in range(1, nvars)))

    mmind.print_domains()
