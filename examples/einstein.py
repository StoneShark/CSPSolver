# -*- coding: utf-8 -*-
"""ALBERT EINSTEIN'S RIDDLE

1. In a street there are five houses, painted five different colours.
2. In each house lives a person of different nationality
3. These five homeowners each drink a different kind of beverage, smoke
different brand of cigar, and keep a different pet.

Question: who owns the fish?

Clues

1. The Brit lives in a red house.
2. The Swede keeps dogs as pets.
3. The Dane drinks tea.
4. The Green house is on the left of the White house.
5. The owner of the Green house drinks coffee.
6. The person who smokes Pall Mall rears birds.
7. The owner of the Yellow house smokes Dunhill.
8. The man living in the centre house drinks milk.
9. The Norwegian lives in the first house.
10. The man who smokes Blends lives next to the one who keeps cats.
11. The man who keeps horses lives next to the man who smokes Dunhill.
12. The man who smokes Blue Master drinks beer.
13. The German smokes Prince.
14. The Norwegian lives next to the blue house.
15. The man who smokes Blends has a neighbour who drinks water.

Examples of using the experimenter:

python einstein.py --solver all
python einstein.py --var_chooser all
python einstein.py --solver NonRecBacktracking
python einstein.py --solver NonRecBacktracking --forward
python einstein.py --forward

Created on Wed May  3 15:02:43 2023
@author: Ann"""

# %% imports

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '..')))
import csp_solver as csp
from csp_solver import constraint as cnstr
from csp_solver import experimenter


# %% problem statement

def build(eproblem):
    """Albert Einstein's Riddle."""

    for i in range(1, 6):
        eproblem.add_variable(
            f'color{i}',
            ['red', 'white', 'green', 'yellow', 'blue'])
        eproblem.add_variable(
            f'nationality{i}',
            ['brit', 'swede', 'dane', 'norwegian', 'german'])
        eproblem.add_variable(
            f'drink{i}',
            ['tea', 'coffee', 'milk', 'beer', 'water'])
        eproblem.add_variable(
            f'smoke{i}',
            ['pallmall', 'dunhill', 'blends', 'bmaster', 'prince'])
        eproblem.add_variable(
            f'pet{i}',
            ['dogs', 'birds', 'cats', 'horses', 'fish'])

    eproblem.add_constraint(
        cnstr.AllDifferent(), [f'color{i}' for i in range(1, 6)])
    eproblem.add_constraint(
        cnstr.AllDifferent(), [f'nationality{i}' for i in range(1, 6)])
    eproblem.add_constraint(
        cnstr.AllDifferent(), [f'drink{i}' for i in range(1, 6)])
    eproblem.add_constraint(
        cnstr.AllDifferent(), [f'smoke{i}' for i in range(1, 6)])
    eproblem.add_constraint(
        cnstr.AllDifferent(), [f'pet{i}' for i in range(1, 6)])

    # Clues 8 & 9
    eproblem.add_constraint(cnstr.InValues(['milk']), ['drink3'])
    eproblem.add_constraint(cnstr.InValues(['norwegian']), ['nationality1'])

    for i in range(1, 6):

        # Clues 1 - 3
        eproblem.add_constraint(cnstr.IfThen('brit', 'red'),
                                [f'nationality{i}', f'color{i}'])
        eproblem.add_constraint(cnstr.IfThen('swede', 'dogs'),
                                [f'nationality{i}', f'pet{i}'])
        eproblem.add_constraint(cnstr.IfThen('dane', 'tea'),
                                [f'nationality{i}', f'drink{i}'])

        # Clue 4
        if i < 5:
            eproblem.add_constraint(cnstr.IfThen('green', 'white'),
                                    [f'color{i}', f'color{i + 1}'])
        else:
            eproblem.add_constraint(cnstr.NotInValues(['green']),
                                    ['color5'])

        # Clues 5 - 7
        eproblem.add_constraint(cnstr.IfThen('green', 'coffee'),
                                [f'color{i}', f'drink{i}'])
        eproblem.add_constraint(cnstr.IfThen('pallmall', 'birds'),
                                [f'smoke{i}', f'pet{i}'])
        eproblem.add_constraint(cnstr.IfThen('yellow', 'dunhill'),
                                [f'color{i}', f'smoke{i}'])

        # Clue 10
        if 1 < i < 5:
            eproblem.add_constraint(
                lambda smoke, peta, petb: smoke != 'blends' or
                peta == 'cats' or petb == 'cats',
                [f'smoke{i}', f'pet{i - 1}', f'pet{i + 1}'])
        else:
            eproblem.add_constraint(cnstr.IfThen('blends', 'cats'),
                                    [f'smoke{i}', f'pet{2 if i == 1 else 4}'])

        # Clue 11
        if 1 < i < 5:
            eproblem.add_constraint(
                lambda pet, smokea, smokeb: pet != 'horses' or
                smokea == 'dunhill' or smokeb == 'dunhill',
                [f'pet{i}', f'smoke{i - 1}', f'smoke{i + 1}'])
        else:
            eproblem.add_constraint(cnstr.IfThen('horses', 'dunhill'),
                                    [f'pet{i}', f'smoke{2 if i == 1 else 4}'])

        # Clues 12 & 13
        eproblem.add_constraint(cnstr.IfThen('bmaster', 'beer'),
                                [f'smoke{i}', f'drink{i}'])
        eproblem.add_constraint(cnstr.IfThen('german', 'prince'),
                                [f'nationality{i}', f'smoke{i}'])

        # Clue 14
        if 1 < i < 5:
            eproblem.add_constraint(
                lambda nationality, colora, colorb:
                    nationality != 'norwegian' or
                    colora == 'blue' or colorb == 'blue',
                [f'nationality{i}', f'color{i - 1}', f'color{i + 1}'])
        else:
            eproblem.add_constraint(cnstr.IfThen('norwegian', 'blue'),
                                    [f'nationality{i}',
                                     f'color{2 if i == 1 else 4}'])

        # Clue 15
        if 1 < i < 5:
            eproblem.add_constraint(
                lambda smoke, drinka, drinkb: smoke != 'blends' or
                drinka == 'water' or drinkb == 'water',
                [f'smoke{i}', f'drink{i - 1}', f'drink{i + 1}'])
        else:
            eproblem.add_constraint(cnstr.IfThen('blends', 'water'),
                                    [f'smoke{i}',
                                     f'drink{2 if i == 1 else 4}'])



def show_solution(solution, _=None):
    """Print the solution in a table and question answer."""
    print()
    print('   Nation    Color     Drink     Smoke     Pet')
    print('--------------------------------------------------')
    for i in range(1, 6):
        print(f'{i}: ', end='')
        for val in (solution[f'nationality{i}'], solution[f'color{i}'],
                    solution[f'drink{i}'], solution[f'smoke{i}'],
                    solution[f'pet{i}']):
            print(f'{val:10}', end='')
        print()
    print('\n')

    fish_nbr = {value : key for key, value in solution.items()}['fish'][-1]
    nat = f'nationality{fish_nbr}'
    print(f'The {solution[nat]} owns the fish.\n')


# %%  main


if __name__ == '__main__':

    experimenter.do_stuff(build, show_solution)


if __name__ == '__test_example__':

    print('\n')
    prob = csp.Problem()
    build(prob)
    sol = prob.get_solution()
    show_solution(sol)
