# -*- coding: utf-8 -*-
"""Created on Thu May 11 08:31:07 2023

@author: Ann
"""

# %% imports

import pytest

import csp_solver as csp
from csp_solver import constraint as cnstr
from csp_solver import list_constraint as lcnstr
from csp_solver import solver
from csp_solver import var_chooser


# %%   test Problem

class TestProblem:


    def test_builds(self):

        test_prob = csp.Problem()

        test_prob.add_variable('a', [1,2,3,4])
        assert test_prob._spec.variables['a'].get_domain() == [1,2,3,4]

        with pytest.raises(ValueError):
            test_prob.add_variable('a', [1,2,3,4])

        test_prob.add_variables('bcd', [False, True])
        assert test_prob._spec.variables['b'].get_domain() == [False, True]
        assert test_prob._spec.variables['c'].get_domain() == [False, True]
        assert test_prob._spec.variables['d'].get_domain() == [False, True]

        with pytest.raises(ValueError):
            test_prob.add_constraint(5, 'ab')

        test_prob.add_constraint(lambda a : a == 5, 'd')
        assert isinstance(test_prob._spec.constraints[0],
                          cnstr.BoolFunction)

        test_prob.add_list_constraint(lcnstr.AtLeastNCList(2, False),
                                    [(lambda a, b : a*2 == b, 'ab'),
                                     (cnstr.MaxSum(4), 'abc'),
                                     (cnstr.AllDifferent(), 'ad')] )
        assert isinstance(test_prob._spec.constraints[1],
                          lcnstr.ListConstraint)

        assert test_prob.solver_name() == 'Backtracking'
        assert test_prob.var_chooser_name() == 'DegreeDomain'

        with pytest.raises(ValueError):
            test_prob.add_list_constraint(cnstr.MaxSum(4),
                                        [(lambda a, b : a*2 == b, 'ab'),
                                         (cnstr.AllDifferent(), 'ad')] )

        with pytest.raises(ValueError):
            test_prob.add_list_constraint('not a list constraint',
                                        [(lambda a, b : a*2 == b, 'ab'),
                                         (cnstr.AllDifferent(), 'ad')] )


    def test_nat_nums(self):

        test_prob = csp.Problem()

        test_prob.add_variable('a', [1, 2, 3, 4])
        test_prob.add_variable('b', [6, 7, -8, 9])

        test_prob.add_constraint(cnstr.MaxSum(12), ['a', 'b'])

        with pytest.raises(ValueError):
            test_prob._spec.natural_numbers_required()


    @pytest.fixture
    def math_fixt(self):

        test_prob = csp.Problem()

        test_prob.add_variable('a', [1, 2, 3, 4])
        test_prob.add_variable('b', [1, 2, 5, 6])
        test_prob.add_variable('c', [2, 23, 216])

        test_prob.add_constraint(cnstr.AllDifferent(), ['a', 'c'])
        test_prob.add_constraint(lambda a, b : a*2 == b, ['a', 'b'])
        test_prob.add_constraint(lambda a, b, c: b**a == c, ['a', 'b', 'c'])

        return test_prob


    @pytest.mark.parametrize('slvr', [solver.Backtracking(),
                                      solver.NonRecBacktracking()])
    def test_math_all(self, math_fixt, slvr):

        math_fixt.solver = slvr
        solutions = math_fixt.get_all_solutions()

        for sol in solutions:
            assert (sol['a'] != sol['c'] and sol['a'] * 2 == sol['b']
                    and sol['b'] ** sol['a'] == sol['c'])


    def test_math_except(self, math_fixt):

        math_fixt.solver = solver.MinConflictsSolver()
        with pytest.raises(NotImplementedError):
            math_fixt.get_all_solutions()


    @pytest.mark.parametrize('slvr', solver.Solver.__subclasses__())
    @pytest.mark.parametrize('vchsr', var_chooser.VarChooser.__subclasses__())
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
    def math_no_fixt(self):
        """3 vars prevents the preprocessor from doing anything."""

        test_prob = csp.Problem()

        test_prob.add_variable('a', [2,4])
        test_prob.add_variable('b', [1,2,5,6])
        test_prob.add_variable('c', [1,2,5,6])

        test_prob.add_constraint(cnstr.AllDifferent(), 'abc')
        test_prob.add_constraint(lambda a, b, c : a*2 == b, 'abc')

        return test_prob


    @pytest.mark.parametrize('slvr', [solver.Backtracking(),
                                      solver.NonRecBacktracking(),
                                      solver.MinConflictsSolver()]
                            )
    def test_math_no_sols(self, math_no_fixt, slvr):

        math_no_fixt.solver = slvr
        sol = math_no_fixt.get_solution()

        assert sol == None


    @pytest.fixture
    def math_two_fixt(self):

        test_prob = csp.Problem()

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

        assert all(sol['a'] == 2 for sol in solutions)
        assert all(sol['c'] == 10 for sol in solutions)

        assert {sol['b'] for sol in solutions} == {6, 8, 9}

        math_two_fixt.print_domains()
