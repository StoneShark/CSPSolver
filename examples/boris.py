# -*- coding: utf-8 -*-
"""Example from
     https://www.boristhebrave.com/2021/08/30/arc-consistency-explained/

Created on Wed Jun 21 16:36:09 2023
@author: Ann"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '..')))
import csp_solver as csp
from csp_solver import constraint as cnstr
from csp_solver import experimenter


def build(prob):
    """Example problem from Boris the Brave."""

    prob.add_variables('ADE', [1, 2, 3, 4])
    prob.add_variable('B', [1, 2, 4])
    prob.add_variable('C', [1, 3, 4])

    prob.add_constraint(cnstr.AllDifferent(), 'AB')
    prob.add_constraint(cnstr.AllEqual(), 'AD')
    prob.add_constraint(cnstr.LessThan(), 'EA')

    prob.add_constraint(cnstr.AllDifferent(), 'BD')
    prob.add_constraint(cnstr.AllDifferent(), 'BC')
    prob.add_constraint(cnstr.LessThan(), 'EB')

    prob.add_constraint(cnstr.LessThan(), 'CD')
    prob.add_constraint(cnstr.LessThan(), 'EC')

    prob.add_constraint(cnstr.LessThan(), 'ED')


def show(solution, _=None):
    """Show the solution"""

    print(f"A = {solution['A']}")
    print(f"B = {solution['B']}")
    print(f"C = {solution['C']}")
    print(f"D = {solution['D']}")
    print(f"E = {solution['E']}")


if __name__ == '__main__':

    experimenter.do_stuff(build, show)


if __name__ == '__test_example__':

    print('\n')
    bprob = csp.Problem()
    build(bprob)
    sol = bprob.get_solution()
    show(sol)
