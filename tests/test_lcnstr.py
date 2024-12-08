# -*- coding: utf-8 -*-
"""
Created on Mon Jun 12 13:31:39 2023

@author: Ann
"""


# %% imports

import operator as op

import pytest

from csp_solver import constraint as cnstr
from csp_solver import list_constraint as lcnstr


# %%

class TestListConstraint:

    def test_contruct(self):

        # ListConstraint really isn't intended to be instantiated
        lcon = lcnstr.ListConstraint(op.le)
        assert lcon._req_nbr == 1
        assert not lcon._exact
        assert not lcon._clist
        assert lcon._op == op.le

        lcon = lcnstr.ListConstraint(op.le, 3, True)
        assert lcon._req_nbr == 3
        assert lcon._exact
        assert lcon._op == op.le

        with pytest.raises(NotImplementedError):
            lcnstr.ListConstraint(op.eq)


    def test_add_constraints(self):

        lcon = lcnstr.ListConstraint(op.le, 3, True)

        with pytest.raises(ValueError):
            lcon.add_constraints(None)

        with pytest.raises(ValueError):
            lcon.add_constraints([cnstr.MaxSum(4)])

        # lcon.add_constraints([, cnstr.AllDifferent()])
        # assert len(lcon._clist) == 2
