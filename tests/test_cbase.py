# -*- coding: utf-8 -*-
"""Test the base constraint classes.

Created on Fri Jun 23 06:00:37 2023
@author: Ann"""

import pytest
pytestmark = pytest.mark.unittest

from csp_solver import constraint as cnstr
from csp_solver.constraint import ArcConCheck

import stubs


class TestGeneral:

    def test_nats(self):

        assert cnstr.Constraint.NAT_NBR_DOMAIN == False
        assert cnstr.BoolFunction.NAT_NBR_DOMAIN == False
        assert cnstr.AllDifferent.NAT_NBR_DOMAIN == False
        assert cnstr.AllEqual.NAT_NBR_DOMAIN == False

        assert cnstr.MaxSum.NAT_NBR_DOMAIN == True
        assert cnstr.ExactSum.NAT_NBR_DOMAIN == True
        assert cnstr.MinSum.NAT_NBR_DOMAIN == True

        assert cnstr.InValues.NAT_NBR_DOMAIN == False
        assert cnstr.NotInValues.NAT_NBR_DOMAIN == False

        assert cnstr.OneOrder.NAT_NBR_DOMAIN == False
        assert cnstr.BoolBinOpConstraint.NAT_NBR_DOMAIN == False
        assert cnstr.UniqueSolutionsIF.NAT_NBR_DOMAIN == False

        # Fail if new constraints need to be added to this test
        assert len(cnstr.Constraint.__subclasses__()) == 14

        assert cnstr.Nand.NAT_NBR_DOMAIN == False
        assert cnstr.Or.NAT_NBR_DOMAIN == False
        assert cnstr.IfThen.NAT_NBR_DOMAIN == False
        assert cnstr.Xor.NAT_NBR_DOMAIN == False
        assert cnstr.Nxor.NAT_NBR_DOMAIN == False

        assert cnstr.LessThan.NAT_NBR_DOMAIN == False
        assert cnstr.LessThanEqual.NAT_NBR_DOMAIN == False

        # Fail if new constraints need to be added to this test
        assert len(cnstr.BoolBinOpConstraint.__subclasses__()) == 5

        assert cnstr.ExactlyNIn.NAT_NBR_DOMAIN == False
        assert cnstr.AtLeastNIn.NAT_NBR_DOMAIN == False
        assert cnstr.AtMostNIn.NAT_NBR_DOMAIN == False
        assert cnstr.AtLeastNNotIn.NAT_NBR_DOMAIN == False

        # Fail if new constraints need to be added to this test
        assert len(cnstr.SetConstraint.__subclasses__()) == 4


    def test_arc_checks(self):

        assert cnstr.Constraint.ARC_CONSIST_CHECK_OK == ArcConCheck.ALWAYS
        assert cnstr.BoolFunction.ARC_CONSIST_CHECK_OK == \
            ArcConCheck.CHECK_INST
        assert cnstr.AllDifferent.ARC_CONSIST_CHECK_OK == ArcConCheck.ALWAYS
        assert cnstr.AllEqual.ARC_CONSIST_CHECK_OK == ArcConCheck.ALWAYS

        assert cnstr.MaxSum.ARC_CONSIST_CHECK_OK == ArcConCheck.ALWAYS
        assert cnstr.ExactSum.ARC_CONSIST_CHECK_OK == ArcConCheck.ALWAYS
        assert cnstr.MinSum.ARC_CONSIST_CHECK_OK == ArcConCheck.CHECK_INST

        assert cnstr.InValues.ARC_CONSIST_CHECK_OK == ArcConCheck.ALWAYS
        assert cnstr.NotInValues.ARC_CONSIST_CHECK_OK == ArcConCheck.ALWAYS

        assert cnstr.OneOrder.ARC_CONSIST_CHECK_OK == ArcConCheck.CHECK_INST

        assert cnstr.LessThan.ARC_CONSIST_CHECK_OK == ArcConCheck.ALWAYS
        assert cnstr.LessThanEqual.ARC_CONSIST_CHECK_OK == ArcConCheck.ALWAYS

        assert cnstr.BoolBinOpConstraint.ARC_CONSIST_CHECK_OK == \
            ArcConCheck.ALWAYS
        assert cnstr.SetConstraint.ARC_CONSIST_CHECK_OK == \
            ArcConCheck.CHECK_INST

        assert cnstr.UniqueSolutionsIF.ARC_CONSIST_CHECK_OK == \
            ArcConCheck.NEVER

        # Fail if new constraints need to be added to this test
        assert len(cnstr.Constraint.__subclasses__()) == 14

        assert cnstr.Nand.ARC_CONSIST_CHECK_OK == ArcConCheck.ALWAYS
        assert cnstr.Or.ARC_CONSIST_CHECK_OK == ArcConCheck.ALWAYS
        assert cnstr.IfThen.ARC_CONSIST_CHECK_OK == ArcConCheck.ALWAYS
        assert cnstr.Xor.ARC_CONSIST_CHECK_OK == ArcConCheck.ALWAYS
        assert cnstr.Nxor.ARC_CONSIST_CHECK_OK == ArcConCheck.ALWAYS

        # Fail if new constraints need to be added to this test
        assert len(cnstr.BoolBinOpConstraint.__subclasses__()) == 5

        assert cnstr.ExactlyNIn.ARC_CONSIST_CHECK_OK == ArcConCheck.CHECK_INST
        assert cnstr.AtLeastNIn.ARC_CONSIST_CHECK_OK == ArcConCheck.CHECK_INST
        assert cnstr.AtMostNIn.ARC_CONSIST_CHECK_OK == ArcConCheck.CHECK_INST
        assert cnstr.AtLeastNNotIn.ARC_CONSIST_CHECK_OK == \
            ArcConCheck.CHECK_INST

        # Fail if new constraints need to be added to this test
        assert len(cnstr.SetConstraint.__subclasses__()) == 4


    def test_arc_ok(self):
        """Test the two default arc_con_ok"""

        assert not cnstr.ConstraintIF.arc_con_ok(object())

        with pytest.raises(AttributeError):
            cnstr.Constraint.arc_con_ok(object())

        class con(cnstr.Constraint):
            def satisfied(self):
                return False

        assert not con().arc_con_ok()


    def test_variables(self):

        vobjs_list = stubs.make_vars([('var1', [3, 6, 9, 10]),
                                      ('var2', [1, 4, 10, 11])])

        con = cnstr.MinSum(5)
        con.set_variables(vobjs_list)

        assert con._params == 2
        assert con._vobjs == vobjs_list
        assert con._vnames == ['var1', 'var2']

        assert con.get_variables() == vobjs_list
        assert con.get_vnames() == ['var1', 'var2']

        vobjs_list = stubs.make_vars([('var1', [3, 6, 9, 10]),
                                      ('var1', [1, 4, 10, 11])])
        with pytest.raises(cnstr.ConstraintError):
            con.set_variables(vobjs_list)



class TestBaseOps:

    @pytest.fixture
    def const(self, request):
        """Request.param is a list of varaible name, domain
        pairs"""

        class AllOdd(cnstr.Constraint):

            def satisfied(self, assignments):
                """True if all assignments are odd"""
                return all(val % 2 for val in assignments.values())

        con = AllOdd()
        con.set_variables(stubs.make_vars(request.param))
        return con


    FIVES = (0, 1, 2, 3, 4)
    VLISTS = [
                ([('v1', FIVES)], True, {'v1': [1, 3]}),

                ([('v1', FIVES), ('v2', FIVES)], False, {'v1': [1, 3],
                                                         'v2': [1, 3]}),

                ([('v1', FIVES), ('v2', FIVES), ('v3', FIVES)],
                 False, {'v1': list(FIVES),
                         'v2': list(FIVES),
                         'v3': list(FIVES)}),
                ([('v1', [1]), ('v2', [3]), ('v3', [5])],
                 True,  {'v1': [1], 'v2': [3], 'v3': [5]}),
            ]


    @pytest.mark.parametrize('const, esats, edoms',
                             VLISTS, indirect=['const'])
    def test_no_conflicts(self, const, esats, edoms):

        assert const.preprocess() == esats

        for vobj in const.get_variables():
            assert vobj.get_domain() == edoms[vobj.name]


    OLISTS = [
                [('v1', (2, 4))],
                [('v1', (2, 4)), ('v2', (2, 4))],
                [('v1', (2, 4)), ('v2', (2, 4)), ('v3', [])],
                [('v1', [1]), ('v2', [2]), ('v3', [4])],

            ]

    @pytest.mark.parametrize('const',
                             OLISTS, indirect=['const'])
    def test_conflicts(self, const):

        with pytest.raises(cnstr.PreprocessorConflict):
            const.preprocess()


    @pytest.mark.parametrize('const',
                             [VLISTS[1][0]], indirect=['const'])
    def test_forward(self, const):

        assert const.forward_check(None)


    @pytest.mark.parametrize('const',
                             [VLISTS[1][0]], indirect=['const'])
    def test_pdomain(self, const, capsys):

        const.print_domains()
        data = capsys.readouterr().out
        assert 'v1' in data
        assert 'v2' in data
