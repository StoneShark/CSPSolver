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
from csp_solver import list_constraint as lcnstr
from csp_solver import solver
from csp_solver import var_chooser
import stubs


# %% test the solver

class TestSolver:
    """Test the Solver class without a problem spec."""

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


    STOP_CASES = [  #trivial solution dicts, only number matters
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


# class TestSolverPSpec:
#     """Test the Solver class with a problem spec."""

#     @pytest.fixture
#     def pspec(self):
#         pass
