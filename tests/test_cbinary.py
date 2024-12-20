# -*- coding: utf-8 -*-
"""Created on Tue Jun 20 05:52:53 2023

@author: Ann
"""



# %% imports

import pytest
pytestmark = pytest.mark.unittest

from csp_solver import constraint as cnstr

import stubs

# %% constants

DOM1 = [0, 3, 5]
DOM2 = [0, 4, 9]


# %% tests

class TestNand:

    def test_construct(self):

        nand = cnstr.Nand(3, 4)

        assert 'Nand' in repr(nand)
        assert nand._val1 == 3
        assert nand._val2 == 4
        assert nand._vobjs == None
        assert nand._vnames == None
        assert nand._params == 0

        nand.set_variables(stubs.make_vars([(1, DOM1),
                                            (2, DOM2)]))
        assert nand._params == 2

        with pytest.raises(cnstr.ConstraintError):
            nand.set_variables(stubs.make_vars([(1, [0, 5]),
                                                (2, DOM2)]))

        with pytest.raises(cnstr.ConstraintError):
            nand.set_variables(stubs.make_vars([(1, DOM1),
                                                (2, [0, 9])]))

    def test_conditions(self):

        nand = cnstr.Nand(3, 4)
        nand.set_variables(stubs.make_vars([(1, DOM1),
                                            (2, DOM2)]))

        assert nand.satisfied({1 : 0, 2 : 0})
        assert nand.satisfied({1 : 0, 2 : 4})
        assert nand.satisfied({1 : 3, 2 : 0})
        assert not nand.satisfied({1 : 3, 2 : 4})

        assert nand.satisfied({2 : 0})
        assert nand.satisfied({2 : 4})
        assert nand.satisfied({1 : 3})

    @pytest.mark.parametrize(
        'assign, exp_ret, new_doms, exp_doms',
        [({1 : 0, 2 : 0}, True, None, [DOM1, DOM2]),
         ({2 : 4}, True, [[0, 5], DOM2], [[0, 5], DOM2]),
         ({1 : 3}, True, [DOM1, [0, 9]], [DOM1, [0, 9]]),

         ({1 : 0}, True, None, [DOM1, DOM2]),
         ({1 : 3}, {2}, None, [DOM1, [0, 9]]),

         ({2 : 0}, True, None, [DOM1, DOM2]),
         ({2 : 4}, {1}, None, [[0, 5], DOM2]),

         ({1 : 3}, False, [DOM1, [4]], [DOM1, []]),
         ({2 : 4}, False, [[3], DOM2], [[], DOM2]),
         ])
    def test_fwd_check(self, assign, exp_ret, new_doms, exp_doms):

        nand = cnstr.Nand(3, 4)
        vobjs = stubs.make_vars([(1, DOM1),
                                 (2, DOM2)])
        nand.set_variables(vobjs)

        if new_doms:
            vobjs[0].set_domain(new_doms[0])
            vobjs[1].set_domain(new_doms[1])

        assert nand.forward_check(assign) == exp_ret

        assert vobjs[0].get_domain() == exp_doms[0]
        assert vobjs[1].get_domain() == exp_doms[1]


class TestOr:

    def test_construct(self):

        orc = cnstr.Or(3, 4)

        assert 'Or' in repr(orc)
        assert orc._val1 == 3
        assert orc._val2 == 4
        assert orc._vobjs == None
        assert orc._vnames == None
        assert orc._params == 0

    def test_conditions(self):

        orc = cnstr.Or(3, 4)
        orc.set_variables(stubs.make_vars([(1, DOM1),
                                           (2, DOM2)]))

        assert orc._params == 2

        assert not orc.satisfied({1 : 0, 2 : 0})
        assert orc.satisfied({1 : 0, 2 : 4})
        assert orc.satisfied({1 : 3, 2 : 0})
        assert orc.satisfied({1 : 3, 2 : 4})

        assert orc.satisfied({2 : 0})
        assert orc.satisfied({2 : 4})
        assert orc.satisfied({1 : 3})

    @pytest.mark.parametrize(
        'assign, exp_ret, new_doms, exp_doms',
        [({1 : 0, 2 : 0}, True, None, [DOM1, DOM2]),

         ({1 : 0}, {2}, None, [DOM1, [4]]),
         ({1 : 3}, True, None, [DOM1, DOM2]),

         ({2 : 0}, {1}, None, [[3], DOM2]),
         ({2 : 4}, True, None, [DOM1, DOM2]),

         ({1 : 0}, False, [DOM1, [1, 9]], [DOM1, []]),
         ({2 : 0}, False, [[1, 5], DOM2], [[], DOM2]),
         ])
    def test_fwd_check(self, assign, exp_ret, new_doms, exp_doms):

        ocr = cnstr.Or(3, 4)
        vobjs = stubs.make_vars([(1, DOM1),
                                 (2, DOM2)])
        ocr.set_variables(vobjs)

        if new_doms:
            vobjs[0].set_domain(new_doms[0])
            vobjs[1].set_domain(new_doms[1])

        assert ocr.forward_check(assign) == exp_ret

        assert vobjs[0].get_domain() == exp_doms[0]
        assert vobjs[1].get_domain() == exp_doms[1]


class TestIfThen:

    def test_construct(self):

        ifthen = cnstr.IfThen(3, 4)

        assert 'IfThen' in repr(ifthen)
        assert ifthen._val1 == 3
        assert ifthen._val2 == 4
        assert ifthen._vobjs == None
        assert ifthen._vnames == None
        assert ifthen._params == 0

    def test_conditions(self):

        ifthen = cnstr.IfThen(3, 4)
        ifthen.set_variables(stubs.make_vars([(1, DOM1),
                                              (2, DOM2)]))

        assert ifthen._params == 2

        assert ifthen.satisfied({1 : 0, 2 : 0})
        assert ifthen.satisfied({1 : 0, 2 : 4})
        assert not ifthen.satisfied({1 : 3, 2 : 0})
        assert ifthen.satisfied({1 : 3, 2 : 4})

        assert ifthen.satisfied({2 : 0})
        assert ifthen.satisfied({2 : 4})
        assert ifthen.satisfied({1 : 3})

    @pytest.mark.parametrize(
        'assign, exp_ret, new_doms, exp_doms',
        [({1 : 0, 2 : 0}, True, None, [DOM1, DOM2]),

         ({1 : 0}, True, None, [DOM1, DOM2]),
         ({1 : 3}, {2}, None, [DOM1, [4]]),

         ({2 : 0}, True, None, [DOM1, DOM2]),
         ({2 : 4}, True, None, [DOM1, DOM2]),

         ({1 : 3}, False, [DOM1, [1, 9]], [DOM1, []]),
         ])
    def test_fwd_check(self, assign, exp_ret, new_doms, exp_doms):

        ifthen = cnstr.IfThen(3, 4)
        vobjs = stubs.make_vars([(1, DOM1),
                                 (2, DOM2)])
        ifthen.set_variables(vobjs)

        if new_doms:
            vobjs[0].set_domain(new_doms[0])
            vobjs[1].set_domain(new_doms[1])

        assert ifthen.forward_check(assign) == exp_ret

        assert vobjs[0].get_domain() == exp_doms[0]
        assert vobjs[1].get_domain() == exp_doms[1]


class TestXor:

    def test_construct(self):

        xor = cnstr.Xor(3, 4)

        assert 'Xor' in repr(xor)
        assert xor._val1 == 3
        assert xor._val2 == 4
        assert xor._vobjs == None
        assert xor._vnames == None
        assert xor._params == 0

    def test_conditions(self):

        xor = cnstr.Xor(3, 4)
        xor.set_variables(stubs.make_vars([(1, DOM1),
                                           (2, DOM2)]))

        assert xor._params == 2

        assert not xor.satisfied({1 : 0, 2 : 0})
        assert xor.satisfied({1 : 0, 2 : 4})
        assert xor.satisfied({1 : 3, 2 : 0})
        assert not xor.satisfied({1 : 3, 2 : 4})

        assert xor.satisfied({2 : 0})
        assert xor.satisfied({2 : 4})
        assert xor.satisfied({1 : 3})

    @pytest.mark.parametrize(
        'assign, exp_ret, new_doms, exp_doms',
        [({1 : 0, 2 : 0}, True, None, [DOM1, DOM2]),
         ({2 : 4}, True, [[0, 5], DOM2], [[0, 5], DOM2]),
         ({1 : 3}, True, [DOM1, [0, 9]], [DOM1, [0, 9]]),

         ({1 : 0}, {2}, None, [DOM1, [4]]),
         ({1 : 3}, {2}, None, [DOM1, [0, 9]]),

         ({2 : 0}, {1}, None, [[3], DOM2]),
         ({2 : 4}, {1}, None, [[0, 5], DOM2]),

         ({1 : 0}, False, [DOM1, [1, 9]], [DOM1, []]),
         ({1 : 3}, False, [DOM1, [4]], [DOM1, []]),
         ({2 : 0}, False, [[1, 5], DOM2], [[], DOM2]),
         ({2 : 4}, False, [[3], DOM2], [[], DOM2]),
         ])
    def test_fwd_check(self, assign, exp_ret, new_doms, exp_doms):

        xor = cnstr.Xor(3, 4)
        vobjs = stubs.make_vars([(1, DOM1),
                                 (2, DOM2)])
        xor.set_variables(vobjs)

        if new_doms:
            vobjs[0].set_domain(new_doms[0])
            vobjs[1].set_domain(new_doms[1])

        assert xor.forward_check(assign) == exp_ret

        assert vobjs[0].get_domain() == exp_doms[0]
        assert vobjs[1].get_domain() == exp_doms[1]


class TestNxor:

    def test_construct(self):

        nxor = cnstr.Nxor(3, 4)

        assert 'Nxor' in repr(nxor)
        assert nxor._val1 == 3
        assert nxor._val2 == 4
        assert nxor._vobjs == None
        assert nxor._vnames == None
        assert nxor._params == 0

    def test_conditions(self):

        nxor = cnstr.Nxor(3, 4)
        nxor.set_variables(stubs.make_vars([(1, DOM1),
                                            (2, DOM2)]))

        assert nxor._params == 2

        assert nxor.satisfied({1 : 0, 2 : 0})
        assert not nxor.satisfied({1 : 0, 2 : 4})
        assert not nxor.satisfied({1 : 3, 2 : 0})
        assert nxor.satisfied({1 : 3, 2 : 4})

        assert nxor.satisfied({2 : 0})
        assert nxor.satisfied({2 : 4})
        assert nxor.satisfied({1 : 3})

    @pytest.mark.parametrize(
        'assign, exp_ret, new_doms, exp_doms',
        [({1 : 0, 2 : 0}, True, None, [DOM1, DOM2]),
         ({2 : 0}, True, [[0, 5], DOM2], [[0, 5], DOM2]),
         ({1 : 0}, True, [DOM1, [0, 9]], [DOM1, [0, 9]]),

         ({1 : 3}, {2}, None, [DOM1, [4]]),
         ({1 : 0}, {2}, None, [DOM1, [0, 9]]),

         ({2 : 4}, {1}, None, [[3], DOM2]),
         ({2 : 0}, {1}, None, [[0, 5], DOM2]),

         ({1 : 3}, False, [DOM1, [1, 9]], [DOM1, []]),
         ({1 : 0}, False, [DOM1, [4]], [DOM1, []]),
         ({2 : 4}, False, [[1, 5], DOM2], [[], DOM2]),
         ({2 : 0}, False, [[3], DOM2], [[], DOM2]),
         ])
    def test_fwd_check(self, assign, exp_ret, new_doms, exp_doms):

        nxor = cnstr.Nxor(3, 4)
        vobjs = stubs.make_vars([(1, DOM1),
                                 (2, DOM2)])
        nxor.set_variables(vobjs)

        if new_doms:
            vobjs[0].set_domain(new_doms[0])
            vobjs[1].set_domain(new_doms[1])

        assert nxor.forward_check(assign) == exp_ret

        assert vobjs[0].get_domain() == exp_doms[0]
        assert vobjs[1].get_domain() == exp_doms[1]
