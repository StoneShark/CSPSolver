# -*- coding: utf-8 -*-
"""Test the solver classes.
There's lots of duplication with test_problem.py.

Created on Sat Dec 14 07:41:15 2024
@author: Ann"""

# %% imports

import re

import pytest

import csp_solver as csp
from csp_solver import arc_consist
from csp_solver import constraint as cnstr
from csp_solver import solver
from csp_solver import var_chooser
import stubs


# %% test the solver

class TestSolver:
    """Test the Solver base class without a problem spec."""

    @pytest.fixture
    def slvr(self):
        return solver.Backtracking()


    def test_construct(self, slvr):
        """check default properties and names"""

        assert not slvr._forward
        assert not slvr._extra
        assert not slvr._arc_con
        assert slvr._chooser == var_chooser.DegreeDomain
        assert slvr._solve_type == solver.SolveType.ONE

        assert not slvr.forward
        assert not slvr.extra
        assert not slvr.arc_con
        assert slvr.chooser == var_chooser.DegreeDomain


    def test_setters_one(self, slvr):
        """exercise the error checking and setting of properties
        into the solver."""

        slvr.chooser = var_chooser.UseFirst
        assert slvr._chooser == var_chooser.UseFirst
        assert slvr.chooser == var_chooser.UseFirst

        with pytest.raises(ValueError):
            slvr.chooser = 5

        slvr.forward = True
        assert slvr._forward
        assert slvr.forward


    def test_setters_two(self, slvr):
        """continue testing setters, but start with new slvr"""

        slvr.enable_forward_check()
        assert slvr._forward
        assert slvr.forward

        with pytest.raises(ValueError):
            slvr.extra = 5

        slvr.extra = stubs.ExtraData()
        assert isinstance(slvr._extra, stubs.ExtraData)
        assert isinstance(slvr.extra, stubs.ExtraData)

        with pytest.raises(ValueError):
            slvr.arc_con = 5

        slvr.arc_con = arc_consist.ArcCon3()
        assert isinstance(slvr._arc_con, arc_consist.ArcCon3)
        assert isinstance(slvr.arc_con, arc_consist.ArcCon3)


    def test_extra_ifs(self, slvr, mocker):
        """call the extra data interfaces both with and
        without the extra data being set."""

        assert not slvr.extra
        assert slvr._assign_extra(None, None)   # return True wo extra
        assert not slvr._pop_extra()            # no return, does nothing

        extra = stubs.ExtraData()
        masgn = mocker.patch.object(extra, 'assign')
        mpop = mocker.patch.object(extra, 'pop')

        slvr.extra = extra

        slvr._assign_extra(None, None)
        masgn.assert_called_once()

        slvr._pop_extra()
        mpop.assert_called_once()


    SA_CASES = [
        ('abc', {'a': 4, 'b': 3, 'c': 2}, {'a': 4, 'b': 3, 'c': 2}),

        # order in assigns dict is wrong and partial assigns
        ('abc', {'b': 4, 'a': 3}, {'a': 3, 'b': 4}),

        # extra data in the assigns dict
        ('abc', {'a': 4, 'b': 3, 'c': 2, 'd': 1}, {'a': 4, 'b': 3, 'c': 2}),
        ]

    @pytest.mark.parametrize('vnames, assigns, eassigns',
                             SA_CASES)
    def test_select_assigns(self, slvr, vnames, assigns, eassigns):

        cassigns = slvr._select_assignments(vnames, assigns)
        assert cassigns == eassigns

        # build a regex of the form '.*[a].*[d].*' to confirm variable order
        vregex = '.*[' + '].*['.join(list(cassigns)) + '].*'
        assert re.fullmatch(vregex, vnames)


    STOP_CASES = [  #trivial solution dicts, only number of sols matters
        [],
        [{'a': 4}],
        [{'a': 4}, {'b': 3}],
        [{'a': 4}, {'b': 3}, {'c': 5}],
        ]

    @pytest.mark.parametrize('sols', STOP_CASES)
    @pytest.mark.parametrize('stype', solver.SolveType)
    def test_stop_solver(self, slvr, sols, stype):

        slvr._solve_type = stype
        stop = slvr._stop_solver(sols)

        if stype == solver.SolveType.ALL:
            assert not stop

        elif stype == solver.SolveType.ONE:
            if len(sols) >= 1:
                assert stop
            else:
                assert not stop

        elif stype == solver.SolveType.MORE_THAN_ONE:
            if len(sols) > 1:
                assert stop
            else:
                assert not stop

        else:
            assert False, f"unknown solve type {stype}"


class TestSolverPSpec:
    """Test the Solver methods that require a problem spec."""

    @pytest.fixture
    def pspec(self):
        """
        for a in [0, 1]:
            for b in [0, 1]:
                for c in [0, 1]:
                    c1 = not a or b
                    c2 = b != c
                    r = c1 and c2
                    print(f'{a:2} {b:2} {c:2}   {c1:2} {c2:2}   {r:2}')
        """

        p_spec = csp.ProblemSpec()
        p_spec.add_variables('abcd', '01')
        p_spec.add_constraint(cnstr.IfThen('1', '1'), 'ab')
        p_spec.add_constraint(cnstr.Xor('1', '1'), 'bc')
        p_spec.prepare_variables()

        return p_spec


    @pytest.fixture
    def slvr(self, pspec):

        return solver.Backtracking(forward_check=True,
                                   problem_spec=pspec)


    CCASES =[
        # both IfThen and Xor return True without full assignments

        # only IfThen tested
        ('a', {'a': '0'}, True),
        ('a', {'a': '0', 'b': '1'}, True),
        ('a', {'a': '0', 'b': '0'}, True),
        ('a', {'a': '1', 'b': '1'}, True),
        ('a', {'a': '1', 'b': '0'}, False),
        ('a', {'b': '1'}, True),

        # both IfThen and Xor tested
        ('b', {'a': '0'}, True),
        ('b', {'a': '0', 'b': '1'}, True),
        ('b', {'a': '1', 'b': '0'}, False),
        ('b', {'a': '0', 'b': '0', 'c': '1'}, True),
        ('b', {'a': '0', 'b': '0', 'c': '0'}, False),

        ('b', {'b': '1', 'c': '0'}, True),
        ('b', {'b': '0', 'c': '1'}, True),

        ('d', {'d': 0}, True),   # d has no constraints
        ]

    @pytest.mark.parametrize('vname, assigns, eret', CCASES)
    def test_consistent(self, slvr, vname, assigns, eret):

        assert slvr._consistent(vname, assigns) == eret


    ACASES = [
        # both IfThen and Xor return True without full assignments

        ({'a': '0'}, True),
        ({'a': '1'}, True),
        ({'b': '0'}, True),
        ({'b': '1'}, True),
        ({'c': '0'}, True),
        ({'c': '1'}, True),

        ({'a': '0', 'b': '0'}, True),
        ({'a': '1', 'b': '1'}, True),
        ({'a': '1', 'b': '0'}, False),
        ({'a': '0', 'c': '0'}, True),
        ({'a': '1', 'c': '1'}, True),
        ({'a': '1', 'c': '0'}, True),
        ({'b': '0', 'c': '0'}, False),
        ({'b': '1', 'c': '1'}, False),
        ({'a': '1', 'c': '0'}, True),

        ({'a': '0', 'b': '0', 'c': '1'}, True),
        ({'a': '0', 'b': '0', 'c': '0'}, False),
        ({'a': '1', 'b': '0', 'c': '0'}, False),
        ({'a': '1', 'b': '0', 'c': '1'}, False),

        ({'d': 0}, True),   # d has no constraints
        ]

    @pytest.mark.parametrize('assigns, eret', ACASES)
    def test_all_consist(self, slvr, assigns, eret):

        assert slvr._all_consistent(assigns) == eret


    def test_fwd_false(self, pspec):
        """call forward with it disabled"""

        my_slvr = solver.Backtracking(forward_check=False,
                                      problem_spec=pspec)
        assert my_slvr._forward_check(None, None)


    FCASES = [
        ('a', {'a': '1'}, ['01', '1', '01'], True),
        # Domain of b is reduced to 1, which could reduce the
        # domain of c, but forward_check does not do 'propagation
        # through singletons or reduced domains'.
        # If it did, overall consistency checking would be needed
        # in _forward_check (case 2 fails if easy temp assigns made).

        ('b', {'b': '0'}, ['01', '01', '1'], True),
        # both constraints forward checked on inner loop
        # outer loop runs once

        ('c', {'a': '1', 'c': '1'}, ['01', '', '01'], False),
        # After domain of b is reduced,
        # the outer loop in _forward_check, checks all b's
        # constraints finding that variable a's assignment
        # further reduces b's domain overconstraining it

        ]

    @pytest.mark.parametrize('vname, assigns, edoms, eret', FCASES)
    def test_forward(self, slvr, vname, assigns, edoms, eret):

        # print(vname)
        # print(slvr._spec.cnstr_dict[vname])

        rval = slvr._forward_check(vname, assigns)

        # print(rval)
        # print('a', slvr._spec.variables['a'].get_domain())
        # print('b', slvr._spec.variables['b'].get_domain())
        # print('c', slvr._spec.variables['c'].get_domain())

        assert rval == eret
        assert set(slvr._spec.variables['a'].get_domain()) == set(edoms[0])
        assert set(slvr._spec.variables['b'].get_domain()) == set(edoms[1])
        assert set(slvr._spec.variables['c'].get_domain()) == set(edoms[2])
