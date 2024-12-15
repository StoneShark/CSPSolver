# -*- coding: utf-8 -*-
"""
Created on Sun Dec 15 12:52:11 2024

@author: Ann
"""


# %% imports


import pytest

from csp_solver import constraint as cnstr
import stubs


# %% tests

class TestMaxSum:
    # no need to test partials, just check the assignments already done

    def test_construct(self):
        msc = cnstr.MaxSum(20)
        assert 'MaxSum' in repr(msc)
        assert isinstance(msc, cnstr.MaxSum)

        assert msc._maxsum == 20


    def test_preprocess(self):

        con = cnstr.MaxSum(5)

        vobjs_list = stubs.make_vars([('var1', [3])])
        con.set_variables(vobjs_list)
        assert con.preprocess()
        assert vobjs_list[0].get_domain() == [3]

        vobjs_list = stubs.make_vars([('var1', [6])])
        con.set_variables(vobjs_list)
        with pytest.raises(cnstr.PreprocessorConflict):
            con.preprocess()

        vobjs_list = stubs.make_vars([('var1', [6, 9, 10])])
        con.set_variables(vobjs_list)
        with pytest.raises(cnstr.PreprocessorConflict):
            con.preprocess()

        vobjs_list = stubs.make_vars([('var1', [3, 6, 9, 10])])
        con.set_variables(vobjs_list)
        assert con.preprocess()
        assert sorted(vobjs_list[0].get_domain()) == [3]

        vobjs_list = stubs.make_vars([('var1', [6, 9, 10]),
                                      ('var2', [10, 11])])
        con.set_variables(vobjs_list)
        with pytest.raises(cnstr.PreprocessorConflict):
            con.preprocess()

        vobjs_list = stubs.make_vars([('var1', [3, 6, 9, 10]),
                                      ('var2', [2, 4, 10, 11])])
        con.set_variables(vobjs_list)
        assert con.preprocess()
        assert sorted(vobjs_list[0].get_domain()) == [3]
        assert sorted(vobjs_list[1].get_domain()) == [2]

        vobjs_list = stubs.make_vars([('var1', [3, 6, 9, 10]),
                                      ('var2', [1, 2, 10, 11])])
        con.set_variables(vobjs_list)
        assert con.preprocess()
        assert sorted(vobjs_list[0].get_domain()) == [3]
        assert sorted(vobjs_list[1].get_domain()) == [1, 2]

        vobjs_list = stubs.make_vars([('var1', [3, 4, 9, 10]),
                                      ('var2', [1, 2, 10, 11]),
                                      ('var3', [0, 2, 10, 11])])
        con.set_variables(vobjs_list)
        assert not con.preprocess()
        assert sorted(vobjs_list[0].get_domain()) == [3, 4]
        assert sorted(vobjs_list[1].get_domain()) == [1, 2]
        assert sorted(vobjs_list[2].get_domain()) == [0, 2]

        vobjs_list = stubs.make_vars([('var1', [3, 6, 9, 10]),
                                      ('var2', [2, 10, 11]),
                                      ('var3', [0, 8, 10, 11])])
        con.set_variables(vobjs_list)
        assert con.preprocess()
        assert vobjs_list[0].get_domain() == [3]
        assert vobjs_list[1].get_domain() == [2]
        assert vobjs_list[2].get_domain() == [0]

        vobjs_list = stubs.make_vars([('var1', [3, 4]),
                                      ('var2', [1, 2, 11]),
                                      ('var3', [0, 2, 11])])
        con = cnstr.MaxSum(10)
        con.set_variables(vobjs_list)
        assert con.preprocess()
        assert sorted(vobjs_list[0].get_domain()) == [3, 4]
        assert sorted(vobjs_list[1].get_domain()) == [1, 2]
        assert sorted(vobjs_list[2].get_domain()) == [0, 2]


    def test_max_sum(self):

        con = cnstr.MaxSum(5)

        assignments = {'var1': 3}
        assert con.satisfied(assignments)

        assignments = {'var1': 5}
        assert con.satisfied(assignments)

        assignments = {'var1': 6}
        assert not con.satisfied(assignments)

        assignments = {'var1': 3, 'var2': 1}
        assert con.satisfied(assignments)

        assignments = {'var1': 3, 'var2': 2}
        assert con.satisfied(assignments)

        assignments = {'var1': 3, 'var2': 3}
        assert not con.satisfied(assignments)


    def test_fwd_check(self):

        vobjs_list = stubs.make_vars([('var1', [3, 5, 12])])
        fc = cnstr.MaxSum(6)
        fc.set_variables(vobjs_list)
        assignments = {'var1': 3}
        assert fc.forward_check(assignments) == set()
        assert vobjs_list[0].get_domain() == [3, 5, 12]

        vobjs_list = stubs.make_vars([('var1', [3, 5, 12]),
                                      ('var2', [3, 6])])
        fc = cnstr.MaxSum(6)
        fc.set_variables(vobjs_list)
        assignments = {'var1': 3}
        assert fc.forward_check(assignments) == {'var2'}
        assert vobjs_list[0].get_domain() == [3, 5, 12]
        assert vobjs_list[1].get_domain() == [3]

        vobjs_list = stubs.make_vars([('var1', [3, 5, 12]),
                                      ('var2', [2, 6]),
                                      ('var3', [1, 7])])
        fc = cnstr.MaxSum(6)
        fc.set_variables(vobjs_list)
        assignments = {'var1': 3}
        assert fc.forward_check(assignments) == {'var2', 'var3'}
        assert vobjs_list[0].get_domain() == [3, 5, 12]
        assert vobjs_list[1].get_domain() == [2]
        assert vobjs_list[2].get_domain() == [1]

        vobjs_list = stubs.make_vars([('var1', [3, 5, 12]),
                                      ('var2', [2, 6]),
                                      ('var3', [5, 6])])
        fc = cnstr.MaxSum(6)
        fc.set_variables(vobjs_list)
        assignments = {'var1': 3, 'var2': 2}
        assert not fc.forward_check(assignments)
        assert vobjs_list[0].get_domain() == [3, 5, 12]
        assert vobjs_list[1].get_domain() == [2, 6]
        assert vobjs_list[2].get_domain() == []


class TestExactSum:

    def test_construct(self):
        esc = cnstr.ExactSum(20)
        assert 'ExactSum' in repr(esc)
        assert isinstance(esc, cnstr.ExactSum)

        assert esc._exactsum == 20
        assert esc._params == 0


    def test_preprocess(self):

        con = cnstr.ExactSum(5)

        vobjs_list = stubs.make_vars([('var1', [3])])
        con.set_variables(vobjs_list)
        with pytest.raises(cnstr.PreprocessorConflict):
            con.preprocess()

        vobjs_list = stubs.make_vars([('var1', [6])])
        con.set_variables(vobjs_list)
        with pytest.raises(cnstr.PreprocessorConflict):
            con.preprocess()

        vobjs_list = stubs.make_vars([('var1', [6, 9, 10])])
        con.set_variables(vobjs_list)
        with pytest.raises(cnstr.PreprocessorConflict):
            con.preprocess()

        vobjs_list = stubs.make_vars([('var1', [3, 6, 9, 10])])
        con.set_variables(vobjs_list)
        with pytest.raises(cnstr.PreprocessorConflict):
            con.preprocess()

        con = cnstr.ExactSum(5)

        vobjs_list = stubs.make_vars([('var1', [6, 9, 10]),
                                      ('var2', [10, 11])])
        con.set_variables(vobjs_list)
        with pytest.raises(cnstr.PreprocessorConflict):
            con.preprocess()

        vobjs_list = stubs.make_vars([('var1', [3, 4, 9, 10]),
                                      ('var2', [1, 2, 10, 11])])
        con.set_variables(vobjs_list)
        assert not con.preprocess()
        assert sorted(vobjs_list[0].get_domain()) == [3, 4]
        assert sorted(vobjs_list[1].get_domain()) == [1, 2]

        vobjs_list = stubs.make_vars([('var1', [3, 6, 9, 10]),
                                      ('var2', [1, 2, 10, 11])])
        con.set_variables(vobjs_list)
        assert con.preprocess()
        assert vobjs_list[0].get_domain() == [3]
        assert vobjs_list[1].get_domain() == [2]

        vobjs_list = stubs.make_vars([('var1', [3, 4, 9, 10]),
                                      ('var2', [1, 2, 10, 11]),
                                      ('var3', [0, 2, 10, 11])])
        con = cnstr.ExactSum(5)
        con.set_variables(vobjs_list)
        assert not con.preprocess()
        assert sorted(vobjs_list[0].get_domain()) == [3, 4]
        assert sorted(vobjs_list[1].get_domain()) == [1, 2]
        assert sorted(vobjs_list[2].get_domain()) == [0, 2]

        vobjs_list = stubs.make_vars([('var1', [3, 6, 9, 10]),
                                      ('var2', [2, 10, 11]),
                                      ('var3', [0, 8, 10, 11])])
        con.set_variables(vobjs_list)
        assert con.preprocess()
        assert vobjs_list[0].get_domain() == [3]
        assert vobjs_list[1].get_domain() == [2]
        assert vobjs_list[2].get_domain() == [0]


    def test_conditions(self):

        con = cnstr.ExactSum(5)
        con.set_variables(stubs.make_vars([('var1', range(6))]))

        assignments = {'var1': 3}
        assert not con.satisfied(assignments)

        assignments = {'var1': 6}
        assert not con.satisfied(assignments)

        con.set_variables(stubs.make_vars([('var1', range(6)),
                                           ('var2', range(6))]))

        assignments = {'var1': 3, 'var2': 1}
        assert not con.satisfied(assignments)

        assignments = {'var1': 3, 'var2': 2}
        assert con.satisfied(assignments)

        assignments = {'var1': 3, 'var2': 3}
        assert not con.satisfied(assignments)


    def test_partial_assings(self):

        con = cnstr.ExactSum(5)
        con.set_variables(stubs.make_vars([('var1', range(6)),
                                           ('var2', range(6))]))

        assignments = {'var1': 3}
        assert con.satisfied(assignments)

        con.set_variables(stubs.make_vars([('var1', range(6)),
                                           ('var2', range(6)),
                                           ('var3', range(6))]))

        assignments = {'var1': 3, 'var2': 1}
        assert con.satisfied(assignments)

        assignments = {'var1': 3, 'var2': 2}
        assert con.satisfied(assignments)

        assignments = {'var1': 3, 'var2': 3}
        assert not con.satisfied(assignments)


    def test_fwd_check(self):

        vobjs_list = stubs.make_vars([('var1', [3, 5, 12])])
        fc = cnstr.ExactSum(6)
        fc.set_variables(vobjs_list)
        assignments = {'var1': 3}
        assert fc.forward_check(assignments) == set()
        assert vobjs_list[0].get_domain() == [3, 5, 12]

        vobjs_list = stubs.make_vars([('var1', [3, 5, 12]),
                                      ('var2', [3, 6])])
        fc = cnstr.ExactSum(6)
        fc.set_variables(vobjs_list)
        assignments = {'var1': 3}
        assert fc.forward_check(assignments) == {'var2'}
        assert vobjs_list[0].get_domain() == [3, 5, 12]
        assert vobjs_list[1].get_domain() == [3]

        vobjs_list = stubs.make_vars([('var1', [3, 5, 12]),
                                      ('var2', [2, 6]),
                                      ('var3', [1, 7])])
        fc = cnstr.ExactSum(6)
        fc.set_variables(vobjs_list)
        assignments = {'var1': 3}
        assert fc.forward_check(assignments) == {'var2', 'var3'}
        assert vobjs_list[0].get_domain() == [3, 5, 12]
        assert vobjs_list[1].get_domain() == [2]
        assert vobjs_list[2].get_domain() == [1]

        vobjs_list = stubs.make_vars([('var1', [3, 5, 12]),
                                      ('var2', [2, 6]),
                                      ('var3', [5, 6])])
        fc = cnstr.ExactSum(6)
        fc.set_variables(vobjs_list)
        assignments = {'var1': 3, 'var2': 2}
        assert not fc.forward_check(assignments)
        assert vobjs_list[0].get_domain() == [3, 5, 12]
        assert vobjs_list[1].get_domain() == [2, 6]
        assert vobjs_list[2].get_domain() == []


class TestMinSum:

    def test_construct(self):
        msc = cnstr.MinSum(20)
        assert 'MinSum' in repr(msc)
        assert isinstance(msc, cnstr.MinSum)

        assert msc._minsum == 20
        assert msc._params == 0


    def test_preprocess(self):

        con = cnstr.MinSum(5)

        vobjs_list = stubs.make_vars([('var1', [3])])
        con.set_variables(vobjs_list)
        with pytest.raises(cnstr.PreprocessorConflict):
            con.preprocess()

        vobjs_list = stubs.make_vars([('var1', [6])])
        con.set_variables(vobjs_list)
        assert con.preprocess()
        assert vobjs_list[0].get_domain() == [6]

        vobjs_list = stubs.make_vars([('var1', [6, 9, 10])])
        con.set_variables(vobjs_list)
        assert con.preprocess()
        assert vobjs_list[0].get_domain() == [6, 9, 10]

        vobjs_list = stubs.make_vars([('var1', [3, 6, 9, 10])])
        con.set_variables(vobjs_list)
        assert con.preprocess()
        assert vobjs_list[0].get_domain() == [6, 9, 10]

        vobjs_list = stubs.make_vars([('var1', [2, 3]),
                                      ('var2', [1, 3])])
        con = cnstr.MinSum(7)
        con.set_variables(vobjs_list)
        with pytest.raises(cnstr.PreprocessorConflict):
            con.preprocess()

        vobjs_list = stubs.make_vars([('var1', [3, 6, 9, 10]),
                                      ('var2', [1, 4, 10, 11])])
        con = cnstr.MinSum(5)
        con.set_variables(vobjs_list)
        assert not con.preprocess()
        assert sorted(vobjs_list[0].get_domain()) == [3, 6, 9, 10]
        assert sorted(vobjs_list[1].get_domain()) == [1, 4, 10, 11]

        vobjs_list = stubs.make_vars([('var1', [6, 9, 10]),
                                      ('var2', [10, 11])])
        con = cnstr.MinSum(10)
        con.set_variables(vobjs_list)
        assert con.preprocess()
        assert sorted(vobjs_list[0].get_domain()) == [6, 9, 10]
        assert sorted(vobjs_list[1].get_domain()) == [10, 11]

        vobjs_list = stubs.make_vars([('var1', [2, 3, 5]),
                                      ('var2', [1, 2, 3]),
                                      ('var3', [0, 1])])
        con = cnstr.MinSum(10)
        con.set_variables(vobjs_list)
        with pytest.raises(cnstr.PreprocessorConflict):
            con.preprocess()


    def test_min_sum(self):

        con = cnstr.MinSum(5)
        con.set_variables(stubs.make_vars([('var1', range(7))]))

        assignments = {'var1': 6}
        assert con.satisfied(assignments)

        assignments = {'var1': 5}
        assert con.satisfied(assignments)

        assignments = {'var1': 3}
        assert not con.satisfied(assignments)

        con.set_variables(stubs.make_vars([('var1', range(7)),
                                           ('var2', range(7))]))

        assignments = {'var1': 3, 'var2': 3}
        assert con.satisfied(assignments)

        assignments = {'var1': 3, 'var2': 2}
        assert con.satisfied(assignments)

        assignments = {'var1': 3, 'var2': 1}
        assert not con.satisfied(assignments)


    def test_partial_assings(self):

        con = cnstr.MinSum(5)
        con.set_variables(stubs.make_vars([('var1', range(7)),
                                           ('var2', range(7))]))

        assignments = {'var1': 3}
        assert con.satisfied(assignments)

        con.set_variables(stubs.make_vars([('var1', range(7)),
                                           ('var2', range(7)),
                                           ('var3', range(7))]))

        assignments = {'var1': 3, 'var2': 1}
        assert con.satisfied(assignments)


    def test_fwd_check(self):
        assert cnstr.MinSum(3).forward_check(None)
