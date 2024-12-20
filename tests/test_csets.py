# -*- coding: utf-8 -*-
"""Test the set constraints.

Created on Mon Dec 16 08:04:19 2024
@author: Ann"""

# %% imports

import pytest
pytestmark = pytest.mark.unittest

from csp_solver import constraint as cnstr
import stubs


# %% tests

class TestExactlyNInCnstr:

    def test_construct(self):
        aln = cnstr.ExactlyNIn([2, 3, 8], 1)
        assert 'ExactlyNIn' in repr(aln)
        assert isinstance(aln, cnstr.ExactlyNIn)
        assert aln._elements == [2, 3, 8]
        assert aln._params == 0
        assert aln._req_nbr == 1

        aln = cnstr.ExactlyNIn([2, 3, 8, 9, 10], 2)
        assert aln._elements == [2, 3, 8, 9, 10]
        assert aln._params == 0
        assert aln._req_nbr == 2


    def test_preprocess(self):

        con = cnstr.ExactlyNIn([2, 3, 8, 9, 10], 1)
        con.set_variables(stubs.make_vars([('var1', [3, 6, 9, 10]),
                                           ('var2', [1, 4, 10, 11])]))
        assert not con.preprocess()

        con = cnstr.ExactlyNIn([2, 3, 8, 9, 10], 4)
        with pytest.raises(cnstr.ConstraintError):
            con.set_variables(stubs.make_vars([(3, [3, 4, 8]),
                                               (4, [3, 4, 5]),
                                               (5, [1, 2, 3]),
                                               (6, [1, 2])]))

        con = cnstr.ExactlyNIn([2, 3, 8, 9, 10], 5)
        with pytest.raises(cnstr.ConstraintError):
            con.set_variables(stubs.make_vars([(3, [3, 4, 8]),
                                               (4, [3, 4, 5]),
                                               (5, [1, 2, 3]),
                                               (6, [1, 2])]))


    SCASES = [([1, 2, 5, 6], 1, {'v1': 1, 'v2': 3, 'v3': 0}, True),
              ([1, 2, 5, 6], 1, {'v1': 0, 'v2': 5, 'v3': 0}, True),
              ([1, 2, 5, 6], 1, {'v1': 2, 'v2': 5, 'v3': 0}, False),
              ([1, 2, 5, 6], 1, {'v1': 0, 'v2': 3, 'v3': 0}, False),

              ([1, 2, 5, 6], 2, {'v1': 1,}, True),
              ([1, 2, 5, 6], 2, {'v1': 1, 'v2': 3}, True),

              ([1, 2, 5, 6], 2, {'v1': 1, 'v2': 3, 'v3': 5}, True),   # 2 in
              ([1, 2, 5, 6], 2, {'v1': 0, 'v2': 5, 'v3': 6}, True),   # 2 in
              ([1, 2, 5, 6], 2, {'v1': 2, 'v2': 5, 'v3': 5}, False),  # 3 in
              ([1, 2, 5, 6], 2, {'v1': 0, 'v2': 3, 'v3': 6}, False),   # 0 in
              ]

    @pytest.mark.parametrize('inset, req_nbr, assign, exp', SCASES)
    def test_conditions(self, inset, req_nbr, assign, exp):

        con = cnstr.ExactlyNIn(inset, req_nbr)
        con.set_variables(stubs.make_vars([('v1', range(6)),
                                           ('v2', range(6)),
                                           ('v3', range(6))]))
        assert con.satisfied(assign) == exp


    @pytest.fixture
    def vobjs_fixt(self):
        return stubs.make_vars([('var1', [3, 7, 12]),
                                ('var2', [1, 6, 9]),
                                ('var3', [5, 6, 10])])

    FCASES = [
     # const met  - tried to delete good vals from var1 but there are none
     ({'var2': 6, 'var3': 5}, set(), [[3, 7, 12], [1, 6, 9], [5, 6, 10]]),

     # const met- v1 and v3 meet constrataint (invalid assign 1--so what)
     #   it forces dom of var2 to be reduced
     ({'var1': 2, 'var3': 5}, {'var2'}, [[3, 7, 12], [9], [5, 6, 10]]),

     # unassigned must be good_vals
     ({'var1': 3}, {'var2', 'var3'}, [[3, 7, 12], [1, 6], [5, 6]]),

     # 1 good, 2 unassigned - can't do domain reduction
     ({'var1': 2}, True, [[3, 7, 12], [1, 6, 9], [5, 6, 10]]),

     # can't meet by numbers
     ({'var1': 3, 'var2': 9}, False, [[3, 7, 12], [1, 6, 9], [5, 6, 10]]),

     # can't meet by domain reduction
     ({'var2': 6, 'var3': 10}, False, [[], [1, 6, 9], [5, 6, 10]]),
     ]

    @pytest.mark.parametrize('assign, exp_ret, exp_domains', FCASES)
    def test_fwd_check(self, vobjs_fixt, assign, exp_ret, exp_domains):

        con = cnstr.ExactlyNIn([1, 2, 5, 6], 2)
        con.set_variables(vobjs_fixt)

        assert con.forward_check(assign) == exp_ret

        assert vobjs_fixt[0].get_domain() == exp_domains[0]
        assert vobjs_fixt[1].get_domain() == exp_domains[1]
        assert vobjs_fixt[2].get_domain() == exp_domains[2]



class TestAtLeastNInCnstr:

    def test_construct(self):
        aln = cnstr.AtLeastNIn([2, 3, 8], 1)
        assert 'AtLeastNIn' in repr(aln)
        assert isinstance(aln, cnstr.AtLeastNIn)
        assert aln._elements == [2, 3, 8]
        assert aln._params == 0
        assert aln._req_nbr == 1

        aln = cnstr.AtLeastNIn([2, 3, 8, 9, 10], 2)
        assert aln._elements == [2, 3, 8, 9, 10]
        assert aln._params == 0
        assert aln._req_nbr == 2


    def test_preprocess(self):

        con = cnstr.AtLeastNIn([2, 3, 8, 9, 10], 1)
        con.set_variables(stubs.make_vars([('var1', [3, 6, 9, 10]),
                                           ('var2', [1, 4, 10, 11])]))
        assert not con.preprocess()

        con = cnstr.AtLeastNIn([2, 3, 8, 9, 10], 4)
        with pytest.raises(cnstr.ConstraintError):
            con.set_variables(stubs.make_vars([(3, [3, 4, 8]),
                                               (4, [3, 4, 5]),
                                               (5, [1, 2, 3]),
                                               (6, [1, 2])]))

        con = cnstr.AtLeastNIn([2, 3, 8, 9, 10], 5)
        with pytest.raises(cnstr.ConstraintError):
            con.set_variables(stubs.make_vars([(3, [3, 4, 8]),
                                               (4, [3, 4, 5]),
                                               (5, [1, 2, 3]),
                                               (6, [1, 2])]))

    SCASES = [
        ([1, 2, 5, 6], 1, {'v1': 1, 'v2': 3}, True),
        ([1, 2, 5, 6], 1, {'v1': 0, 'v2': 5}, True),
        ([1, 2, 5, 6], 1, {'v1': 2, 'v2': 5}, True),
        ([1, 2, 5, 6], 1, {'v1': 0, 'v2': 3}, False),

        ([1, 2, 5, 6], 1, {'v1': 1}, True),
        ([1, 2, 5, 6], 1, {'v2': 5}, True),
        ([1, 2, 5, 6], 1, {'v1': 3}, True),
        ([1, 2, 5, 6], 1, {'v2': 0}, True),
         ]
    @pytest.mark.parametrize('inset, req_nbr, assign, exp', SCASES)
    def test_conditions(self, inset, req_nbr, assign, exp):

        con = cnstr.AtLeastNIn(inset, req_nbr)
        con.set_variables(stubs.make_vars([('v1', range(6)),
                                           ('v2', range(6))]))
        assert con.satisfied(assign) == exp

    @pytest.fixture
    def vobjs_fixt(self):
        return stubs.make_vars([('var1', [3, 7, 12]),
                                ('var2', [1, 6, 9]),
                                ('var3', [5, 6, 10])])

    FCASES = [
         # const met
         ({'var2': 6, 'var3': 5}, True, [[3, 7, 12], [1, 6, 9], [5, 6, 10]]),

         # unassigned must be good_vals
         ({'var1': 3}, {'var2', 'var3'}, [[3, 7, 12], [1, 6], [5, 6]]),

         # 1 good, 2 unassigned - can't do domain reduction
         ({'var1': 2}, True, [[3, 7, 12], [1, 6, 9], [5, 6, 10]]),

         # can't meet by numbers
         ({'var1': 3, 'var2': 9}, False, [[3, 7, 12], [1, 6, 9], [5, 6, 10]]),

         # can't meet by domain reduction
         ({'var2': 6, 'var3': 10}, False, [[], [1, 6, 9], [5, 6, 10]]),
         ]

    @pytest.mark.parametrize('assign, exp_ret, exp_domains', FCASES)
    def test_fwd_check(self, vobjs_fixt, assign, exp_ret, exp_domains):

        con = cnstr.AtLeastNIn([1, 2, 5, 6], 2)
        con.set_variables(vobjs_fixt)

        assert con.forward_check(assign) == exp_ret

        assert vobjs_fixt[0].get_domain() == exp_domains[0]
        assert vobjs_fixt[1].get_domain() == exp_domains[1]
        assert vobjs_fixt[2].get_domain() == exp_domains[2]



class TestAtMostNInCnstr:

    def test_construct(self):
        aln = cnstr.AtMostNIn([2, 3, 8], 1)
        assert 'AtMostNIn' in repr(aln)
        assert isinstance(aln, cnstr.AtMostNIn)
        assert aln._elements == [2, 3, 8]
        assert aln._params == 0
        assert aln._req_nbr == 1

        aln = cnstr.AtMostNIn([2, 3, 8, 9, 10], 2)
        assert aln._elements == [2, 3, 8, 9, 10]
        assert aln._params == 0
        assert aln._req_nbr == 2


    def test_preprocess(self):

        con = cnstr.AtMostNIn([2, 3, 8, 9, 10], 1)
        con.set_variables(stubs.make_vars([('var1', [3, 6, 9, 10]),
                                           ('var2', [1, 4, 10, 11])]))
        assert not con.preprocess()

        con = cnstr.AtMostNIn([2, 3, 8, 9, 10], 4)
        with pytest.raises(cnstr.ConstraintError):
            con.set_variables(stubs.make_vars([(3, [3, 4, 8]),
                                               (4, [3, 4, 5]),
                                               (5, [1, 2, 3]),
                                               (6, [1, 2])]))

        con = cnstr.AtMostNIn([2, 3, 8, 9, 10], 5)
        with pytest.raises(cnstr.ConstraintError):
            con.set_variables(stubs.make_vars([(3, [3, 4, 8]),
                                               (4, [3, 4, 5]),
                                               (5, [1, 2, 3]),
                                               (6, [1, 2])]))

    SCASES = [
        ([1, 2, 5, 6], 1, {'v1': 1, 'v2': 3}, True),
        ([1, 2, 5, 6], 1, {'v1': 0, 'v2': 5}, True),
        ([1, 2, 5, 6], 1, {'v1': 2, 'v2': 5}, False),
        ([1, 2, 5, 6], 1, {'v1': 0, 'v2': 3}, True),   # 0 is at most

        ([1, 2, 5, 6], 1, {'v1': 1}, True),
        ([1, 2, 5, 6], 1, {'v2': 5}, True),
        ([1, 2, 5, 6], 1, {'v1': 3}, True),
        ([1, 2, 5, 6], 1, {'v2': 0}, True),
         ]
    @pytest.mark.parametrize('inset, req_nbr, assign, exp', SCASES)
    def test_conditions(self, inset, req_nbr, assign, exp):

        con = cnstr.AtMostNIn(inset, req_nbr)
        con.set_variables(stubs.make_vars([('v1', range(6)),
                                           ('v2', range(6))]))
        assert con.satisfied(assign) == exp

    @pytest.fixture
    def vobjs_fixt(self):
        return stubs.make_vars([('var1', [3, 7, 12]),
                                ('var2', [1, 6, 9]),
                                ('var3', [5, 6, 10])])

    FCASES = [
         # const met - attempt to reduce 1, but nothing
         ({'var2': 6, 'var3': 5}, set(), [[3, 7, 12], [1, 6, 9], [5, 6, 10]]),

         # no dom reductions
         ({'var1': 3}, True, [[3, 7, 12], [1, 6, 9], [5, 6, 10]]),

         # const met- v1 and v3 meet constrataint (invalid assign 1--so what)
         #   it forces dom of var2 to be reduced
         ({'var1': 2, 'var3': 5}, {'var2'}, [[3, 7, 12], [9], [5, 6, 10]]),
         ]

    @pytest.mark.parametrize('assign, exp_ret, exp_domains', FCASES)
    def test_fwd_check(self, vobjs_fixt, assign, exp_ret, exp_domains):

        con = cnstr.AtMostNIn([1, 2, 5, 6], 2)
        con.set_variables(vobjs_fixt)

        result = con.forward_check(assign)
        print(result)
        print('var1', vobjs_fixt[0].get_domain())
        print('var2', vobjs_fixt[1].get_domain())
        print('var3', vobjs_fixt[2].get_domain())
        assert result == exp_ret

        assert vobjs_fixt[0].get_domain() == exp_domains[0]
        assert vobjs_fixt[1].get_domain() == exp_domains[1]
        assert vobjs_fixt[2].get_domain() == exp_domains[2]


# %% NotIn

class TestAtLeastNNotIn:

    def test_construct(self):
        aln = cnstr.AtLeastNNotIn([2, 3, 8], 1)
        assert 'AtLeastNNotIn' in repr(aln)
        assert isinstance(aln, cnstr.AtLeastNNotIn)
        assert aln._elements == [2, 3, 8]
        assert aln._params == 0
        assert aln._req_nbr == 1

        aln = cnstr.AtLeastNNotIn([2, 3, 8, 9, 10], 2)
        assert aln._elements == [2, 3, 8, 9, 10]
        assert aln._params == 0
        assert aln._req_nbr == 2


    def test_preprocess(self):

        con = cnstr.AtLeastNNotIn([2, 3, 8, 9, 10], 1)
        con.set_variables(stubs.make_vars([('var1', [3, 6, 9, 10]),
                                           ('var2', [1, 4, 10, 11])]))
        assert not con.preprocess()

        con = cnstr.AtLeastNNotIn([2, 3, 8, 9, 10], 4)
        with pytest.raises(cnstr.ConstraintError):
            con.set_variables(stubs.make_vars([(3, [3, 4, 8]),
                                               (4, [3, 4, 5]),
                                               (5, [1, 2, 3]),
                                               (6, [1, 2])]))

        con = cnstr.AtLeastNNotIn([2, 3, 8, 9, 10], 5)
        with pytest.raises(cnstr.ConstraintError):
            con.set_variables(stubs.make_vars([(3, [3, 4, 8]),
                                               (4, [3, 4, 5]),
                                               (5, [1, 2, 3]),
                                               (6, [1, 2])]))

    @pytest.mark.parametrize(
        'inset, req_nbr, assign, exp',
        [([1, 2, 5, 6], 1, {'v1': 1, 'v2': 3}, True),
         ([1, 2, 5, 6], 1, {'v1': 0, 'v2': 5}, True),
         ([1, 2, 5, 6], 1, {'v1': 2, 'v2': 5}, False),
         ([1, 2, 5, 6], 1, {'v1': 0, 'v2': 3}, True),

         ([1, 2, 5, 6], 1, {'v1': 1}, True),
         ([1, 2, 5, 6], 1, {'v2': 5}, True),
         ([1, 2, 5, 6], 1, {'v1': 3}, True),
         ([1, 2, 5, 6], 1, {'v2': 0}, True),

         # ([1, 2, 5, 6], 1, True, {'v1': 1, 'v2': 3}, True),
         # ([1, 2, 5, 6], 1, True, {'v1': 0, 'v2': 5}, True),
         # ([1, 2, 5, 6], 1, True, {'v1': 2, 'v2': 5}, False),
         # ([1, 2, 5, 6], 1, True, {'v1': 0, 'v2': 3}, False),

         ])
    def test_conditions(self, inset, req_nbr, assign, exp):

        con = cnstr.AtLeastNNotIn(inset, req_nbr)
        con.set_variables(stubs.make_vars([('v1', range(6)),
                                          ('v2', range(6))]))
        assert con.satisfied(assign) == exp

    @pytest.fixture
    def vobjs_fixt(self):
        return stubs.make_vars([('var1', [1, 2, 5]),
                                ('var2', [1, 6, 9]),
                                ('var3', [5, 6, 10])])

    @pytest.mark.parametrize(
        'assign, exp_ret, exp_domains',

        [
         # const met
         ({'var2': 3, 'var3': 4}, True, [[1, 2, 5], [1, 6, 9], [5, 6, 10]]),

         # unassigned must be bad_vals
         ({'var1': 6}, {'var2', 'var3'}, [[1, 2, 5], [9], [10]]),

         # can't meet by numbers
         ({'var1': 6, 'var2': 6}, False, [[1, 2, 5], [1, 6, 9], [5, 6, 10]]),

         # can't meet by domain reduction
         ({'var2': 6, 'var3': 10}, False, [[], [1, 6, 9], [5, 6, 10]]),
         ])
    def test_fwd_check(self, vobjs_fixt, assign, exp_ret, exp_domains):

        con = cnstr.AtLeastNNotIn([1, 2, 5, 6], 2)
        con.set_variables(vobjs_fixt)

        assert con.forward_check(assign) == exp_ret

        assert vobjs_fixt[0].get_domain() == exp_domains[0]
        assert vobjs_fixt[1].get_domain() == exp_domains[1]
        assert vobjs_fixt[2].get_domain() == exp_domains[2]
