# -*- coding: utf-8 -*-
"""Setup master_mind_6 for use with the experimenter.

Each build contains an extra guess: build 1 contains first
guess, build 2 contains first and second guess, etc.

Filename must not contain master_mind_6 or it will be marked slow.

Created on Mon Dec 16 10:34:59 2024
@author: Ann"""

import functools as ft
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '../..')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import csp_solver as csp
from csp_solver import constraint as cnstr
from csp_solver import experimenter
from csp_solver import list_constraint as lcnstr
from csp_solver import solver
from csp_solver import var_chooser

import master_mind as mmind


def add_guess_1(puz):

    # guess 1:  rryygg   result:  1 black 1 white
    # one is in the right place
    puz.add_list_constraint(lcnstr.OneOfCList(),
                              [(cnstr.InValues('r'), '1'),
                               (cnstr.InValues('r'), '2'),
                               (cnstr.InValues('y'), '3'),
                               (cnstr.InValues('y'), '4'),
                               (cnstr.InValues('g'), '5'),
                               (cnstr.InValues('g'), '6')
                               ])

    # one is in a place it wasn't tested
    puz.add_list_constraint(lcnstr.OneOfCList(),
                              [(cnstr.InValues('r'), '3'),
                               (cnstr.InValues('r'), '4'),
                               (cnstr.InValues('r'), '5'),
                               (cnstr.InValues('r'), '6'),

                               (cnstr.InValues('y'), '1'),
                               (cnstr.InValues('y'), '2'),
                               (cnstr.InValues('y'), '5'),
                               (cnstr.InValues('y'), '6'),

                               (cnstr.InValues('g'), '1'),
                               (cnstr.InValues('g'), '2'),
                               (cnstr.InValues('g'), '3'),
                               (cnstr.InValues('g'), '4')
                               ])

    # tested two of each, but it doesn't constrain the solution more
    puz.add_constraint(cnstr.AtLeastNIn('ryg', 2), '123456')


def add_guess_2(puz):

    # guess 2:  ccbbpp     restult: 1 white
    # none is in the right place
    puz.add_constraint(cnstr.NotInValues('c'), '12')
    puz.add_constraint(cnstr.NotInValues('b'), '34')
    puz.add_constraint(cnstr.NotInValues('p'), '56')

    puz.add_constraint(cnstr.ExactlyNIn('cbp', 1), '123456')

    # one is in a place it wasn't tested
    puz.add_list_constraint(lcnstr.OneOfCList(),
                              [(cnstr.InValues('c'), '3'),
                               (cnstr.InValues('c'), '4'),
                               (cnstr.InValues('c'), '5'),
                               (cnstr.InValues('c'), '6'),

                               (cnstr.InValues('b'), '1'),
                               (cnstr.InValues('b'), '2'),
                               (cnstr.InValues('b'), '5'),
                               (cnstr.InValues('b'), '6'),

                               (cnstr.InValues('p'), '1'),
                               (cnstr.InValues('p'), '2'),
                               (cnstr.InValues('p'), '3'),
                               (cnstr.InValues('p'), '4')
                               ])


def add_guess_3(puz):

    # guess 3:  ookkww     restult: 3 white
    # none is in the right place
    puz.add_constraint(cnstr.NotInValues('o'), '12')
    puz.add_constraint(cnstr.NotInValues('k'), '34')
    puz.add_constraint(cnstr.NotInValues('w'), '56')

    # have 6 total clue pegs so we know for certain there are not 3 or more
    # of any color   and can refine ryg const to Exactly
    puz.add_constraint(cnstr.ExactlyNIn('okw', 3), '123456')
    puz.add_constraint(cnstr.ExactlyNIn('ryg', 2), '123456')

    puz.add_constraint(cnstr.AtMostNIn('r', 2), '123456')
    puz.add_constraint(cnstr.AtMostNIn('y', 2), '123456')
    puz.add_constraint(cnstr.AtMostNIn('g', 2), '123456')
    puz.add_constraint(cnstr.AtMostNIn('o', 2), '123456')
    puz.add_constraint(cnstr.AtMostNIn('k', 2), '123456')
    puz.add_constraint(cnstr.AtMostNIn('w', 2), '123456')

    # three colors are in locations not tested
    puz.add_list_constraint(lcnstr.NOfCList(3),
                              [(cnstr.InValues('o'), '3'),
                               (cnstr.InValues('o'), '4'),
                               (cnstr.InValues('o'), '5'),
                               (cnstr.InValues('o'), '6'),

                               (cnstr.InValues('k'), '1'),
                               (cnstr.InValues('k'), '2'),
                               (cnstr.InValues('k'), '5'),
                               (cnstr.InValues('k'), '6'),

                               (cnstr.InValues('w'), '1'),
                               (cnstr.InValues('w'), '2'),
                               (cnstr.InValues('w'), '3'),
                               (cnstr.InValues('w'), '4')
                               ])


def add_guess_4(puz):

    #  guess 4:  rrrryy   result: 1 black
    # we know 1 green is used (guess 1 and this one)
    puz.add_constraint(cnstr.ExactlyNIn('g', 1), '123456')

    # we know 1 of red or yellow is used
    puz.add_constraint(cnstr.ExactlyNIn('ry', 1), '123456')

    # would have gotten white pegs for these
    puz.add_constraint(cnstr.NotInValues('r'), '56')
    puz.add_constraint(cnstr.NotInValues('y'), '1234')

    # one is in the right place
    puz.add_list_constraint(lcnstr.OneOfCList(),
                              [(cnstr.InValues('r'), '1'),
                               (cnstr.InValues('r'), '2'),
                               (cnstr.InValues('r'), '3'),
                               (cnstr.InValues('r'), '4'),
                               (cnstr.InValues('y'), '5'),
                               (cnstr.InValues('y'), '6')
                               ])

def add_guess_5(puz):

    #  guess 5: rgcokk  result: 2 whites
    puz.add_constraint(cnstr.ExactlyNIn('rgcok', 2), '123456')

    puz.add_constraint(cnstr.NotInValues('r'), '1')
    puz.add_constraint(cnstr.NotInValues('g'), '2')
    puz.add_constraint(cnstr.NotInValues('c'), '3')
    puz.add_constraint(cnstr.NotInValues('o'), '4')
    puz.add_constraint(cnstr.NotInValues('k'), '56')


def add_guess_6(puz):

    #  guess 6: bkwwyg  result: 4 black 1 white
    # 5 of these colors are used
    puz.add_constraint(cnstr.ExactlyNIn('bkwyg', 5), '123456')

    # one of the missing colors is used once
    puz.add_constraint(cnstr.ExactlyNIn('rcpo', 1), '123456')

    puz.add_list_constraint(lcnstr.NOfCList(4),
                              [(cnstr.InValues('b'), '1'),
                               (cnstr.InValues('k'), '2'),
                               (cnstr.InValues('w'), '3'),
                               (cnstr.InValues('w'), '4'),
                               (cnstr.InValues('y'), '5'),
                               (cnstr.InValues('g'), '6')
                               ])


def add_guess_7(puz):

    # guess 7:  wkpwyg   3 black 3 white
    puz.add_constraint(cnstr.InValues('kpwyg'), '123456')

    puz.add_list_constraint(lcnstr.NOfCList(3),
                              [(cnstr.InValues('w'), '1'),
                               (cnstr.InValues('k'), '2'),
                               (cnstr.InValues('p'), '3'),
                               (cnstr.InValues('w'), '4'),
                               (cnstr.InValues('y'), '5'),
                               (cnstr.InValues('g'), '6')
                               ])



def build(nguess, puz):

    puz.add_variables(mmind.POSITIONS[:6],
                      mmind.COLORS[:9])

    puz.solver = solver.NonRecBacktracking()
    puz.enable_forward_check()
    puz.var_chooser = var_chooser.MinDomain

    add_guess_1(puz)
    if nguess >= 2: add_guess_2(puz)
    if nguess >= 3: add_guess_3(puz)
    if nguess >= 4: add_guess_4(puz)
    if nguess >= 5: add_guess_5(puz)
    if nguess >= 6: add_guess_6(puz)
    if nguess >= 7: add_guess_7(puz)


def show(sol, _=None):

    nvars= len(sol) + 1
    print(''.join(sol[str(i)] for i in range(1, nvars)))



# %% main

build_funcs = []
for bnbr in range(1, 8):
    bfunc = ft.partial(build, bnbr)
    bfunc.__name__ = f'guesses_{bnbr}'
    bfunc.__doc__ = f'Master Mind 6 with {bnbr} guesses.'
    build_funcs += [bfunc]


if __name__ == '__main__':

    experimenter.do_stuff(build_funcs, show)


if __name__ == '__test_example__':

    bprob = csp.Problem()
    build(7, bprob)
    sol = bprob.get_solution()
    show(sol)
