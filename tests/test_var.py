# -*- coding: utf-8 -*-
"""
Created on Sun May  7 11:49:58 2023

@author: Ann
"""

# %% imports

import pytest

import csp_solver as csp

# %%

class TestVariable:

    @pytest.fixture
    def var_fixt(self):

        return csp.Variable('var_name', range(10))


    def test_contruction(self, var_fixt):

        assert var_fixt.name == 'var_name'
        assert len(var_fixt._domain) == 10
        assert len(var_fixt._hidden) == 0
        assert len(list(var_fixt._nbr_remain)) == 0

        assert var_fixt.nbr_values() == 10
        assert var_fixt.get_domain() == var_fixt._domain
        assert var_fixt.get_domain() is var_fixt._domain
        assert var_fixt.get_domain() == list(range(10))

        assert not list(var_fixt._nbr_remain)
        assert not var_fixt._hidden


    def test_domain_const(self):

        domain = list(range(10))
        tvar1 = csp.Variable('var_name', domain)
        tvar2 = csp.Variable('var_name', domain)

        assert tvar1.get_domain() == tvar1._domain
        assert tvar1.get_domain() is not domain
        assert tvar1.get_domain() == list(range(10))

        assert tvar2.get_domain() == tvar2._domain
        assert tvar2.get_domain() is not domain
        assert tvar2.get_domain() == list(range(10))

        assert tvar1.get_domain() is not tvar2.get_domain()
        assert tvar1._domain is not tvar2._domain

        tvar1.remove_dom_val(5)

        assert tvar1._domain == [0, 1, 2, 3, 4, 6, 7, 8, 9]
        assert tvar2._domain == list(range(10))

        domain = [0, 1, 2]
        tvar1.set_domain(domain)
        assert tvar1.get_domain() == [0, 1, 2]


    @pytest.mark.parametrize('rval, exp',
                             [(0, list(range(1,10))),
                              (9, list(range(9))),
                              (5, [0, 1, 2, 3, 4, 6, 7, 8, 9])
                              ])
    def test_remove_dom_val(self, var_fixt, rval, exp):
        var_fixt.remove_dom_val(rval)
        assert var_fixt.get_domain() == exp


    def test_remove_all(self, var_fixt):

        for i in range(10):
            var_fixt.remove_dom_val(i)

        assert not var_fixt.get_domain()
        assert var_fixt.get_domain() == []


    def test_remove_missing(self, var_fixt):

        with pytest.raises(ValueError):
            var_fixt.remove_dom_val(10)


    def test_history(self, var_fixt):

        var_fixt.push_domain()
        var_fixt.pop_domain()

        assert var_fixt.get_domain() == list(range(10))


    def test_hide(self):

        vobj = csp.Variable('var', range(4))

        with pytest.raises(ValueError):
            assert vobj.hide(10)

        assert vobj.hide(3)
        assert vobj.hide(2)
        assert vobj.hide(1)
        assert not vobj.hide(0)    # last value, now domain is empty


    @pytest.mark.parametrize('rval, exp',
                             [(0, list(range(1,10))),
                              (9, list(range(9))),
                              (5, [0, 1, 2, 3, 4, 6, 7, 8, 9])
                              ])
    def test_hist_2(self, var_fixt, rval, exp):

        var_fixt.push_domain()

        assert list(var_fixt._nbr_remain) == [10]

        assert var_fixt.hide(rval)
        assert var_fixt.get_domain() == exp
        assert var_fixt._hidden == [rval]

        var_fixt.pop_domain()

        assert sorted(var_fixt.get_domain()) == list(range(10))


    def test_hist_3(self, var_fixt):

        var_fixt.push_domain()  # first push
        assert list(var_fixt._nbr_remain) == [10]

        assert var_fixt.hide(3)
        assert var_fixt.hide(7)

        assert var_fixt._hidden == [3, 7]
        assert var_fixt.get_domain() == [0, 1, 2, 4, 5, 6, 8, 9]

        var_fixt.push_domain()   # second push
        assert list(var_fixt._nbr_remain) == [10, 8]

        assert var_fixt.hide(4)
        assert var_fixt.hide(5)
        assert var_fixt.hide(9)

        assert sorted(var_fixt.get_domain()) == [0, 1, 2, 6, 8]
        assert var_fixt._hidden == [3, 7, 4, 5, 9]

        var_fixt.push_domain()   # third push
        assert list(var_fixt._nbr_remain) == [10, 8, 5]
        var_fixt.pop_domain()    # pop third

        assert list(var_fixt._nbr_remain) == [10, 8]

        var_fixt.pop_domain()   # pop second

        assert list(var_fixt._nbr_remain) == [10]
        assert var_fixt._hidden == [3, 7]
        assert sorted(var_fixt.get_domain()) == [0, 1, 2, 4, 5, 6, 8, 9]

        var_fixt.pop_domain()  # pop first

        assert list(var_fixt._nbr_remain) == []
        assert var_fixt._hidden == []
        assert sorted(var_fixt.get_domain()) == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


    def test_hist_errros(self, var_fixt):

        var_fixt.push_domain()  # first push
        assert list(var_fixt._nbr_remain) == [10]

        var_fixt.pop_domain()  # pop first

        assert list(var_fixt._nbr_remain) == []
        assert var_fixt._hidden == []
        assert sorted(var_fixt.get_domain()) == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

        with pytest.raises(IndexError):
            var_fixt.pop_domain()  # extra pop


    def test_hist_reset(self, var_fixt):

        var_fixt.push_domain()  # first push
        assert list(var_fixt._nbr_remain) == [10]

        assert var_fixt.hide(3)
        assert var_fixt.hide(7)

        assert var_fixt._hidden == [3, 7]
        assert var_fixt.get_domain() == [0, 1, 2, 4, 5, 6, 8, 9]

        var_fixt.push_domain()   # second push
        assert list(var_fixt._nbr_remain) == [10, 8]

        assert var_fixt.hide(4)
        assert var_fixt.hide(5)
        assert var_fixt.hide(9)

        assert sorted(var_fixt.get_domain()) == [0, 1, 2, 6, 8]
        assert var_fixt._hidden == [3, 7, 4, 5, 9]

        var_fixt.reset_dhist()

        assert list(var_fixt._nbr_remain) == []
        assert var_fixt._hidden == []
        assert sorted(var_fixt.get_domain()) == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
