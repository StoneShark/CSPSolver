# -*- coding: utf-8 -*-
"""Send More Money CSP

Choose digits for each letter such that:

    s e n d
+   m o r e
 ----------
  m o n e y

Each assignment should be unique and without leading zeros.

Two problem representations are provided.

Created on Thu Jun 15 08:15:56 2023
@author: Ann"""

import functools as ft
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '..')))

from csp_solver import constraint as cnstr
from csp_solver import experimenter


ZERO = ord('0')

POWERS = [1, 10, 100, 1_000, 10_000]


def test_add(vorder, arg_dict):
    """Get the individual digits of three numbers each of length 'places'.
    Test concat(1st third of digits) + concat(2nd third of digits)
    equals concat(3rd third of digits)

    e.g  a, b, c, d, e, f = args  =>
    (a * 10 + b + c * 10 + d) mod 10 == e * 10 + f
    for places == 2"""

    if len(arg_dict) < 8:
        return True

    places = len(vorder) // 3
    val = [0] * 3
    for n in range(3):

        digits = [arg_dict[c] for c in reversed(vorder[n*places:(n+1)*places])]

        val[n] = sum(pwr * dig
                     for pwr, dig in zip(POWERS, digits))

    return (val[0] + val[1]) % POWERS[places] == val[2]


def test_4d_sum(arg_dict):
    """Test in concat(abcd) + concat(efgh) == sum(ijklm)"""

    if len(arg_dict) < 8:
        return True

    digits = [arg_dict[c] for c in 'sendmoremoney']

    val = [0] * 3
    val[0] = sum(pwr * dig
                 for pwr, dig in zip(POWERS, reversed(digits[0:4])))
    val[1] = sum(pwr * dig
                 for pwr, dig in zip(POWERS, reversed(digits[4:8])))
    val[2] = sum(pwr * dig
                 for pwr, dig in zip(POWERS, reversed(digits[8:])))

    return val[0] + val[1] == val[2]


def build_one(money_prob):
    """send + more = money. A very hardway."""

    money_prob.add_variables('sendmory', range(10))

    money_prob.add_constraint(cnstr.AllDifferent(), 'sendmory')
    money_prob.add_constraint(cnstr.NotInValues([0]), 'sm')

    money_prob.add_constraint(lambda a, b, c: (a + b) % 10 == c, 'dey')

    money_prob.add_constraint(
        cnstr.BoolFunction(ft.partial(test_add, 'ndreey'), var_args=True),
        'ndrey')
    money_prob.add_constraint(
        cnstr.BoolFunction(ft.partial(test_add, 'endoreney'), var_args=True),
        'endory')

    money_prob.add_constraint(cnstr.BoolFunction(test_4d_sum, var_args=True),
                              'sendmory')


def build_two(money_prob):
    """send + more == money.  problem statement with carries."""

    def add_no_carry(op1, op2, dsum, cryout):
        return op1 + op2 == dsum + cryout * 10

    def add_w_carry(op1, op2, cryin, dsum, cryout):
        return op1 + op2 + cryin == dsum + cryout * 10

    def add_dupl(op1, op2, cryin, dsum):
        return op1 + op2 + cryin == dsum + op2 * 10

    money_prob.add_variables('endory', range(0, 10))
    money_prob.add_variables('sm', range(1, 10))
    money_prob.add_variables(['c1', 'c2', 'c3'], [0, 1])

    money_prob.add_constraint(cnstr.AllDifferent(), 'sendmory')

    money_prob.add_constraint(add_no_carry, ['d', 'e',       'y', 'c1'])
    money_prob.add_constraint(add_w_carry,  ['n', 'r', 'c1', 'e', 'c2'])
    money_prob.add_constraint(add_w_carry,  ['e', 'o', 'c2', 'n', 'c3'])
    money_prob.add_constraint(add_dupl,     ['s', 'm', 'c3', 'o'])


def show(sol):
    """pretty print the solution."""

    print('  ' + ''.join([chr(ZERO + sol[v]) for v in 'send']))
    print('+ ' + ''.join([chr(ZERO + sol[v]) for v in 'more']))
    print('------')
    print(' ' + ''.join([chr(ZERO + sol[v]) for v in 'money']))

    if 'c1' in sol:
        print(f"\nc1={sol['c1']}  c2={sol['c2']}  c3={sol['c3']}")


if __name__ == '__main__':

    experimenter.do_stuff([build_one, build_two], show)
