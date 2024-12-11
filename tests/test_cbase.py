# -*- coding: utf-8 -*-
"""
Created on Fri Jun 23 06:00:37 2023

@author: Ann
"""

import pytest

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
        assert cnstr.AtLeastNIn.NAT_NBR_DOMAIN == False
        assert cnstr.AtLeastNNotIn.NAT_NBR_DOMAIN == False

        assert cnstr.OneOrder.NAT_NBR_DOMAIN == False
        assert cnstr.BoolBinOpConstraint.NAT_NBR_DOMAIN == False

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
        assert cnstr.AtLeastNIn.ARC_CONSIST_CHECK_OK == ArcConCheck.ALWAYS
        assert cnstr.AtLeastNNotIn.ARC_CONSIST_CHECK_OK == \
            ArcConCheck.CHECK_INST

        assert cnstr.OneOrder.ARC_CONSIST_CHECK_OK == ArcConCheck.CHECK_INST

        assert cnstr.LessThan.ARC_CONSIST_CHECK_OK == ArcConCheck.ALWAYS
        assert cnstr.LessThanEqual.ARC_CONSIST_CHECK_OK == ArcConCheck.ALWAYS

        assert cnstr.BoolBinOpConstraint.ARC_CONSIST_CHECK_OK == \
            ArcConCheck.ALWAYS

        # Fail if new constraints need to be added to this test
        assert len(cnstr.Constraint.__subclasses__()) == 14

        assert cnstr.Nand.ARC_CONSIST_CHECK_OK == ArcConCheck.ALWAYS
        assert cnstr.Or.ARC_CONSIST_CHECK_OK == ArcConCheck.ALWAYS
        assert cnstr.IfThen.ARC_CONSIST_CHECK_OK == ArcConCheck.ALWAYS
        assert cnstr.Xor.ARC_CONSIST_CHECK_OK == ArcConCheck.ALWAYS
        assert cnstr.Nxor.ARC_CONSIST_CHECK_OK == ArcConCheck.ALWAYS

        # Fail if new constraints need to be added to this test
        assert len(cnstr.BoolBinOpConstraint.__subclasses__()) == 5


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
