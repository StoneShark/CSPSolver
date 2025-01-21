# -*- coding: utf-8 -*-
"""
Created on Tue Jan 21 06:07:47 2025

@author: Ann
"""

# %% imports


import pytest
pytestmark = pytest.mark.unittest

from csp_solver import constraint as cnstr
import stubs


# %% tests

TENS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


class TestUniqueSets:

    def test_construct(self):

        # empty list param
        with pytest.raises(cnstr.ConstraintError):
            cnstr.UniqueSets(None)

        # param not a list of iterables
        with pytest.raises(cnstr.ConstraintError):
            cnstr.UniqueSets('ab')
        with pytest.raises(cnstr.ConstraintError):
            cnstr.UniqueSets([1, 2])

        # iterables of length 1 are rejected
        with pytest.raises(cnstr.ConstraintError):
            cnstr.UniqueSets(['abc', 'd'])
        with pytest.raises(cnstr.ConstraintError):
            cnstr.UniqueSets([['a', 'b', 'c'], ['d']])

        # accept this, iterpreted as vgroups below
        assert cnstr.UniqueSets(['abc', 'de'])

        vgroups = [['a', 'b', 'c'], ['d', 'e']]
        cons = cnstr.UniqueSets(vgroups)
        assert 'UniqueSets' in repr(cons)
        assert isinstance(cons, cnstr.UniqueSolutionsIF)
        assert isinstance(cons, cnstr.UniqueSets)
        assert cons._vname_sets == vgroups
        assert not cons._saved_solutions


    def test_vsets(self):

        cons = cnstr.UniqueSets(['abc', 'de'])
        vsets = cons._value_sets({'a': 3, 'b': 4, 'c': 3, 'd': 5, 'e': 6})

        assert len(vsets) == 2
        assert all(isinstance(vset, set) for vset in vsets)
        assert vsets[0] == {3, 4}
        assert vsets[1] == {5, 6}


    S1PARAMS = [
        # partial assignments are not rejected
        [{'a': 4}, True],

        # exact same solution
        [{'a': 2, 'b': 4, 'c': 3, 'd': 5, 'e': 7}, False],

        [{'a': 4, 'b': 2, 'c': 3, 'd': 5, 'e': 7}, False],
        [{'a': 2, 'b': 4, 'c': 3, 'd': 7, 'e': 5}, False],
        [{'a': 4, 'b': 2, 'c': 3, 'd': 7, 'e': 5}, False],

        [{'a': 2, 'b': 4, 'c': 4, 'd': 3, 'e': 7}, True],
        [{'a': 2, 'b': 6, 'c': 5, 'd': 3, 'e': 7}, True],
        ]

    @pytest.mark.parametrize('assigns, unique', S1PARAMS)
    def test_one_sol_found(self, assigns, unique):

        cons = cnstr.UniqueSets(['abc', 'de'])
        cons.set_variables(stubs.make_vars([(vname, TENS)
                                            for vname in 'abcde']))

        cons.solution_found({'a': 2, 'b': 4, 'c': 3, 'd': 5, 'e': 7})
        assert len(cons._saved_solutions) == 1

        assert cons.satisfied(assigns) == unique


    S2PARAMS = [

        # exact same solutions
        [{'a': 2, 'b': 4, 'c': 3, 'd': 5, 'e': 7}, False],
        [{'a': 2, 'b': 4, 'c': 4, 'd': 3, 'e': 7}, False],

        # sol 1 duplicates
        [{'a': 4, 'b': 2, 'c': 3, 'd': 5, 'e': 7}, False],
        [{'a': 2, 'b': 4, 'c': 3, 'd': 7, 'e': 5}, False],
        [{'a': 4, 'b': 2, 'c': 3, 'd': 7, 'e': 5}, False],

        # sol 2 duplicates
        [{'a': 2, 'b': 4, 'c': 4, 'd': 3, 'e': 7}, False],
        [{'a': 4, 'b': 2, 'c': 4, 'd': 3, 'e': 7}, False],
        [{'a': 4, 'b': 2, 'c': 4, 'd': 7, 'e': 3}, False],

        #  these might NOT be duplicates of sol 2
        #   right set of values but not the right counts
        #   developer choice was to try to catch behavior and document it
        [{'a': 2, 'b': 2, 'c': 4, 'd': 3, 'e': 7}, False],
        [{'a': 2, 'b': 2, 'c': 4, 'd': 7, 'e': 3}, False],

        [{'a': 2, 'b': 6, 'c': 5, 'd': 3, 'e': 7}, True],
        ]

    @pytest.mark.parametrize('assigns, unique', S2PARAMS)
    def test_two_sol_found(self, assigns, unique):

        cons = cnstr.UniqueSets(['abc', 'de'])
        cons.set_variables(stubs.make_vars([(vname, TENS)
                                            for vname in 'abcde']))

        cons.solution_found({'a': 2, 'b': 4, 'c': 3, 'd': 5, 'e': 7})
        cons.solution_found({'a': 2, 'b': 4, 'c': 4, 'd': 3, 'e': 7})
        assert len(cons._saved_solutions) == 2

        assert cons.satisfied(assigns) == unique
