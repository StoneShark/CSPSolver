# -*- coding: utf-8 -*-
"""Use constraints to solve a sample MasterMind puzzle.
Solution is incremental with new constraints
added after each guess and clue result.

Run these from the MasterMind directory.

Created on Mon Dec 16 09:47:06 2024
@author: Ann"""

# %% imports

from csp_solver import constraint as cnstr
from csp_solver import list_constraint as lcnstr

import master_mind as mmind


# %% problem setup

# 6 positions: 6 colors
puz = mmind.setup(6, 9)

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


# %%     guess 2:  ccbbpp   result:  1 black 1 white

# one is in the right place
puz.add_list_constraint(lcnstr.OneOfCList(),
                          [(cnstr.InValues('c'), '1'),
                           (cnstr.InValues('c'), '2'),
                           (cnstr.InValues('b'), '3'),
                           (cnstr.InValues('b'), '4'),
                           (cnstr.InValues('p'), '5'),
                           (cnstr.InValues('p'), '6')
                           ])

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


# %%     guess 3:  ookkww   result:  2 white

# none is in the right place
puz.add_constraint(cnstr.NotInValues('o'), '12')
puz.add_constraint(cnstr.NotInValues('k'), '34')
puz.add_constraint(cnstr.NotInValues('w'), '56')

# two are in a places not tested
puz.add_list_constraint(lcnstr.NOfCList(2),
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

# we have 6 total clue pegs so we know that there are not more
# than 2 of any color set
puz.add_constraint(cnstr.ExactlyNIn('ryg', 2), '123456')
puz.add_constraint(cnstr.ExactlyNIn('cbp', 2), '123456')
puz.add_constraint(cnstr.ExactlyNIn('okw', 2), '123456')

print('Guess 3')
mmind.get_print_sols(puz)


# %%     guess 4:  rgbpkk   result:  1 black 1 white

# one is in the right place
puz.add_list_constraint(lcnstr.OneOfCList(),
                          [(cnstr.InValues('r'), '1'),
                           (cnstr.InValues('g'), '2'),
                           (cnstr.InValues('b'), '3'),
                           (cnstr.InValues('p'), '4'),
                           (cnstr.InValues('k'), '5'),
                           (cnstr.InValues('k'), '6')
                           ])

# one is in a place it wasn't tested
puz.add_list_constraint(lcnstr.OneOfCList(),
                          [(cnstr.InValues('r'), '2'),
                           (cnstr.InValues('r'), '3'),
                           (cnstr.InValues('r'), '4'),
                           (cnstr.InValues('r'), '5'),
                           (cnstr.InValues('r'), '6'),

                           (cnstr.InValues('g'), '1'),
                           (cnstr.InValues('g'), '3'),
                           (cnstr.InValues('g'), '4'),
                           (cnstr.InValues('g'), '5'),
                           (cnstr.InValues('g'), '6'),

                           (cnstr.InValues('b'), '1'),
                           (cnstr.InValues('b'), '2'),
                           (cnstr.InValues('b'), '4'),
                           (cnstr.InValues('b'), '5'),
                           (cnstr.InValues('b'), '6'),

                           (cnstr.InValues('p'), '1'),
                           (cnstr.InValues('p'), '2'),
                           (cnstr.InValues('p'), '3'),
                           (cnstr.InValues('p'), '5'),
                           (cnstr.InValues('p'), '6'),

                           (cnstr.InValues('k'), '1'),
                           (cnstr.InValues('k'), '2'),
                           (cnstr.InValues('k'), '3'),
                           (cnstr.InValues('k'), '4'),
                           ])

print('Guess 4')
mmind.get_print_sols(puz)

# 348 solutions remain

# %%     guess 5:  rrrppp   result:  2 black

# two are in the right places
puz.add_list_constraint(lcnstr.NOfCList(2),
                          [(cnstr.InValues('r'), '1'),
                           (cnstr.InValues('r'), '2'),
                           (cnstr.InValues('r'), '3'),
                           (cnstr.InValues('p'), '4'),
                           (cnstr.InValues('p'), '5'),
                           (cnstr.InValues('p'), '6')
                           ])

# no white pegs, we can eliminate these possibility
puz.add_constraint(cnstr.NotInValues('r'), '456')
puz.add_constraint(cnstr.NotInValues('p'), '123')

print('Guess 5')
mmind.get_print_sols(puz)

# 39 solutions remain


# %% guess 6: yyyggg     result: 1 white

puz.add_constraint(cnstr.NotInValues('y'), '123')
puz.add_constraint(cnstr.NotInValues('g'), '456')

puz.add_constraint(cnstr.AtMostNIn('y', 1), '123456')
puz.add_constraint(cnstr.AtMostNIn('g', 1), '123456')

print('Guess 6')
mmind.get_print_sols(puz)

# 17 remaining solutions

# %% guess 7:  rwwcpy    result: 4 black, 2 white

# four are in the right places
puz.add_list_constraint(lcnstr.NOfCList(4),
                          [(cnstr.InValues('r'), '1'),
                           (cnstr.InValues('w'), '2'),
                           (cnstr.InValues('w'), '3'),
                           (cnstr.InValues('c'), '4'),
                           (cnstr.InValues('p'), '5'),
                           (cnstr.InValues('y'), '6')
                           ])

# 6 pegs so we can remove colors not included from all domains
puz.add_constraint(cnstr.NotInValues('gbok'), '123456')

# don't think the two white pegs add any additional limits

print('Guess 7')
mmind.get_print_sols(puz)

# 2 remaining solutions

# guessed wrong: rwwcyp

# solution  rwcwpy
