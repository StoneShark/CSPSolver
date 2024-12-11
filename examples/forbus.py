# -*- coding: utf-8 -*-
"""From _Artificial Intelligence_, problem 3-9, Winston, p444

Four problem representations are provided.

Created on Sat May 13 17:14:13 2023
@author: Ann"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '..')))

from csp_solver import constraint as cnstr
from csp_solver import experimenter
from csp_solver import list_constraint as lcnstr


PETER = 'Peter'
PAUL = 'Paul'
JANE = 'Jane'

SAX = 'sax'
GUITAR = 'guitar'
DRUMS = 'drums'

F13 = '13'
CATS = 'cats'
HEIGHTS = 'heights'


def build_one(forbus):
    """From _Artificial Intelligence_, problem 3-9, Winston, p444
    using 3 variable sets and lambda constraints."""

    for i in range(1, 4):
        forbus.add_variable(f'name{i}', (PETER, PAUL, JANE))
        forbus.add_variable(f'play{i}', (SAX, GUITAR, DRUMS))
        forbus.add_variable(f'fear{i}', (F13, CATS, HEIGHTS))

    forbus.add_constraint(cnstr.OneOrder(),
                          [f'name{i}' for i in range(1, 4)])

    forbus.add_constraint(cnstr.AllDifferent(),
                          [f'name{i}' for i in range(1, 4)])
    forbus.add_constraint(cnstr.AllDifferent(),
                          [f'play{i}' for i in range(1, 4)])
    forbus.add_constraint(cnstr.AllDifferent(),
                          [f'fear{i}' for i in range(1, 4)])

    for i in range(1, 4):

        forbus.add_constraint(
            lambda name, play: play != GUITAR or name != PETER,
            [f'name{i}', f'play{i}'])

        forbus.add_constraint(
            lambda name, fear: fear != HEIGHTS or name != PETER,
            [f'name{i}', f'fear{i}'])

        forbus.add_constraint(
            lambda play, fear: play != GUITAR or fear != HEIGHTS,
            [f'play{i}', f'fear{i}'])

        forbus.add_constraint(
            lambda name, fear: fear != CATS or name != PAUL,
            [f'name{i}', f'fear{i}'])

        forbus.add_constraint(
            lambda name, play: play != SAX or name != PAUL,
            [f'name{i}', f'play{i}'])

        forbus.add_constraint(
            lambda play, fear: play != SAX or fear != CATS,
            [f'play{i}', f'fear{i}'])

        forbus.add_constraint(
            lambda play, fear: play != DRUMS or fear != F13,
            [f'play{i}', f'fear{i}'])

        forbus.add_constraint(
            lambda play, fear: play != DRUMS or fear != HEIGHTS,
            [f'play{i}', f'fear{i}'])


def build_two(forbus):
    """From _Artificial Intelligence_, problem 3-9, Winston, p444
    using 2 variable sets and lambda constraints."""

    # pre-assign the names - reduce variable and constraint count
    for name in (PETER, PAUL, JANE):
        forbus.add_variable(f'{name}_plays', (SAX, GUITAR, DRUMS))
        forbus.add_variable(f'{name}_fears', (F13, CATS, HEIGHTS))

    forbus.add_constraint(cnstr.AllDifferent(),
                          [f'{name}_plays' for name in (PETER, PAUL, JANE)])
    forbus.add_constraint(cnstr.AllDifferent(),
                          [f'{name}_fears' for name in (PETER, PAUL, JANE)])

    # These 4 constraints are completely handled by the preprocessing
    forbus.add_constraint(cnstr.NotInValues([GUITAR]), [PETER + '_plays'])
    forbus.add_constraint(cnstr.NotInValues([HEIGHTS]), [PETER + '_fears'])
    forbus.add_constraint(cnstr.NotInValues([CATS]), [PAUL + '_fears'])
    forbus.add_constraint(cnstr.NotInValues([SAX]), [PAUL + '_plays'])

    for name in (PETER, PAUL, JANE):

        forbus.add_constraint(
            lambda play, fear: play != GUITAR or fear != HEIGHTS,
            [f'{name}_plays', f'{name}_fears'])

        forbus.add_constraint(
            lambda play, fear: play != SAX or fear != CATS,
            [f'{name}_plays', f'{name}_fears'])

        forbus.add_constraint(
            lambda play, fear: play != DRUMS or fear != F13,
            [f'{name}_plays', f'{name}_fears'])

        forbus.add_constraint(
            lambda play, fear: play != DRUMS or fear != HEIGHTS,
            [f'{name}_plays', f'{name}_fears'])


def build_three(forbus):
    """From _Artificial Intelligence_, problem 3-9, Winston, p444
    using 2 variable sets and Nand constraints."""

    for name in (PETER, PAUL, JANE):
        forbus.add_variable(f'{name}_plays', (SAX, GUITAR, DRUMS))
        forbus.add_variable(f'{name}_fears', (F13, CATS, HEIGHTS))

    forbus.add_constraint(cnstr.AllDifferent(),
                          [f'{name}_plays' for name in (PETER, PAUL, JANE)])
    forbus.add_constraint(cnstr.AllDifferent(),
                          [f'{name}_fears' for name in (PETER, PAUL, JANE)])

    forbus.add_constraint(cnstr.NotInValues([GUITAR]), [PETER + '_plays'])
    forbus.add_constraint(cnstr.NotInValues([HEIGHTS]), [PETER + '_fears'])

    forbus.add_constraint(cnstr.NotInValues([CATS]), [PAUL + '_fears'])
    forbus.add_constraint(cnstr.NotInValues([SAX]), [PAUL + '_plays'])

    for name in (PETER, PAUL, JANE):

        # Use the Nand instead of the lambdas
        forbus.add_constraint(cnstr.Nand(GUITAR, HEIGHTS),
                              [f'{name}_plays', f'{name}_fears'])

        forbus.add_constraint(cnstr.Nand(SAX, CATS),
                              [f'{name}_plays', f'{name}_fears'])

        forbus.add_constraint(cnstr.Nand(DRUMS, F13),
                              [f'{name}_plays', f'{name}_fears'])

        forbus.add_constraint(cnstr.Nand(DRUMS, HEIGHTS),
                              [f'{name}_plays', f'{name}_fears'])


def build_four(forbus):
    """From _Artificial Intelligence_, problem 3-9, Winston, p444
    using 2 variable sets and list constraints.

    This is a simple example of using ListContraint.
    The Nand solution is a better solution (build 3);
    ListConstraints cannot be preprocessed or forward_checked.
    """

    for name in (PETER, PAUL, JANE):
        forbus.add_variable(f'{name}_plays', (SAX, GUITAR, DRUMS))
        forbus.add_variable(f'{name}_fears', (F13, CATS, HEIGHTS))

    forbus.add_constraint(cnstr.AllDifferent(),
                          [f'{name}_plays' for name in (PETER, PAUL, JANE)])
    forbus.add_constraint(cnstr.AllDifferent(),
                          [f'{name}_fears' for name in (PETER, PAUL, JANE)])

    forbus.add_constraint(cnstr.NotInValues([GUITAR]), [PETER + '_plays'])
    forbus.add_constraint(cnstr.NotInValues([HEIGHTS]), [PETER + '_fears'])

    forbus.add_constraint(cnstr.NotInValues([CATS]), [PAUL + '_fears'])
    forbus.add_constraint(cnstr.NotInValues([SAX]), [PAUL + '_plays'])

    for name in (PETER, PAUL, JANE):

        forbus.add_list_constraint(lcnstr.OrCList(),
            [(cnstr.NotInValues([GUITAR]), [f'{name}_plays']),
             (cnstr.NotInValues([HEIGHTS]),[f'{name}_fears'])])

        forbus.add_list_constraint(lcnstr.OrCList(),
            [(cnstr.NotInValues([SAX]), [f'{name}_plays']),
             (cnstr.NotInValues([CATS]),[f'{name}_fears'])])

        forbus.add_list_constraint(lcnstr.OrCList(),
            [(cnstr.NotInValues([DRUMS]), [f'{name}_plays']),
             (cnstr.NotInValues([F13]),[f'{name}_fears'])])

        forbus.add_list_constraint(lcnstr.OrCList(),
            [(cnstr.NotInValues([DRUMS]), [f'{name}_plays']),
             (cnstr.NotInValues([HEIGHTS]),[f'{name}_fears'])])


def show_solution(solution):
    """Show solution based on variable set."""

    if 'name1' in solution:
        print()
        print('Name      Plays     Fears')
        print('----------------------------')
        for i in range(1, 4):
            for val in (solution[f'name{i}'],
                        solution[f'play{i}'],
                        solution[f'fear{i}']):
                print(f'{val:10}', end='')
            print()
        print()

    else:
        print()
        print('Name      Plays     Fears')
        print('----------------------------')
        for name in (PETER, PAUL, JANE):
            for val in (name,
                        solution[f'{name}_plays'],
                        solution[f'{name}_fears']):
                print(f'{val:10}', end='')
            print()
        print()


# %% main

if __name__ == '__main__':

    experimenter.do_stuff([build_one, build_two, build_three, build_four],
                          show_solution)
