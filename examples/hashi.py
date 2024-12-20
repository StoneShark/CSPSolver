# -*- coding: utf-8 -*-
"""A Hashiwokaker solver.
Puzzles and rules at https://www.hashi.info/

Variables are possible bridge locations between islands.
Domain is the number of bridged between each (0, 1 or 3).

Constraints:
    ExactSums for number of bridges out of each island
    Or for bridge locations that would cross
    BoolFunction to test if all islands are connected

Created on Wed Dec 18 07:19:07 2024
@author: Ann"""

# %% imports

import functools as ft
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '..')))
import csp_solver as csp
from csp_solver import constraint as cnstr
from csp_solver import experimenter


# %%  constants

VALS = 'abcdefghijk'

IDX = {val: idx for idx, val in enumerate(VALS)}

ROW = 0
COL = 1


# %%  problem grid  - grid used by both build and print_sol


grid1 = [[1, 0, 3, 0, 0, 2, 0],
         [0, 0, 0, 0, 0, 0, 1],
         [0, 0, 0, 1, 0, 2, 0],
         [3, 0, 6, 0, 4, 0, 3],
         [0, 1, 0, 2, 0, 0, 0],
         [2, 0, 2, 0, 1, 0, 0],
         [0, 2, 0, 4, 0, 0, 2]]

grid2 = [[2, 0, 0, 2, 0, 4, 0, 0, 4, 0, 2],
         [0, 3, 0, 0, 2, 0, 0, 0, 0, 0, 0],
         [0, 0, 0, 0, 0, 2, 0, 0, 6, 0, 5],
         [3, 0, 1, 0, 4, 0, 0, 1, 0, 0, 0],
         [0, 4, 0, 2, 0, 0, 0, 0, 0, 1, 0],
         [3, 0, 1, 0, 2, 0, 3, 0, 2, 0, 3],
         [0, 2, 0, 0, 0, 0, 0, 1, 0, 3, 0],
         [0, 0, 0, 2, 0, 0, 4, 0, 1, 0, 2],
         [2, 0, 2, 0, 0, 3, 0, 0, 0, 0, 0],
         [0, 1, 0, 0, 0, 0, 2, 0, 0, 2, 0],
         [2, 0, 2, 0, 0, 4, 0, 3, 0, 0, 2],
         ]


grids = [grid1, grid2]

# %% all_connected

def all_connected(islands, expected, arg_dict):
    """Determine if all of the nodes are connected.

    Do this by picking a node and seeing if we can
    travel across bridges to all the islands.

    var_args was true in the constraint so that we get
    the assignment dictionary (otherwise we need to
    know the order of the nodes).
    Return True until we have all the assignments
    (expected is the right number).

    Algorithm:

    Pick an island, put it in to_expand.
    While nodes to_expand:
        Pop an isle from the to_expand set and add it to
        the visited set.
        When we have the visited all the islands, return True.

        Find all of the neighbors with bridges to them from the popped isle,
            if they have been visited do nothing
            if they have not been visited add to the to_expand set.

    If we exit the loops without returning True, return False.
    """

    if len(arg_dict) < expected:
        return True

    nislands = len(islands)
    to_expand = set([islands[0]])
    visited = set()

    while to_expand:

        isle = to_expand.pop()

        visited |= set([isle])
        if len(visited) == nislands:
            return True

        for node, cnt in arg_dict.items():
            if not cnt:
                continue

            end1 = node[:2]
            end2 = node[2:]

            if isle == end1 and end2 not in visited:
                to_expand |= set([end2])

            elif isle == end2 and end1 not in visited:
                to_expand |= set([end1])

    return False


# %% define and print csp

def build(build_nbr, prob):
    """Build a hashi puzzle."""

    isle_cnts = {VALS[idx] + VALS[idy]: cnt
                 for idx, row in enumerate(grids[build_nbr])
                 for idy, cnt in enumerate(row)
                 if cnt}
    islands = list(isle_cnts.keys())
    nislands = len(islands)

    # compute nodes -- possible bridges between islands
    # first point is always alpha-sort-order less than second
    nodes = []
    verts = []
    horzs = []
    for idi, isle in enumerate(islands):

        if idi + 1 < nislands and islands[idi + 1][ROW] == isle[ROW]:
            nodes += [isle + islands[idi + 1]]
            horzs += [isle + islands[idi + 1]]

        for nisle in islands[idi+1:]:
            if nisle[COL] == isle[COL]:
                nodes += [isle + nisle]
                verts += [isle + nisle]
                break

    prob.add_variables(nodes, [0, 1, 2])

    # each isle must have cnt number of bridges in/out
    for isle, cnt in isle_cnts.items():
        neighs = [bdg for bdg in nodes if bdg[:2] == isle or bdg[2:] == isle]
        prob.add_constraint(cnstr.ExactSum(cnt), neighs)

    # bridges cannot cross, relies on node point order (see above)
    for vert in verts:
        for horz in horzs:
            if vert[0] < horz[0] < vert[2] and horz[1] < vert[1] < horz[3]:
                prob.add_constraint(cnstr.Or(0, 0), [vert, horz])

    # all islands must be connected to eachother
    # var_args is True to pass the assignment dict (positional
    # arguments would be messy to decode), the actual test
    # isn't done until all the assignments are made
    prob.add_constraint(
        cnstr.BoolFunction(ft.partial(all_connected, islands, len(nodes)),
                            True),
        nodes)


def print_sol(sol, build_nbr):

    pgrid = [row[:] for row in grids[build_nbr]]

    for node, bridges in sol.items():

        if not bridges:
            continue

        row1 = IDX[node[0]]
        col1 = IDX[node[1]]
        row2 = IDX[node[2]]
        col2 = IDX[node[3]]

        if row1 == row2:
            for col in range(col1 + 1, col2):
                pgrid[row1][col] = '\u2550' if bridges == 2 else '\u2500'

        elif col1 == col2:
            for row in range(row1 + 1, row2):
                pgrid[row][col1] = '\u2551' if bridges == 2 else '\u2502'

    for row in pgrid:
        for val in row:
            print(val if val else ' ', end=' ')
        print()


# %% main

build_funcs = []
for bnbr in range(len(grids)):
    bfunc = ft.partial(build, bnbr)
    bfunc.__name__ = f'build({bnbr}, '
    build_funcs += [bfunc]


if __name__ == '__main__':

    experimenter.do_stuff(build_funcs, print_sol)


if __name__ == '__test_example__':

    for bnbr, _ in enumerate(grids):

        print(f'\nSolving grid {bnbr}')
        bprob = csp.Problem()
        build(bnbr, bprob)
        sol = bprob.get_solution()
        print_sol(sol, bnbr)
