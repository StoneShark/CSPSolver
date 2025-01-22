# -*- coding: utf-8 -*-
"""Test the csp_solver.Problem and ProblemSpec classes.

Created on Thu May 11 08:31:07 2023
@author: Ann"""

# %% imports

import pytest
pytestmark = pytest.mark.unittest

import csp_solver as csp
from csp_solver import arc_consist
from csp_solver import constraint as cnstr
from csp_solver import extra_data
from csp_solver import list_constraint as lcnstr
from csp_solver import solver
from csp_solver import var_chooser
import stubs


# %%   test Problem


class TestProblem:

    @pytest.fixture
    def test_prob(self):
        return csp.Problem()


    def test_defaults(self, test_prob):
        """This sets the stage for other tests that confirm a value
        is changed. If chaning a default, recheck the tests below
        to confirm they still actually do a test."""

        assert 'Backtracking' in str(test_prob.solver)
        assert 'DegreeDomain' in str(test_prob.var_chooser)
        assert not test_prob.forward_check
        assert not test_prob.extra_data
        assert not test_prob.arc_con

        assert test_prob.pspec == test_prob._spec
        assert not test_prob._spec.usol_cnstr
        assert test_prob._spec.variables == {}
        assert test_prob._spec.constraints == []

        assert test_prob.solver_name() == 'Backtracking'
        assert test_prob.var_chooser_name() == 'DegreeDomain'
        assert test_prob.arc_con_name() == None


    def test_vars(self, test_prob):

        test_prob.add_variable('a', [1,2,3,4])
        assert test_prob._spec.variables['a'].get_domain() == [1,2,3,4]

        # add a dupl variable
        with pytest.raises(ValueError):
            test_prob.add_variable('a', [1,2,3,4])

        # add a bunch of vars all with same domain
        dom = [False, True]
        test_prob.add_variables('bcd', dom)
        dom[0] = 5
        assert test_prob._spec.variables['b'].get_domain() == [False, True]
        assert test_prob._spec.variables['c'].get_domain() == [False, True]
        assert test_prob._spec.variables['d'].get_domain() == [False, True]


    def test_uniq_cnstr(self, test_prob):

        test_prob.add_variable('a', [1,2,3,4])
        test_prob.add_variables('bcd', [False, True])

        # must usol must have correct IF class
        with pytest.raises(ValueError):
            test_prob.set_unique_sol_constraint(object(), 'abcd')

        con = cnstr.UniqueSets(['ab', 'cd'])
        test_prob.set_unique_sol_constraint(con, 'abcd')
        assert test_prob._spec.usol_cnstr == con

        # don't allow setting second unique sol cnstr
        with pytest.raises(ValueError):
            test_prob.set_unique_sol_constraint(con, 'abcd')


    def test_cnstrs(self, test_prob):

        test_prob.add_variable('a', [1,2,3,4])
        test_prob.add_variables('bcd', [False, True])

        # add a bad constraint
        with pytest.raises(ValueError):
            test_prob.add_constraint(5, 'ab')

        # test converting lambda to a BoolFunction constraint
        test_prob.add_constraint(lambda a : a == 5, 'd')
        assert isinstance(test_prob._spec.constraints[0],
                          cnstr.BoolFunction)

        # test reusing a constraint -- bad
        con = cnstr.AllDifferent()
        test_prob.add_constraint(con, 'ab')
        with pytest.raises(ValueError):
            test_prob.add_constraint(con, 'de')


    def test_lcnstrs(self, test_prob):

        test_prob.add_variable('a', [1,2,3,4])
        test_prob.add_variables('bcd', [False, True])

        # add a valid list constraint
        test_prob.add_list_constraint(lcnstr.AtLeastNCList(2),
                                       [(lambda a, b : a*2 == b, 'ab'),
                                        (cnstr.MaxSum(4), 'abc'),
                                        (cnstr.AllDifferent(), 'ad')] )
        assert isinstance(test_prob._spec.constraints[0],
                          lcnstr.ListConstraint)

        # test adding a list constraint with only 1 constraint -- bad
        with pytest.raises(ValueError):
            test_prob.add_list_constraint(lcnstr.AtLeastNCList(2),
                                           [(lambda a, b : a*2 == b, 'ab')] )

        # test adding a list constraint where constraint isn't a list con
        with pytest.raises(ValueError):
            test_prob.add_list_constraint(cnstr.MaxSum(4),
                                           [(lambda a, b : a*2 == b, 'ab'),
                                            (cnstr.AllDifferent(), 'ad')] )

        # test adding a list constraint where constraint isn't a list con
        with pytest.raises(ValueError):
            test_prob.add_list_constraint('not a list constraint',
                                           [(lambda a, b : a*2 == b, 'ab'),
                                           (cnstr.AllDifferent(), 'ad')] )


    def test_nat_nums(self, test_prob):

        test_prob.add_variable('a', [1, 2, 3, 4])
        test_prob.add_variable('b', [6, 7, -8, 9])

        test_prob.add_constraint(cnstr.MaxSum(12), ['a', 'b'])

        with pytest.raises(ValueError):
            test_prob._spec.natural_numbers_required()


    def test_set_vchooser(self, test_prob):

        with pytest.raises(ValueError):
            test_prob.var_chooser = object()

        test_prob.var_chooser = var_chooser.UseFirst
        assert test_prob.var_chooser == var_chooser.UseFirst
        assert test_prob._solver.chooser == var_chooser.UseFirst


    def test_set_forward(self, test_prob):

        test_prob.forward_check = True
        assert test_prob.forward_check
        assert test_prob._solver.forward


    def test_set_extra(self, test_prob):

        with pytest.raises(ValueError):
            test_prob.extra_data = 5

        test_prob.extra_data = stubs.ExtraData()
        assert isinstance(test_prob._solver.extra, stubs.ExtraData)


    def test_set_arc_con(self, test_prob):

        test_prob.arc_con = None
        assert test_prob._solver.arc_con == None

        with pytest.raises(ValueError):
            test_prob.arc_con = 5

        test_prob.arc_con = arc_consist.ArcCon3()
        assert isinstance(test_prob._solver.arc_con, arc_consist.ArcCon3)


    def test_set_solver(self, test_prob):
        """Test that when the solver is changed all previously
        set options are copied."""

        with pytest.raises(ValueError):
            test_prob.solver = 5

        # init data in default solver
        test_prob.forward_check = True
        test_prob.var_chooser = var_chooser.UseFirst
        test_prob.extra_data = stubs.ExtraData()
        test_prob.arc_con = arc_consist.ArcCon3()

        # constructed with defaults
        new_solver = solver.NonRecBacktracking()
        assert 'DegreeDomain' in str(new_solver.chooser)
        assert not new_solver.forward
        assert not new_solver.extra
        assert not new_solver.arc_con

        test_prob.solver = new_solver

        # test that all updates were copied into new solver
        assert test_prob._solver.chooser == var_chooser.UseFirst
        assert test_prob._solver.forward
        assert isinstance(test_prob._solver.extra, stubs.ExtraData)
        assert isinstance(test_prob._solver.arc_con, arc_consist.ArcCon3)


    @pytest.fixture
    def math_fixt(self, test_prob):

        test_prob.add_variable('a', [1, 2, 3, 4])
        test_prob.add_variable('b', [1, 2, 5, 6])
        test_prob.add_variable('c', [2, 23, 216])

        test_prob.add_constraint(cnstr.AllDifferent(), ['a', 'c'])
        test_prob.add_constraint(lambda a, b : a*2 == b, ['a', 'b'])
        test_prob.add_constraint(lambda a, b, c: b**a == c, ['a', 'b', 'c'])

        return test_prob


    @pytest.mark.parametrize('slvr', [solver.Backtracking(),
                                      solver.NonRecBacktracking(),
                                      solver.BareNRBack()])
    def test_math_all(self, math_fixt, slvr):

        math_fixt.solver = slvr
        solutions = math_fixt.get_all_solutions()

        for sol in solutions:
            assert (sol['a'] != sol['c'] and sol['a'] * 2 == sol['b']
                    and sol['b'] ** sol['a'] == sol['c'])


    def test_math_except(self, math_fixt):

        math_fixt.solver = solver.MinConflictsSolver()
        with pytest.raises(ValueError):
            math_fixt.get_all_solutions()


    @pytest.mark.parametrize('slvr', [solver.Backtracking,
                                      solver.NonRecBacktracking,
                                      solver.BareNRBack])
    @pytest.mark.parametrize('vchsr', var_chooser.VarChooser.derived())
    def test_math_prob_one(self, math_fixt, slvr, vchsr):


        tsolver = slvr()
        math_fixt.solver = tsolver
        assert math_fixt._solver == tsolver

        math_fixt.var_chooser = vchsr
        assert math_fixt._solver._chooser == vchsr

        sol = math_fixt.get_solution()

        assert (sol['a'] != sol['c'] and sol['a'] * 2 == sol['b']
                and sol['b'] ** sol['a'] == sol['c'])


    @pytest.fixture
    def math_no_fixt(self, test_prob):
        """3 vars prevents the preprocessor from doing anything."""

        test_prob.add_variable('a', [2,4])
        test_prob.add_variable('b', [1,2,5,6])
        test_prob.add_variable('c', [1,2,5,6])

        test_prob.add_constraint(cnstr.AllDifferent(), 'abc')
        test_prob.add_constraint(lambda a, b, c : a*2 == b, 'abc')

        return test_prob


    @pytest.mark.parametrize('slvr', solver.Solver.derived())
    def test_math_no_sols(self, math_no_fixt, slvr):

        math_no_fixt.solver = slvr()
        sol = math_no_fixt.get_solution()

        assert sol == None


    @pytest.fixture
    def math_two_fixt(self, test_prob):

        test_prob.add_variable('a', [1, 2, 3, 4])
        test_prob.add_variable('b', [6, 7, 8, 9])
        test_prob.add_variable('c', [10, 11])

        test_prob.add_constraint(cnstr.MaxSum(12), ['a', 'b'])
        test_prob.add_constraint(cnstr.MinSum(10), ['b', 'c'])
        test_prob.add_constraint(cnstr.ExactSum(12), ['a', 'c'])
        test_prob.add_constraint(cnstr.NotInValues([7]), ['b'])
        test_prob.add_constraint(cnstr.InValues([10]), ['c'])

        return test_prob


    @pytest.mark.parametrize('slvr', [solver.Backtracking(),
                                      solver.NonRecBacktracking()])
    def test_math_two_all_fwd(self, math_two_fixt, slvr):

        assert math_two_fixt._solver._forward == False
        math_two_fixt.enable_forward_check()
        assert math_two_fixt._solver._forward == True

        math_two_fixt.solver = slvr
        solutions = math_two_fixt.get_all_solutions()

        assert len(solutions) == 3
        assert all(sol['a'] == 2 for sol in solutions)
        assert all(sol['c'] == 10 for sol in solutions)

        assert {sol['b'] for sol in solutions} == {6, 8, 9}

        math_two_fixt.print_domains()
        math_two_fixt.print_constraints()


    @pytest.mark.parametrize('slvr', [solver.Backtracking(),
                                      solver.NonRecBacktracking()])
    def test_math_two_gr_one(self, math_two_fixt, slvr):
        """Solve the same problem again with more_than_one_solution,
        stops when the second solution is found."""

        math_two_fixt.enable_forward_check()
        math_two_fixt.solver = slvr

        # check setting solver didn't clear forward_check
        assert math_two_fixt.forward_check
        solutions = math_two_fixt.more_than_one_solution()

        assert len(solutions) == 2
