# -*- coding: utf-8 -*-
"""Use constraints to solve a sample MasterMind puzzle.
Solution is incremental with new constraints
added after each guess and clue result.

Run these from the MasterMind directory.

Created on Mon Dec 16 10:34:59 2024
@author: Ann"""


# %% imports

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '../..')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from csp_solver import constraint as cnstr
from csp_solver import list_constraint as lcnstr
from csp_solver import var_chooser

import master_mind as mmind


# %% run the file as the test

'__test_example__'


# %% problem setup

# 6 positions: 9 colors
puz = mmind.setup(6, 9)

puz.enable_forward_check()
puz.var_chooser = var_chooser.MinDomain


mmind.get_print_sols(puz)

# 531441 solutions to this puzzle

# %%     guess 1:  rryygg   result:  1 black 1 white

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

print('Guess 1')
mmind.get_print_sols(puz)

# 777760 remaining

# %% guess 2:  ccbbpp     restult: 1 white

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

print('Guess 2')
mmind.get_print_sols(puz)

# 12960 remaining

# %% guess 3:  ookkww     restult: 3 white

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

print('Guess 3')
mmind.get_print_sols(puz)

# 3552 remaining

# %%  guess 4:  rrrryy   result: 1 black

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

print('Guess 4')
mmind.get_print_sols(puz)

#   704 solution

# %%  guess 5: rgcokk  result: 2 whites

puz.add_constraint(cnstr.ExactlyNIn('rgcok', 2), '123456')

puz.add_constraint(cnstr.NotInValues('r'), '1')
puz.add_constraint(cnstr.NotInValues('g'), '2')
puz.add_constraint(cnstr.NotInValues('c'), '3')
puz.add_constraint(cnstr.NotInValues('o'), '4')
puz.add_constraint(cnstr.NotInValues('k'), '56')

# two are in places not tested
#  domains already limited to this, nbr sols unchanged
# puz.add_list_constraint(lcnstr.NOfCList(2),
#                           [ # already know r can't be in 56 (guess 4)
#                            (cnstr.InValues('r'), '2'),
#                            (cnstr.InValues('r'), '3'),
#                            (cnstr.InValues('r'), '4'),

#                            (cnstr.InValues('g'), '1'),
#                            (cnstr.InValues('g'), '3'),
#                            (cnstr.InValues('g'), '4'),
#                            (cnstr.InValues('g'), '5'),
#                            (cnstr.InValues('g'), '6'),

#                            # already know c can't be in 12 (guess 2)
#                            (cnstr.InValues('c'), '4'),
#                            (cnstr.InValues('c'), '5'),
#                            (cnstr.InValues('c'), '6'),

#                            # already know o can't be in 12 (guess 3)
#                            (cnstr.InValues('o'), '3'),
#                            (cnstr.InValues('o'), '5'),
#                            (cnstr.InValues('o'), '6'),

#                            # already know k can't be in 34 (guess 3)
#                            (cnstr.InValues('k'), '1'),
#                            (cnstr.InValues('k'), '2'),
#                            ])

print('Guess 5')
mmind.get_print_sols(puz)

# 26 solutions


# %%  guess 6: bkwwyg  result: 4 black 1 white

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

print('Guess 6')
mmind.get_print_sols(puz)

# 4 solutions

# %% guess 7:  wkpwyg   3 black 3 white

puz.add_constraint(cnstr.InValues('kpwyg'), '123456')

puz.add_list_constraint(lcnstr.NOfCList(3),
                          [(cnstr.InValues('w'), '1'),
                           (cnstr.InValues('k'), '2'),
                           (cnstr.InValues('p'), '3'),
                           (cnstr.InValues('w'), '4'),
                           (cnstr.InValues('y'), '5'),
                           (cnstr.InValues('g'), '6')
                           ])

print('Guess 7')
mmind.get_print_sols(puz)


# solution is kpwwyg
