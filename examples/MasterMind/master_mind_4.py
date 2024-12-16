# -*- coding: utf-8 -*-
"""Use constraints to solve a sample MasterMind puzzle.
Solution is incremental with new constraints
added after each guess and clue result.

Run these from the MasterMind directory.

Created on Sun Dec 15 10:25:28 2024
@author: Ann"""

# %% imports

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '../..')))
from csp_solver import constraint as cnstr
from csp_solver import list_constraint as lcnstr

import master_mind as mmind

# %%  setup

puz = mmind.setup(4, 6)

mmind.get_print_sols(puz)


# %%  rryy  1 white

puz.add_constraint(cnstr.NotInValues('r'), '12')
puz.add_constraint(cnstr.NotInValues('y'), '34')

puz.add_constraint(cnstr.ExactlyNIn('ry', 1), '1234')

mmind.get_print_sols(puz)


# %% ggcc  1 black 1 white

# assignments could include gg, cc, gc, or gc, OR ggg or ccc
puz.add_constraint(cnstr.AtLeastNIn('bg', 2), '1234')

# one of guess in right place
puz.add_list_constraint(lcnstr.NOfCList(1),
                        [(cnstr.InValues('g'), '1'),
                         (cnstr.InValues('g'), '2'),
                         (cnstr.InValues('c'), '3'),
                         (cnstr.InValues('c'), '4')])

# one of guess is in wrong place, so must be on opp side
puz.add_list_constraint(lcnstr.NOfCList(1),
                        [(cnstr.InValues('c'), '1'),
                         (cnstr.InValues('c'), '2'),
                         (cnstr.InValues('g'), '3'),
                         (cnstr.InValues('g'), '4')])

mmind.get_print_sols(puz)


# %%  bbpp  1 white

puz.add_constraint(cnstr.NotInValues('b'), '12')
puz.add_constraint(cnstr.NotInValues('p'), '34')

puz.add_constraint(cnstr.ExactlyNIn('bp', 1), '1234')

mmind.get_print_sols(puz)


# %%  yggb  1 black 1 white

puz.add_constraint(cnstr.ExactlyNIn('ybg', 2), '1234')

# one of guess in right place
puz.add_list_constraint(lcnstr.NOfCList(1),
                        [(cnstr.InValues('y'), '1'),
                         (cnstr.InValues('g'), '2'),
                         (cnstr.InValues('g'), '3'),
                         (cnstr.InValues('b'), '4')])
mmind.get_print_sols(puz)


# %%  pgrg  1 black 1 white

puz.add_constraint(cnstr.AtLeastNIn('rgp', 2, exact=True), '1234')

# one of guess in right place
puz.add_list_constraint(lcnstr.NOfCList(1),
                        [(cnstr.InValues('p'), '1'),
                         (cnstr.InValues('g'), '2'),
                         (cnstr.InValues('r'), '3'),
                         (cnstr.InValues('g'), '4')])
mmind.get_print_sols(puz)


# %%  gcrb

# that's the solution (it was 50-50)
