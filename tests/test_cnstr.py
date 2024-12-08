# -*- coding: utf-8 -*-
"""
Created on Sun May  7 16:03:49 2023

@author: Ann
"""
# %% imports

import functools as ft
import operator as op

import pytest

from csp_solver import constraint as cnstr
import stubs


# %% test classes

class TestFunc:

    def test_construct(self):

        fc = cnstr.BoolFunction(op.neg)
        assert 'BoolFunction' in repr(fc)

        assert isinstance(fc, cnstr.BoolFunction)

        assert fc._func == op.neg
        assert fc._var_args == False
        assert fc._params == 0

        fc = cnstr.BoolFunction(op.eq, False)
        assert isinstance(fc, cnstr.BoolFunction)

        assert fc._func == op.eq
        assert fc._var_args == False
        assert fc._params == 0

        with pytest.raises(cnstr.ConstraintError):
            cnstr.BoolFunction(5)

        fc = cnstr.BoolFunction(ft.partial(op.eq, 4))
        assert 'BoolFunction' in repr(fc)
        assert 'eq(4' in repr(fc)

    def test_preprocess(self):

        con = cnstr.BoolFunction(lambda a: a == 3, False)
        con.set_variables(stubs.make_vars([('var1', [3])]))
        assert con.preprocess()

        con = cnstr.BoolFunction(lambda a: a == 3, False)
        con.set_variables(stubs.make_vars([('var1', [3, 6, 9, 10])]))
        assert con.preprocess()

        con = cnstr.BoolFunction(lambda a: a == 3, False)
        con.set_variables(stubs.make_vars([('var1', [6, 9, 10])]))
        with pytest.raises(cnstr.PreprocessorConflict):
            con.preprocess()

        con = cnstr.BoolFunction(lambda a, b: a == b, False)
        con.set_variables(stubs.make_vars([('var1', [3]),
                                           ('var2', [4])]))
        with pytest.raises(cnstr.PreprocessorConflict):
            con.preprocess()

        con = cnstr.BoolFunction(lambda a, b: a == b, False)
        con.set_variables(stubs.make_vars([('var1', [3, 5]),
                                           ('var2', [3, 4])]))
        assert con.preprocess()

        con = cnstr.BoolFunction(lambda a, b: a == b, False)
        con.set_variables(stubs.make_vars([('var1', [3, 5]),
                                           ('var2', [3, 4]),
                                           ('var3', [3, 5, 7])]))
        assert not con.preprocess()

    def test_func(self):

        var_list = stubs.make_vars([('var1', [1, 2, 3, 4, 5, 6]),
                                    ('var2', [1, 2, 3, 4, 5, 6])])

        con = cnstr.BoolFunction(lambda a, b: a == 2 * b, False)
        con.set_variables(var_list)

        assignments = {'var1': 6, 'var2': 3}
        assert con.satisfied(assignments)

        assignments = {'var1': 4, 'var2': 4}
        assert not con.satisfied(assignments)

        assignments = {'var1': 4}
        assert con.satisfied(assignments)

        def odd(val_dict):
            return all(val % 2 for val in val_dict.values())

        con = cnstr.BoolFunction(odd, True)
        con.set_variables(var_list)

        assignments = {'var1': 3, 'var2': 5}
        assert con.satisfied(assignments)

        assignments = {'var1': 4, 'var2': 3}
        assert not con.satisfied(assignments)

        assignments = {'var1': 4, 'var2': 6}
        assert not con.satisfied(assignments)

        assignments = {'var1': 4}
        assert not con.satisfied(assignments)

        assignments = {'var1': 3}
        assert con.satisfied(assignments)

    def test_fwd_check(self):

        vobjs_list = stubs.make_vars([('var1', [3, 5, 12])])
        fc = cnstr.BoolFunction(lambda a: a == 3, False)
        fc.set_variables(vobjs_list)
        assignments = {'var1': 3}
        assert fc.forward_check(assignments)
        assert vobjs_list[0].get_domain() == [3, 5, 12]

        vobjs_list = stubs.make_vars([('var1', [3, 5, 12]),
                                      ('var2', [3, 6])])
        fc = cnstr.BoolFunction(lambda a, b: 2 * a == b, False)
        fc.set_variables(vobjs_list)
        assignments = {'var1': 3}
        assert fc.forward_check(assignments)
        assert vobjs_list[0].get_domain() == [3, 5, 12]
        assert vobjs_list[1].get_domain() == [6]

        vobjs_list = stubs.make_vars([('var1', [3, 5, 12]),
                                      ('var2', [3, 8])])
        fc = cnstr.BoolFunction(lambda a, b: 2 * a == b, False)
        fc.set_variables(vobjs_list)
        assignments = {'var1': 3}
        assert not fc.forward_check(assignments)
        assert vobjs_list[0].get_domain() == [3, 5, 12]
        assert vobjs_list[1].get_domain() == []

        vobjs_list = stubs.make_vars([('var1', [3, 5, 12]),
                                      ('var2', [3, 8]),
                                      ('var3', [3])])
        fc = cnstr.BoolFunction(lambda a, b, c: 2 * a == b + c, False)
        fc.set_variables(vobjs_list)
        assignments = {'var1': 3}
        assert fc.forward_check(assignments)
        assert vobjs_list[0].get_domain() == [3, 5, 12]
        assert vobjs_list[1].get_domain() == [3, 8]
        assert vobjs_list[2].get_domain() == [3]

        vobjs_list = stubs.make_vars([('var1', [3, 5, 6, 12]),
                                      ('var2', [3, 8]),
                                      ('var3', [3, 4])])
        fc = cnstr.BoolFunction(lambda a, b, c: 2 * a == b + c, False)
        fc.set_variables(vobjs_list)
        assignments = {'var1': 6, 'var2': 8}
        assert fc.forward_check(assignments)
        assert vobjs_list[0].get_domain() == [3, 5, 6, 12]
        assert vobjs_list[1].get_domain() == [3, 8]
        assert vobjs_list[2].get_domain() == [4]

        vobjs_list = stubs.make_vars([('var1', [3, 5, 6, 12]),
                                      ('var2', [3, 8]),
                                      ('var3', [3, 12])])
        fc = cnstr.BoolFunction(
            lambda a, b, c: 2 * a == b + c, False)
        fc.set_variables(vobjs_list)
        assignments = {'var1': 6, 'var2': 8}
        assert not fc.forward_check(assignments)
        assert vobjs_list[0].get_domain() == [3, 5, 6, 12]
        assert vobjs_list[1].get_domain() == [3, 8]
        assert vobjs_list[2].get_domain() == []

        vobjs_list = stubs.make_vars([('var1', [3, 5, 6, 12]),
                                      ('var2', [3, 8]),
                                      ('var3', [3, 12])])
        fc = cnstr.BoolFunction(lambda a, b, c: 2 * a == b + c, False)
        fc.set_variables(vobjs_list)
        fc._params = 4
        assignments = {'var1': 6, 'var2': 8, 'var3': 4}
        with pytest.raises(AttributeError):
            fc.forward_check(assignments)


class TestAllDifferent:
    # no need to test partials, just check the assignments already done

    def test_construct(self):

        adc = cnstr.AllDifferent()
        assert 'AllDifferent' in repr(adc)
        assert isinstance(adc, cnstr.AllDifferent)

    def test_preprocess(self):

        con = cnstr.AllDifferent()
        con.set_variables(stubs.make_vars([('var1', [3])]))
        assert con.preprocess()

        con.set_variables(stubs.make_vars([('var1', [3, 6, 9, 10])]))
        assert not con.preprocess()

        con.set_variables(stubs.make_vars([('var1', [3]),
                                           ('var2', [3])]))
        with pytest.raises(cnstr.PreprocessorConflict):
            con.preprocess()

        con.set_variables(stubs.make_vars([('var1', [3]),
                                           ('var2', [4])]))
        assert con.preprocess()

        con.set_variables(stubs.make_vars([('var1', [3, 6, 9, 10]),
                                           ('var2', [3, 6, 9, 10])]))
        assert not con.preprocess()

    def test_all_diff(self):

        assignments = {'var1': 3}
        assert cnstr.AllEqual().satisfied(assignments)

        assignments = {'var1': 3, 'var2': 6, 'var3': 9, 'var4': 10}
        assert cnstr.AllDifferent().satisfied(assignments)

        assignments = {'var1': 3, 'var2': 6, 'var3': 6, 'var4': 6}
        assert not cnstr.AllDifferent().satisfied(assignments)

        assignments = {'var1': 3, 'var2': 3, 'var3': 6, 'var4': 6}
        assert not cnstr.AllDifferent().satisfied(assignments)

        assignments = {'var1': 6, 'var2': 6, 'var3': 6, 'var4': 6}
        assert not cnstr.AllDifferent().satisfied(assignments)

    def test_fwd_check(self):

        vobjs_list = stubs.make_vars([('var1', [3, 5, 12])])
        fc = cnstr.AllDifferent()
        fc.set_variables(vobjs_list)
        assignments = {'var1': 3}
        assert fc.forward_check(assignments)
        assert vobjs_list[0].get_domain() == [3, 5, 12]

        vobjs_list = stubs.make_vars([('var1', [3, 5, 12]),
                                      ('var2', [3, 6])])
        fc = cnstr.AllDifferent()
        fc.set_variables(vobjs_list)
        assignments = {'var1': 3}
        assert fc.forward_check(assignments)
        assert vobjs_list[0].get_domain() == [3, 5, 12]
        assert vobjs_list[1].get_domain() == [6]

        vobjs_list = stubs.make_vars([('var1', [3, 5, 12]),
                                      ('var2', [3, 6]),
                                      ('var3', [6])])
        fc = cnstr.AllDifferent()
        fc.set_variables(vobjs_list)
        assignments = {'var1': 3, 'var2': 6}
        assert not fc.forward_check(assignments)
        assert vobjs_list[0].get_domain() == [3, 5, 12]
        assert vobjs_list[1].get_domain() == [3, 6]
        assert vobjs_list[2].get_domain() == []


class TestAllEqual:
    # no need to test partials, just check the assignments already done

    def test_construct(self):

        aec = cnstr.AllEqual()
        assert 'AllEqual' in repr(aec)
        assert isinstance(aec, cnstr.AllEqual)

    def test_preprocess(self):

        con = cnstr.AllEqual()

        vobjs_list = stubs.make_vars([('var1', [3])])
        con.set_variables(vobjs_list)
        assert con.preprocess()

        vobjs_list = stubs.make_vars([('var1', [3, 6, 9, 10])])
        con.set_variables(vobjs_list)
        assert not con.preprocess()

        vobjs_list = stubs.make_vars([('var1', [3]),
                                      ('var2', [3])])
        con.set_variables(vobjs_list)
        assert con.preprocess()

        vobjs_list = stubs.make_vars([('var1', [3]),
                                      ('var2', [4])])
        con.set_variables(vobjs_list)
        with pytest.raises(cnstr.PreprocessorConflict):
            con.preprocess()

        vobjs_list = stubs.make_vars([('var1', [3, 6, 9, 10]),
                                      ('var2', [3, 6, 9, 10])])
        con.set_variables(vobjs_list)
        assert not con.preprocess()

    def test_all_equal(self):

        assignments = {'var1': 3}
        assert cnstr.AllEqual().satisfied(assignments)

        assignments = {'var1': 3, 'var2': 6, 'var3': 9, 'var4': 10}
        assert not cnstr.AllEqual().satisfied(assignments)

        assignments = {'var1': 3, 'var2': 6, 'var3': 6, 'var4': 6}
        assert not cnstr.AllEqual().satisfied(assignments)

        assignments = {'var1': 3, 'var2': 3, 'var3': 6, 'var4': 6}
        assert not cnstr.AllEqual().satisfied(assignments)

        assignments = {'var1': 6, 'var2': 6, 'var3': 6, 'var4': 6}
        assert cnstr.AllEqual().satisfied(assignments)

    def test_fwd_check(self):

        vobjs_list = stubs.make_vars([('var1', [3, 5, 12])])
        fc = cnstr.AllEqual()
        fc.set_variables(vobjs_list)
        assignments = {'var1': 3}
        assert fc.forward_check(assignments) == set()
        assert vobjs_list[0].get_domain() == [3, 5, 12]

        vobjs_list = stubs.make_vars([('var1', [3, 5, 12]),
                                      ('var2', [3, 6])])
        fc = cnstr.AllEqual()
        fc.set_variables(vobjs_list)
        assignments = {'var1': 3}
        assert fc.forward_check(assignments) == {'var2'}
        assert vobjs_list[0].get_domain() == [3, 5, 12]
        assert vobjs_list[1].get_domain() == [3]

        vobjs_list = stubs.make_vars([('var1', [3, 5, 12]),
                                      ('var2', [3, 6]),
                                      ('var3', [3, 7])])
        fc = cnstr.AllEqual()
        fc.set_variables(vobjs_list)
        assignments = {'var1': 3}
        assert fc.forward_check(assignments) == {'var2', 'var3'}
        assert vobjs_list[0].get_domain() == [3, 5, 12]
        assert vobjs_list[1].get_domain() == [3]
        assert vobjs_list[2].get_domain() == [3]

        vobjs_list = stubs.make_vars([('var1', [3, 5, 12]),
                                      ('var2', [3]),
                                      ('var3', [5, 6])])
        fc = cnstr.AllEqual()
        fc.set_variables(vobjs_list)
        assignments = {'var1': 3, 'var2': 3}
        assert not fc.forward_check(assignments)
        assert vobjs_list[0].get_domain() == [3, 5, 12]
        assert vobjs_list[1].get_domain() == [3]
        assert vobjs_list[2].get_domain() == []


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


class TestInCnstr:
    # no need to test conditions because preprocessor always fully satisfies

    def test_construct(self):
        ic = cnstr.InValues([2, 3, 8])
        assert 'InValues' in repr(ic)
        assert isinstance(ic, cnstr.InValues)
        assert ic._good_vals == [2, 3, 8]

        with pytest.raises(cnstr.ConstraintError):
            cnstr(cnstr.InValues([]))

    def test_preprocess(self):

        con = cnstr.InValues([2, 5])
        con.set_variables(stubs.make_vars([('var1', [6])]))
        with pytest.raises(cnstr.PreprocessorConflict):
            con.preprocess()

        con = cnstr.InValues([2, 5, 6])
        con.set_variables(stubs.make_vars([('var1', [6])]))
        assert con.preprocess()

        vobjs_list = stubs.make_vars([('var1', [3, 6, 9, 10]),
                                      ('var2', [1, 4, 10, 11])])
        con = cnstr.InValues([3, 6, 10])
        con.set_variables(vobjs_list)
        assert con.preprocess()
        assert sorted(vobjs_list[0].get_domain()) == [3, 6, 10]
        assert sorted(vobjs_list[1].get_domain()) == [10]

    def test_fwd_check(self):
        assert cnstr.InValues([3, 6]).forward_check(None)


class TestNotInCnstr:
    # no need to test conditions because preprocessor always fully satisfies

    def test_construct(self):
        ic = cnstr.NotInValues([2, 3, 8])
        assert 'NotInValue' in repr(ic)
        assert isinstance(ic, cnstr.NotInValues)

        assert ic._bad_vals == [2, 3, 8]

        with pytest.raises(cnstr.ConstraintError):
            cnstr(cnstr.NotInValues([]))

    def test_preprocess(self):

        con = cnstr.NotInValues([2, 5])
        con.set_variables(stubs.make_vars([('var1', [5])]))
        with pytest.raises(cnstr.PreprocessorConflict):
            con.preprocess()

        con = cnstr.NotInValues([2, 5, 6])
        con.set_variables(stubs.make_vars([('var1', [4])]))
        assert con.preprocess()

        vobjs_list = stubs.make_vars([('var1', [3, 6, 9, 10]),
                                      ('var2', [1, 4, 10, 11])])
        con = cnstr.NotInValues([3, 6, 10])
        con.set_variables(vobjs_list)
        assert con.preprocess()
        assert sorted(vobjs_list[0].get_domain()) == [9]
        assert sorted(vobjs_list[1].get_domain()) == [1, 4, 11]

    def test_fwd_check(self):
        assert cnstr.NotInValues([3, 6]).forward_check(None)


class TestAtLeastNInCnstr:

    def test_construct(self):
        aln = cnstr.AtLeastNIn([2, 3, 8])
        assert 'AtLeastNIn' in repr(aln)
        assert isinstance(aln, cnstr.AtLeastNIn)
        assert aln._good_vals == [2, 3, 8]
        assert aln._params == 0
        assert aln._req_nbr == 1
        assert aln._exact == False

        aln = cnstr.AtLeastNIn([2, 3, 8, 9, 10], 2)
        assert aln._good_vals == [2, 3, 8, 9, 10]
        assert aln._params == 0
        assert aln._req_nbr == 2
        assert aln._exact == False

        aln = cnstr.AtLeastNIn([2, 3, 8, 9, 10], 2, True)
        assert aln._good_vals == [2, 3, 8, 9, 10]
        assert aln._params == 0
        assert aln._req_nbr == 2
        assert aln._exact == True

    def test_preprocess(self):

        con = cnstr.AtLeastNIn([2, 3, 8, 9, 10])
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

    @pytest.mark.parametrize(
        'inset, req_nbr, exact, assign, exp',
        [([1, 2, 5, 6], 1, False, {'v1': 1, 'v2': 3}, True),
         ([1, 2, 5, 6], 1, False, {'v1': 0, 'v2': 5}, True),
         ([1, 2, 5, 6], 1, False, {'v1': 2, 'v2': 5}, True),
         ([1, 2, 5, 6], 1, False, {'v1': 0, 'v2': 3}, False),

         ([1, 2, 5, 6], 1, False, {'v1': 1}, True),
         ([1, 2, 5, 6], 1, False, {'v2': 5}, True),
         ([1, 2, 5, 6], 1, False, {'v1': 3}, True),
         ([1, 2, 5, 6], 1, False, {'v2': 0}, True),

         ([1, 2, 5, 6], 1, True, {'v1': 1, 'v2': 3}, True),
         ([1, 2, 5, 6], 1, True, {'v1': 0, 'v2': 5}, True),
         ([1, 2, 5, 6], 1, True, {'v1': 2, 'v2': 5}, False),
         ([1, 2, 5, 6], 1, True, {'v1': 0, 'v2': 3}, False),
         ])
    def test_conditions(self, inset, req_nbr, exact, assign, exp):

        con = cnstr.AtLeastNIn(inset, req_nbr, exact)
        con.set_variables(stubs.make_vars([('v1', range(6)),
                                           ('v2', range(6))]))
        assert con.satisfied(assign) == exp

    @pytest.fixture
    def vobjs_fixt(self):
        return stubs.make_vars([('var1', [3, 7, 12]),
                                ('var2', [1, 6, 9]),
                                ('var3', [5, 6, 10])])

    @pytest.mark.parametrize(
        'assign, exp_ret, exp_domains',
        [
         # const met
         ({'var2': 6, 'var3': 5}, True, [[3, 7, 12], [1, 6, 9], [5, 6, 10]]),

         # unassigned must be good_vals
         ({'var1': 3}, {'var2', 'var3'}, [[3, 7, 12], [1, 6], [5, 6]]),

         # can't meet by numbers
         ({'var1': 3, 'var2': 9}, False, [[3, 7, 12], [1, 6, 9], [5, 6, 10]]),

         # can't meet by domain reduction
         ({'var2': 6, 'var3': 10}, False, [[], [1, 6, 9], [5, 6, 10]]),
         ])
    def test_fwd_check(self, vobjs_fixt, assign, exp_ret, exp_domains):

        con = cnstr.AtLeastNIn([1, 2, 5, 6], 2, False)
        con.set_variables(vobjs_fixt)

        assert con.forward_check(assign) == exp_ret

        assert vobjs_fixt[0].get_domain() == exp_domains[0]
        assert vobjs_fixt[1].get_domain() == exp_domains[1]
        assert vobjs_fixt[2].get_domain() == exp_domains[2]


class TestAtLeastNNotIn:

    def test_construct(self):
        aln = cnstr.AtLeastNNotIn([2, 3, 8])
        assert 'AtLeastNNotIn' in repr(aln)
        assert isinstance(aln, cnstr.AtLeastNNotIn)
        assert aln._bad_vals == [2, 3, 8]
        assert aln._params == 0
        assert aln._req_nbr == 1
        assert aln._exact == False

        aln = cnstr.AtLeastNNotIn([2, 3, 8, 9, 10], 2)
        assert aln._bad_vals == [2, 3, 8, 9, 10]
        assert aln._params == 0
        assert aln._req_nbr == 2
        assert aln._exact == False

        aln = cnstr.AtLeastNNotIn([2, 3, 8, 9, 10], 2, True)
        assert aln._bad_vals == [2, 3, 8, 9, 10]
        assert aln._params == 0
        assert aln._req_nbr == 2
        assert aln._exact == True

    def test_preprocess(self):

        con = cnstr.AtLeastNNotIn([2, 3, 8, 9, 10])
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
        'inset, req_nbr, exact, assign, exp',
        [([1, 2, 5, 6], 1, False, {'v1': 1, 'v2': 3}, True),
         ([1, 2, 5, 6], 1, False, {'v1': 0, 'v2': 5}, True),
         ([1, 2, 5, 6], 1, False, {'v1': 2, 'v2': 5}, False),
         ([1, 2, 5, 6], 1, False, {'v1': 0, 'v2': 3}, True),

         ([1, 2, 5, 6], 1, False, {'v1': 1}, True),
         ([1, 2, 5, 6], 1, False, {'v2': 5}, True),
         ([1, 2, 5, 6], 1, False, {'v1': 3}, True),
         ([1, 2, 5, 6], 1, False, {'v2': 0}, True),

         ([1, 2, 5, 6], 1, True, {'v1': 1, 'v2': 3}, True),
         ([1, 2, 5, 6], 1, True, {'v1': 0, 'v2': 5}, True),
         ([1, 2, 5, 6], 1, True, {'v1': 2, 'v2': 5}, False),
         ([1, 2, 5, 6], 1, True, {'v1': 0, 'v2': 3}, False),

         ])
    def test_conditions(self, inset, req_nbr, exact, assign, exp):

        con = cnstr.AtLeastNNotIn(inset, req_nbr, exact)
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

        con = cnstr.AtLeastNNotIn([1, 2, 5, 6], 2, False)
        con.set_variables(vobjs_fixt)

        assert con.forward_check(assign) == exp_ret

        assert vobjs_fixt[0].get_domain() == exp_domains[0]
        assert vobjs_fixt[1].get_domain() == exp_domains[1]
        assert vobjs_fixt[2].get_domain() == exp_domains[2]


class TestOneOrder:

    def test_construct(self):
        con = cnstr.OneOrder()
        assert 'OneOrder' in repr(con)
        assert isinstance(con, cnstr.OneOrder)

    def test_conditions(self):

        con = cnstr.OneOrder()

        assert con.satisfied({2: 6})
        assert con.satisfied({'z': 1, 'y': 2, 'x': 3})
        assert con.satisfied({'z': 1, 'y': 2, 'x': 2})
        assert not con.satisfied({'z': 3, 'y': 2, 'x': 2})


DOM1 = [0, 3, 5]
DOM2 = [0, 4, 9]

DFWD_A = [-1, 3, 4, 9, 10]
DFWD_B = [0, 4, 9]


class TestLessThan:

    def test_construct(self):

        lt = cnstr.LessThan()

        assert 'LessThan' in repr(lt)
        assert lt._vobjs == None
        assert lt._vnames == None
        assert lt._params == 0

        lt.set_variables(stubs.make_vars([(1, DOM1),
                                          (2, DOM2)]))
        assert lt._params == 2

        with pytest.raises(cnstr.ConstraintError):
            lt.set_variables(stubs.make_vars([(2, DOM2)]))

        with pytest.raises(cnstr.ConstraintError):
            lt.set_variables(stubs.make_vars([(1, DOM1),
                                              (2, DOM2),
                                              (3, DOM2)]))

    def test_preprocess(self):

        lt = cnstr.LessThan()
        lt.set_variables(stubs.make_vars([(1, [0, 1, 2]),
                                          (2, [3, 4, 5])]))
        assert not lt.preprocess()
        assert lt._vobjs[0].get_domain() == [0, 1, 2]
        assert lt._vobjs[1].get_domain() == [3, 4, 5]

        lt = cnstr.LessThan()
        lt.set_variables(stubs.make_vars([(1, [3, 4, 8]),
                                          (2, [1, 2, 4, 5])]))
        assert not lt.preprocess()
        assert lt._vobjs[0].get_domain() == [3, 4]
        assert lt._vobjs[1].get_domain() == [4, 5]

        lt = cnstr.LessThan()
        lt.set_variables(stubs.make_vars([(1, [3, 4, 8]),
                                          (2, [1, 2, 4])]))
        assert lt.preprocess()
        assert lt._vobjs[0].get_domain() == [3]
        assert lt._vobjs[1].get_domain() == [4]

        lt = cnstr.LessThan()
        lt.set_variables(stubs.make_vars([(1, [8]),
                                          (2, [1, 2, 4, 5])]))
        with pytest.raises(cnstr.PreprocessorConflict):
            lt.preprocess()

    def test_conditions(self):

        lt = cnstr.LessThan()
        lt.set_variables(stubs.make_vars([(1, DOM1),
                                          (2, DOM2)]))

        assert lt.satisfied({1 : 0, 2 : 4})
        assert not lt.satisfied({1 : 0, 2 : 0})
        assert not lt.satisfied({1 : 2, 2 : 0})

        assert lt.satisfied({1 : 0})
        assert lt.satisfied({2 : 0})

    @pytest.mark.parametrize(
        'assign, exp_ret, sdoms, edoms',
        [({1 : -1, 2 : 4}, True, [DFWD_A, DFWD_B], [DFWD_A, DFWD_B]),

         ({1 : -1}, True, [DFWD_A, DFWD_B], [DFWD_A, DFWD_B]),
         ({1 : 3}, {2}, [DFWD_A, DFWD_B], [DFWD_A, [4, 9]]),
         ({1 : 4}, {2}, [DFWD_A, DFWD_B], [DFWD_A, [9]]),
         ({1 : 9}, False, [DFWD_A, DFWD_B], [DFWD_A, []]),
         ({1 : 10}, False, [DFWD_A, DFWD_B], [DFWD_A, []]),

         ({2 : -1}, False, [DFWD_B, DFWD_A], [[], DFWD_A]),
         ({2 : 3}, {1}, [DFWD_B, DFWD_A], [[0], DFWD_A]),
         ({2 : 4}, {1}, [DFWD_B, DFWD_A], [[0], DFWD_A]),
         ({2 : 9}, {1}, [DFWD_B, DFWD_A], [[0, 4], DFWD_A]),
         ({2 : 10}, True, [DFWD_B, DFWD_A], [DFWD_B, DFWD_A]),
         ])
    def test_fwd_check(self, assign, exp_ret, sdoms, edoms):

        lt = cnstr.LessThan()
        vobjs = stubs.make_vars([(1, sdoms[0]),
                                 (2, sdoms[1])])
        lt.set_variables(vobjs)

        rval = lt.forward_check(assign)
        print(rval)
        lt.print_domains()
        assert rval == exp_ret

        assert vobjs[0].get_domain() == edoms[0]
        assert vobjs[1].get_domain() == edoms[1]





class TestLessThanEqual:

    def test_construct(self):

        le = cnstr.LessThanEqual()

        assert 'LessThanEqual' in repr(le)
        assert le._vobjs == None
        assert le._vnames == None
        assert le._params == 0

        le.set_variables(stubs.make_vars([(1, DOM1),
                                          (2, DOM2)]))
        assert le._params == 2

        with pytest.raises(cnstr.ConstraintError):
            le.set_variables(stubs.make_vars([(2, DOM2)]))

        with pytest.raises(cnstr.ConstraintError):
            le.set_variables(stubs.make_vars([(1, DOM1),
                                              (2, DOM2),
                                              (3, DOM2)]))

    def test_preprocess(self):

        le = cnstr.LessThanEqual()
        le.set_variables(stubs.make_vars([(1, [0, 1, 2]),
                                          (2, [3, 4, 5])]))
        assert not le.preprocess()
        assert le._vobjs[0].get_domain() == [0, 1, 2]
        assert le._vobjs[1].get_domain() == [3, 4, 5]

        le = cnstr.LessThanEqual()
        le.set_variables(stubs.make_vars([(1, [3, 4, 8]),
                                          (2, [1, 2, 4, 5])]))
        assert not le.preprocess()
        assert le._vobjs[0].get_domain() == [3, 4]
        assert le._vobjs[1].get_domain() == [4, 5]

        le = cnstr.LessThanEqual()
        le.set_variables(stubs.make_vars([(1, [3, 4, 8]),
                                          (2, [1, 2, 4])]))
        assert not le.preprocess()
        assert le._vobjs[0].get_domain() == [3, 4]
        assert le._vobjs[1].get_domain() == [4]

        le = cnstr.LessThanEqual()
        le.set_variables(stubs.make_vars([(1, [8]),
                                          (2, [1, 2, 4, 5])]))
        with pytest.raises(cnstr.PreprocessorConflict):
            le.preprocess()

    def test_conditions(self):

        le = cnstr.LessThanEqual()
        le.set_variables(stubs.make_vars([(1, DOM1),
                                          (2, DOM2)]))

        assert le.satisfied({1 : 0, 2 : 4})
        assert le.satisfied({1 : 0, 2 : 0})
        assert not le.satisfied({1 : 2, 2 : 0})

        assert le.satisfied({1 : 0})
        assert le.satisfied({2 : 0})

    @pytest.mark.parametrize(
        'assign, exp_ret, sdoms, edoms',
        [({1 : -1, 2 : 4}, True, [DFWD_A, DFWD_B], [DFWD_A, DFWD_B]),

         ({1 : -1}, True, [DFWD_A, DFWD_B], [DFWD_A, DFWD_B]),
         ({1 : 3}, {2}, [DFWD_A, DFWD_B], [DFWD_A, [4, 9]]),
         ({1 : 9}, {2}, [DFWD_A, DFWD_B], [DFWD_A, [9]]),
         ({1 : 10}, False, [DFWD_A, DFWD_B], [DFWD_A, []]),

         ({2 : -1}, False, [DFWD_B, DFWD_A], [[], DFWD_A]),
         ({2 : 3}, {1}, [DFWD_B, DFWD_A], [[0], DFWD_A]),
         ({2 : 4}, {1}, [DFWD_B, DFWD_A], [[0, 4], DFWD_A]),
         ({2 : 9}, True, [DFWD_B, DFWD_A], [DFWD_B, DFWD_A]),
         ({2 : 10}, True, [DFWD_B, DFWD_A], [DFWD_B, DFWD_A]),
         ])
    def test_fwd_check(self, assign, exp_ret, sdoms, edoms):

        le = cnstr.LessThanEqual()
        vobjs = stubs.make_vars([(1, sdoms[0]),
                                 (2, sdoms[1])])
        le.set_variables(vobjs)

        rval = le.forward_check(assign)
        print(rval)
        le.print_domains()
        assert rval == exp_ret

        assert vobjs[0].get_domain() == edoms[0]
        assert vobjs[1].get_domain() == edoms[1]
