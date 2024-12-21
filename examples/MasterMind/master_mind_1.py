# -*- coding: utf-8 -*-
"""Use constraints to solve a sample MasterMind puzzle.
Solution is incremental with new constraints
added after each guess and clue result.

Run these from the MasterMind directory.

Created on Sun Dec 15 07:30:15 2024
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


# %% problem setup

# 4 positions: 6 colors
puz = mmind.setup(4, 6)

mmind.get_print_sols(puz)


# %%     guess 1:  r y g c  result: 2 white

# we can eliminate one assignment set
puz.add_constraint(cnstr.NotInValues('r'), '1')
puz.add_constraint(cnstr.NotInValues('y'), '2')
puz.add_constraint(cnstr.NotInValues('g'), '3')
puz.add_constraint(cnstr.NotInValues('c'), '4')

# exactly two of the colors are used, but possibly in mult places
puz.add_constraint(cnstr.AtLeastNIn('rygc', 2), '1234')

print('Guess 1')
mmind.get_print_sols(puz)

# %%    guess 2: b p r y    result:   none

# can eliminate all four colors
puz.add_constraint(cnstr.NotInValues('bpry'), '1234')

print('Guess 2')
mmind.get_print_sols(puz)


# %%  guess 3: g g c g    result:  2 black

puz.add_list_constraint(lcnstr.NOfCList(2),
                          [(cnstr.InValues('g'), '1'),
                           (cnstr.InValues('g'), '2'),
                           (cnstr.InValues('c'), '3'),
                           (cnstr.InValues('g'), '4')])
print('Guess 3')
mmind.get_print_sols(puz)


# solution is:   c c c g
