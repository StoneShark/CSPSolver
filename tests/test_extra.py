# -*- coding: utf-8 -*-
"""ExtraData is just an interface class, so it's already
'covered'.

The real tests are to confirm that the backtracking solvers
    1. make the right calls to extra data in the right places
    2. respond properly when the extra data assign finds
       a conflict

Created on Sat Dec 21 16:23:22 2024
@author: Ann"""


# %% imports

import collections

import pytest
pytestmark = pytest.mark.unittest

import csp_solver as csp
from csp_solver import constraint as cnstr
from csp_solver import extra_data
from csp_solver import list_constraint as lcnstr
from csp_solver import solver
from csp_solver import var_chooser


# %%   test extra data

class ExtraTrue(extra_data.ExtraDataIF):
    """Make dictionary and deque of the data, always return True"""

    def __init__(self):
        self.avars = dict()
        self.data = collections.deque()

    def assign(self, var, val):

        if var in self.avars:
            self.avars[var] = val
        else:
            self.data.append(var)
            self.avars[var] = val

        return True

    def pop(self):

        var = self.data.pop()
        del self.avars[var]


class ExtraNoRed(extra_data.ExtraDataIF):
    """Make dictionary and deque of the data, return
    False if any position is assigned to red.

    Clearly this could be done more efficiently by
    removing red from the domains--but that's not
    what we are testing.

    We are testing if the solvers respond properly
    by eliminating the solutions they should based
    on the return value."""

    def __init__(self):
        self.avars = dict()
        self.data = collections.deque()

    def assign(self, var, val):

        if val == 'r':
            return False

        if var in self.avars:
            self.avars[var] = val
        else:
            self.data.append(var)
            self.avars[var] = val

        return True

    def pop(self):

        var = self.data.pop()
        del self.avars[var]


def wrap_consistent(mocker, slvr):
    """Wrap the _consistent method in the solver with a
    method to confirm that all values in assigns are in
    the extra data."""

    orig_method = slvr._consistent

    def consist_checker(vname, assigns):
        """Does extra data match the assigns"""

        assert slvr._extra.avars == assigns
        return orig_method(vname, assigns)

    mocker.patch.object(slvr, '_consistent', consist_checker)


class TestExtraData:

    @pytest.fixture
    def mmind(self):
        """This is the first three guesses from the master_mind_4
        example."""

        puz = csp.Problem()
        puz.add_variables('1234', 'rygcbp')

        # rryy  1 white
        puz.add_constraint(cnstr.NotInValues('r'), '12')
        puz.add_constraint(cnstr.NotInValues('y'), '34')
        puz.add_constraint(cnstr.ExactlyNIn('ry', 1), '1234')

        # ggcc  1 black 1 white
        # assignments could include gg, cc, gc, or gc, OR ggg or ccc
        puz.add_constraint(cnstr.AtLeastNIn('bg', 2), '1234')

        # one of guess in right place
        puz.add_list_constraint(lcnstr.OneOfCList(),
                                [(cnstr.InValues('g'), '1'),
                                 (cnstr.InValues('g'), '2'),
                                 (cnstr.InValues('c'), '3'),
                                 (cnstr.InValues('c'), '4')])

        # one of guess is in wrong place, so must be on opp side
        puz.add_list_constraint(lcnstr.OneOfCList(),
                                [(cnstr.InValues('c'), '1'),
                                 (cnstr.InValues('c'), '2'),
                                 (cnstr.InValues('g'), '3'),
                                 (cnstr.InValues('g'), '4')])

        # bbpp  1 white
        puz.add_constraint(cnstr.NotInValues('b'), '12')
        puz.add_constraint(cnstr.NotInValues('p'), '34')
        puz.add_constraint(cnstr.ExactlyNIn('bp', 1), '1234')

        return puz


    @pytest.fixture
    def half_addr(self):
        """solutions are the truth table"""

        haddr = csp.Problem()
        haddr.add_variables('abcs', (0, 1))
        haddr.add_constraint(lambda a, b, s: (1 if a != b else 0) == s, 'abs')
        haddr.add_constraint(lambda a, b, c: (1 if a and b else 0) == c, 'abc')
        return haddr


    @pytest.mark.parametrize('csp_fixt, e_nbr_sols',
                             [('half_addr', 4),
                              ('mmind', 12)])
    @pytest.mark.parametrize('slvr', [solver.Backtracking(),
                                      solver.NonRecBacktracking()],
                             ids=['recursive', 'nonrecurs'])
    @pytest.mark.parametrize('vchsr', [var_chooser.UseFirst,
                                       var_chooser.MinDomain],
                             ids=['UseFirst', 'MinDomain'])
    def test_assigns_and_pops(self, request, mocker,
                              slvr, vchsr, csp_fixt, e_nbr_sols):
        """Test a simple two-value problem (half_addr) and a slightly
        more complex problem with larger domains (mmind).

        Both backtracking solvers should yeild the same results
        and general use of the extra data.

        Test two var_choosers that should select variables in
        different orders (at least for mmind).

        The key part of the test is in wrap_consistent::consist_checker
        were it is confirmed that extra_data.assign has been
        called for all assigned variables being sent to
        solver._consistent and that there are no extra assignments
        (e.g. the right pops were called).
        """

        csp_prob = request.getfixturevalue(csp_fixt)

        csp_prob.solver = slvr
        csp_prob.extra_data = ExtraTrue()
        csp_prob.var_chooser = vchsr

        assert csp_prob._solver
        assert csp_prob._solver.extra

        wrap_consistent(mocker, csp_prob._solver)

        allsols = csp_prob.get_all_solutions()
        assert len(allsols) == e_nbr_sols

        # print(allsols)


    @pytest.mark.parametrize('slvr', [solver.Backtracking(),
                                      solver.NonRecBacktracking()],
                             ids=['recursive', 'nonrecurs'])
    def test_extra_fails(self, mocker, mmind, slvr):
        """Extra data will eliminate all solutions with
        red pegs in the answer (it's a fabricated example
        to test the handling of extra.assign return values).

        The solution set is reduced from the 12 found in
        test_assigns_and_pops to 4."""

        mmind.solver = slvr
        mmind.extra_data = ExtraNoRed()

        assert mmind._solver
        assert mmind._solver.extra

        wrap_consistent(mocker, mmind._solver)

        allsols = mmind.get_all_solutions()
        assert len(allsols) == 4

        # print(allsols)
