# -*- coding: utf-8 -*-
"""
Created on Mon Jun 12 13:31:39 2023
@author: Ann"""


# %% imports

import pytest
pytestmark = pytest.mark.unittest

import csp_solver as csp
from csp_solver import constraint as cnstr
from csp_solver import list_constraint as lcnstr


# %%

class TestListConstraint:
    """Test basic construction with OneOfCList and OrCList.
    Base classes are test more below."""

    def test_contruct(self):

        lcon = lcnstr.OneOfCList()
        assert lcon._req_nbr == 1
        assert 'OneOfCList' in str(lcon)

        assert not lcon._clist
        assert not lcon.get_vnames()
        assert not lcon.preprocess()
        assert lcon.forward_check(None)


    def test_set_constraints(self):

        lcon = lcnstr.OrCList()
        assert lcon._req_nbr == 1
        assert 'OrCList' in str(lcon)

        with pytest.raises(ValueError):
            lcon.set_constraints(None)

        with pytest.raises(ValueError):
            lcon.set_constraints([cnstr.MaxSum(4)])

        v1 = csp.Variable('var1', [1, 2, 3, 4, 5])
        v2 = csp.Variable('var2', [1, 2, 3, 4, 5])
        clist = [0] * 3
        clist[0] = cnstr.InValues([3, 4])
        clist[0].set_variables([v1])
        clist[1] = cnstr.InValues([4, 5])
        clist[1].set_variables([v2])
        clist[2] = cnstr.AllEqual()
        clist[2].set_variables([v1, v2])

        lcon.set_constraints(clist)

        with pytest.raises(cnstr.ConstraintError):
            lcon.set_constraints(clist)


def get_id(case):
    """Build case id from the case tuple"""

    rnbr, vdict, rval = case

    return f"{rnbr}-" \
        + "-".join(f"{vnam}_{vval}" for vnam, vval in vdict.items()) \
            + f"-{rval}"


class TestAtLeastN:

    @pytest.fixture
    def aln_con(self, request):

        lcon = lcnstr.AtLeastNCList(request.param)

        v1 = csp.Variable('var1', [1, 2, 3, 4, 5])
        v2 = csp.Variable('var2', [1, 2, 3, 4, 5])

        clist = [0] * 3

        clist[0] = cnstr.InValues([3, 4])
        clist[0].set_variables([v1])

        clist[1] = cnstr.InValues([4, 5])
        clist[1].set_variables([v2])

        clist[2] = cnstr.AllEqual()
        clist[2].set_variables([v1, v2])

        lcon.set_constraints(clist)

        return lcon

    cases = [
        (1, {'var1': 2, 'var2': 1}, False),   # none sat
        (1, {'var1': 4}, True),              # partial assigns and 1 sat
        (1, {'var1': 4, 'var2': 5}, True),  # 2 sat
        (1, {'var1': 4, 'var2': 4}, True),  # all 3 sat

        (1, {'var1': 2}, True),   # partial assigns and 0 sat,
                                   # but allEQ returns T until !EQ found
                                  # to allow rem vars to be set
        (1, {'var1': 4}, True),   # partial assigns and 2 sat (inc allEQ)

        (2, {'var1': 4, 'var2': 5}, True),  # 2 sat one not
        (3, {'var1': 4, 'var2': 4}, True),  # all 3 sat

        ]

    @pytest.mark.parametrize('aln_con, assigns, esat',
                             cases, indirect=['aln_con'],
                             ids=[get_id(case) for case in cases])
    def test_aln_constr(self, aln_con, assigns, esat):

        assert sorted(aln_con._vnames) == ['var1', 'var2']
        assert len(aln_con._clist) == 3
        assert aln_con._params == 2

        assert aln_con.satisfied(assigns) == esat



class TestAtMostN:

    @pytest.fixture
    def amn_con(self, request):

        lcon = lcnstr.AtMostNCList(request.param)

        v1 = csp.Variable('var1', [1, 2, 3, 4, 5])
        v2 = csp.Variable('var2', [1, 2, 3, 4, 5])

        clist = [0] * 3

        clist[0] = cnstr.InValues([2, 3])
        clist[0].set_variables([v1])

        clist[1] = cnstr.InValues([2, 4])
        clist[1].set_variables([v2])

        clist[2] = cnstr.MaxSum(5)
        clist[2].set_variables([v1, v2])

        lcon.set_constraints(clist)

        return lcon


    cases = [
        (1, {'var1': 3, 'var2': 3}, True),    # T-F-F
        (1, {'var1': 5, 'var2': 4}, True),    # F-T-F
        (1, {'var1': 4, 'var2': 1}, True),    # F-F-T
        (1, {'var1': 4, 'var2': 5}, True),    # F-F-F
        (1, {'var1': 3, 'var2': 4}, False),   # T-T-F
        (1, {'var1': 3, 'var2': 2}, False),   # T-T-T

        (1, {'var1': 3}, True),   # T-T-d  partial assigns and 1 sat
                                           # InValue ret T if not assigned
        (1, {'var1': 6}, True),   # F-d-F partial assigns and 0 sat

        (2, {'var1': 3, 'var2': 3}, True),   # T-F-F
        (2, {'var1': 3, 'var2': 4}, True),   # T-T-F
        (3, {'var1': 3, 'var2': 2}, True),   # T-T-T

        ]

    @pytest.mark.parametrize('amn_con, assigns, esat',
                             cases,
                             indirect=['amn_con'],
                             ids=[get_id(case) for case in cases])
    def test_amn_constr(self, amn_con, assigns, esat):

        print(amn_con)
        assert sorted(amn_con._vnames) == ['var1', 'var2']
        assert len(amn_con._clist) == 3
        assert amn_con._params == 2

        assert amn_con.satisfied(assigns) == esat



def print_tt():
    """Truth table for TestNOoCList constraint (nof_con)"""

    print("     a       b       c       con1     con2    con3    cons met")
    print("-" * 65)
    for a in [False, True]:
        for b in [False, True]:
            for c in [False, True]:

                c1 = (a != b)
                c2 = (a or c)
                c3 = (not b or c)
                ans = sum([c1, c2, c3])
                print(f"{a:6}  {b:6}  {c:6}    {c1:6}  {c2:6}  {c3:6}   {ans:6}")


class TestNOfClist:

    @pytest.fixture
    def nof_con(self, request):

        lcon = lcnstr.NOfCList(request.param)

        a = csp.Variable('a', [False, True])
        b = csp.Variable('b', [False, True])
        c = csp.Variable('c', [False, True])

        clist = [0] * 3

        clist[0] = cnstr.AllDifferent()   #  a xor b  is  a != b
        clist[0].set_variables([a, b])

        clist[1] = cnstr.Or(True, True)             # a or c
        clist[1].set_variables([a, c])

        clist[2] = cnstr.IfThen(True, True)   # if b then c   is  not b or c
        clist[2].set_variables([b, c])

        lcon.set_constraints(clist)

        return lcon


    cases = [
        # one constraint met
        (1, {'a': 0, 'b': 0, 'c': 0}, True),
        (2, {'a': 0, 'b': 0, 'c': 0}, False),
        (3, {'a': 0, 'b': 0, 'c': 0}, False),

        # two constraints met
        (1, {'a': 0, 'b': 0, 'c': 1}, False),
        (2, {'a': 0, 'b': 0, 'c': 1}, True),
        (3, {'a': 0, 'b': 0, 'c': 1}, False),  # short circuit to F in loop

        # three constraints met
        (1, {'a': 0, 'b': 1, 'c': 1}, False),
        (2, {'a': 0, 'b': 1, 'c': 1}, False),
        (3, {'a': 0, 'b': 1, 'c': 1}, True),

        # not fully assigned -- always True
        (1, {'b': 0, 'c': 1}, True),
        (2, {'a': 0, 'c': 0}, True),
        (3, {'a': 0, 'b': 1}, True),
        ]

    @pytest.mark.parametrize('nof_con, assigns, esat',
                             cases,
                             indirect=['nof_con'],
                             ids=[get_id(case) for case in cases])
    def test_nof_constr(self, nof_con, assigns, esat):

        print(nof_con)
        assert sorted(nof_con._vnames) == ['a', 'b', 'c']
        assert len(nof_con._clist) == 3
        assert nof_con._params == 3

        assert nof_con.satisfied(assigns) == esat



    def test_too_params(self):
        """Confirm constraint can be met, e.g. req_br not too high"""

        lcon = lcnstr.NOfCList(3)

        a = csp.Variable('a', [False, True])
        b = csp.Variable('b', [False, True])
        c = csp.Variable('c', [False, True])

        clist = [0] * 2

        clist[0] = cnstr.AllDifferent()
        clist[0].set_variables([a, b])
        clist[1] = cnstr.Or(True, True)
        clist[1].set_variables([a, c])

        with pytest.raises(cnstr.ConstraintError):
            lcon.set_constraints(clist)
