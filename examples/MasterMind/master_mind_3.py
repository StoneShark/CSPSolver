# -*- coding: utf-8 -*-
"""Use constraints to solve a sample MasterMind puzzle.
Solution is incremental with new constraints
added after each guess and clue result.

Run these from the MasterMind directory.

Created on Sun Dec 15 09:47:40 2024
@author: Ann"""

# %% imports

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '../..')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from csp_solver import constraint as cnstr
from csp_solver import list_constraint as lcnstr

import master_mind as mmind


# %% run the file as the test

'__test_example__'


# %%  setup

puz = mmind.setup(4, 9)

mmind.get_print_sols(puz)


# %%  rryy  no pegs

puz.add_constraint(cnstr.NotInValues('ry'), '1234')
print("\n Guess: rryy")
mmind.get_print_sols(puz)


# %%  ggcc  no pegs

puz.add_constraint(cnstr.NotInValues('gc'), '1234')
print("\n Guess: ggcc")
mmind.get_print_sols(puz)


# %%  bbpp  1 black

# would have gotten white peg(s), for either of these
puz.add_constraint(cnstr.NotInValues('b'), '34')
puz.add_constraint(cnstr.NotInValues('p'), '12')

# one of guess is right
puz.add_list_constraint(lcnstr.NOfCList(1),
                        [(cnstr.InValues('b'), '1'),
                         (cnstr.InValues('b'), '2'),
                         (cnstr.InValues('p'), '3'),
                         (cnstr.InValues('p'), '4')])

print("\n Guess: bbpp")
mmind.get_print_sols(puz)


# %%  ookk  1 black, 2 white

# have 4 total pegs, white is not used
puz.add_constraint(cnstr.NotInValues('w'), '1234')

# one of guess in right place
puz.add_list_constraint(lcnstr.NOfCList(1),
                        [(cnstr.InValues('o'), '1'),
                         (cnstr.InValues('o'), '2'),
                         (cnstr.InValues('k'), '3'),
                         (cnstr.InValues('k'), '4')])

# cannot have more than two of either orange or black (4 total pegs)
puz.add_constraint(cnstr.AtMostNIn('o', 2), '1234')
puz.add_constraint(cnstr.AtMostNIn('k', 2), '1234')

print("\nGuess: ookk")
mmind.get_print_sols(puz)


# %%    koop   4 whites

# have 4 pegs in clue, blue is not used
puz.add_constraint(cnstr.NotInValues('b'), '1234')

# we can eliminate one assignment set
puz.add_constraint(cnstr.NotInValues('k'), '1')
puz.add_constraint(cnstr.NotInValues('o'), '2')
puz.add_constraint(cnstr.NotInValues('o'), '3')
puz.add_constraint(cnstr.NotInValues('p'), '4')

print("\nGuess: koop")
mmind.get_print_sols(puz)


# answer is okpo
