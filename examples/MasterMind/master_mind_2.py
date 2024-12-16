# -*- coding: utf-8 -*-
"""Use constraints to solve a sample MasterMind puzzle.
Solution is incremental with new constraints
added after each guess and clue result.

Run these from the MasterMind directory.

Created on Sun Dec 15 08:38:25 2024
@author: Ann"""

# %% imports

from csp_solver import constraint as cnstr
from csp_solver import list_constraint as lcnstr

import master_mind as mmind


# %% problem setup

# 4 positions: 6 colors
puz = mmind.setup(4, 6)

mmind.get_print_sols(puz)


# %%     guess 1:  rryy   3 white

# we can eliminate one assignment set
puz.add_constraint(cnstr.NotInValues('r'), '12')
puz.add_constraint(cnstr.NotInValues('y'), '34')

# 3 of the assignments are ry, but not in pos tested
puz.add_list_constraint(lcnstr.AtLeastNCList(3),
                          [(cnstr.InValues('y'), '1'),
                           (cnstr.InValues('y'), '2'),
                           (cnstr.InValues('r'), '3'),
                           (cnstr.InValues('r'), '4')])

# 1 of the assignments must be gcbp
puz.add_constraint(cnstr.ExactlyNIn('gcbp', 1), '1234')

print('Guess 1')
mmind.get_print_sols(puz)


# %%     guess 2:  ggcc   1 white

# have 4 pegs in non-overlapping guesses: we know untested colors are not used
puz.add_constraint(cnstr.NotInValues('bp'), '1234')

# we can eliminate the assignments
puz.add_constraint(cnstr.NotInValues('g'), '1')
puz.add_constraint(cnstr.NotInValues('g'), '2')
puz.add_constraint(cnstr.NotInValues('c'), '3')
puz.add_constraint(cnstr.NotInValues('c'), '4')

# 1 of the assignments is gc, but not in pos tested
puz.add_list_constraint(lcnstr.AtLeastNCList(1),
                          [(cnstr.InValues('c'), '1'),
                           (cnstr.InValues('c'), '2'),
                           (cnstr.InValues('g'), '3'),
                           (cnstr.InValues('g'), '4')])

print('Guess 2')
mmind.get_print_sols(puz)


# %%     guess 3:  yygr   2 black

# two assignments are right
puz.add_list_constraint(lcnstr.NOfCList(2),
                          [(cnstr.InValues('y'), '1'),
                           (cnstr.InValues('y'), '2'),
                           (cnstr.InValues('g'), '3'),
                           (cnstr.InValues('r'), '4')])

# no white pegs, so yyrg is not a solution:

#    only one peg may be yellow
puz.add_constraint(cnstr.ExactlyNIn('y', 1), '12')

#    and pegs 3 and 4 must be red
puz.add_constraint(cnstr.InValues('r'), '34')


print('Guess 3')
mmind.get_print_sols(puz)


# %%     guess 4:  ycrr   2 black, 2 white

puz.add_constraint(cnstr.NotInValues('y'), '1')
puz.add_constraint(cnstr.NotInValues('c'), '2')

print('Guess 4')
mmind.get_print_sols(puz)


# solution is c y r r
