# -*- coding: utf-8 -*-
"""Test the arc consistency checker with both the
recursive backtracking solver and the
non-recursive backtracking solver.

Created on Thu Jun 22 05:30:19 2023
@author: Ann"""


# %% imports

import pytest
pytestmark = pytest.mark.unittest

import csp_solver as csp
from csp_solver import arc_consist
from csp_solver.arc_consist import ArcStat
from csp_solver import constraint as cnstr
from csp_solver import list_constraint as lcnstr
from csp_solver import solver


# %%


GOOD_ARCCON = arc_consist.ArcConIF.derived()

class BadArcCon(arc_consist.ArcConIF):
    pass

class TestArcCon:

    @pytest.mark.parametrize('arccon', GOOD_ARCCON)
    def test_good_interfaces(self, arccon):
        """build each to confirm that it defines the required interface"""
        assert arccon()


    def test_no_interfaces(self):
        """confirm error is reported"""
        with pytest.raises(TypeError):
            assert BadArcCon()


    def test_set_arc_con(self):
        """Test valid indirectly through the solver interface."""
        slvr = solver.Backtracking()
        assert slvr._arc_con == None

        slvr.arc_con = arc_consist.ArcCon3()
        assert isinstance(slvr._arc_con, arc_consist.ArcCon3)

        slvr.arc_con = None
        assert slvr._arc_con == None

        with pytest.raises(ValueError):
            slvr.arc_con = 5

        with pytest.raises(ValueError):
            slvr.arc_con = object()

        # odd tests but we can instantiate ArcConIF
        with pytest.raises(ValueError):
            arc_consist.ArcConIF.set_pspec(object(), None)

        with pytest.raises(AttributeError):
            arc_consist.ArcConIF.set_pspec(object(),
                                           csp.ProblemSpec())

    def test_const(self):

        ac = arc_consist.ArcCon3()
        assert ac._spec == None
        assert ac._all_arcs == None

        pspec = csp.ProblemSpec()
        ac.set_pspec(pspec)
        assert ac._spec is pspec

        with pytest.raises(ValueError):
            ac.set_pspec(5)

        with pytest.raises(ValueError):
            ac.set_pspec(object())



class TestArcCon3Boris:
    """This does detailed testing of the arc consistency
    methods with both solvers."""

    @pytest.fixture(params=[solver.Backtracking,
                            solver.NonRecBacktracking])
    def prob_fixt(self, request):
        """Variables A - E are reduced to one value each
        by arc consistency.

        example from:
            https://www.boristhebrave.com/2021/08/30/arc-consistency-explained/
        """

        prob = csp.Problem(my_solver=request.param())

        prob.arc_con = arc_consist.ArcCon3()

        # define variables in order, so arc tuples can be anticipated
        prob.add_variable('A', [1, 2, 3, 4])
        prob.add_variable('B', [1, 2, 4])
        prob.add_variable('C', [1, 3, 4])
        prob.add_variables('DE', [1, 2, 3, 4])
        prob.add_variable('F', [1, 2, 3, 4])

        prob.add_constraint(cnstr.AllDifferent(), 'AB')
        prob.add_constraint(cnstr.AllEqual(), 'AD')
        prob.add_constraint(cnstr.LessThan(), 'EA')

        prob.add_constraint(cnstr.AllDifferent(), 'BD')
        prob.add_constraint(cnstr.AllDifferent(), 'BC')
        prob.add_constraint(cnstr.LessThan(), 'EB')

        prob.add_constraint(cnstr.LessThan(), 'CD')
        prob.add_constraint(cnstr.LessThan(), 'EC')

        prob.add_constraint(cnstr.LessThan(), 'ED')

        prob.add_constraint(cnstr.MinSum(10), 'ABC')
        prob.add_constraint(cnstr.MinSum(5), 'BC')

        prob.add_list_constraint(lcnstr.OrCList(),
                                 [(cnstr.IfThen(2, 3), 'AF'),
                                  (cnstr.Nand(1, 3), 'BF')])


        # the stuff below is normally done in solver.get_solution
        # don't call prob._spec.prepare_variables() to keep from preprocessing

        for constraint in prob._spec.constraints[:]:
            for vname in constraint.get_vnames():
                prob._spec.cnstr_dict[vname] += [constraint]

        prob._solver.arc_con.set_pspec(prob._spec)

        return prob


    def test_get_arcs(self, prob_fixt):

        arccon = prob_fixt._solver.arc_con
        assert isinstance(arccon, arc_consist.ArcCon3)

        arcs = arccon._get_arcs()

        expect = {'AB' : [cnstr.AllDifferent],
                  'AD' : [cnstr.AllEqual],
                  'AE' : [cnstr.LessThan],
                  'BC' : [cnstr.AllDifferent, cnstr.MinSum],
                  'BD' : [cnstr.AllDifferent],
                  'BE' : [cnstr.LessThan],
                  'CD' : [cnstr.LessThan],
                  'CE' : [cnstr.LessThan],
                  'DE' : [cnstr.LessThan]}

        for vpair, clist in expect.items():

            assert (vpair[0], vpair[1]) in arcs
            acons = arcs[(vpair[0], vpair[1])]

            assert len(acons) == len(clist)
            enames = sorted(con.__name__ for con in clist)
            anames = sorted(con.__class__.__name__ for con in acons)

            assert enames == anames


    @pytest.mark.parametrize('vname1, val1, vname2, expected',
                             [('A', 2, 'D', True),  # params in order
                              ('B', 4, 'E', True),  # params reversed, one val not ok
                              ('B', 1, 'E', False),
                              ])
    def test_any_sats(self, prob_fixt, vname1, val1, vname2, expected):

        arccon = prob_fixt._solver.arc_con
        arcs = arccon._get_arcs()

        cons = arcs[(vname1, vname2)]
        dom = arccon._spec.variables[vname2].get_domain()
        rval = arccon._any_value_sats(cons, vname1, val1, vname2, dom)
        assert rval == expected


    def test_any_sats_two(self, prob_fixt):
        """Force the outer for loop to not execute."""

        arccon = prob_fixt._solver.arc_con
        arcs = arccon._get_arcs()

        cons = arcs[('C', 'E')]
        assert arccon._any_value_sats(cons, 'C', 3, 'E', []) == False


    @pytest.mark.parametrize('vname1, vname2, ex_ret, ex_dom1',
                             [('A', 'D',ArcStat.NONE, None),
                              ('B', 'E', ArcStat.CHANGED, [2, 4]),
                              ])
    def test_arc_reduce(self, prob_fixt, vname1, vname2, ex_ret, ex_dom1):

        arccon = prob_fixt._solver.arc_con
        arcs = arccon._get_arcs()

        dom1 = arccon._spec.variables[vname1].get_domain_copy()
        dom2 = arccon._spec.variables[vname2].get_domain_copy()

        cons = arcs[(vname1, vname2)]
        rval = arccon._arc_reduce(cons, vname1, vname2)

        assert rval == ex_ret

        if ex_dom1:
            assert arccon._spec.variables[vname1].get_domain() == ex_dom1
        else:
            assert arccon._spec.variables[vname1].get_domain() == dom1
        assert arccon._spec.variables[vname2].get_domain() == dom2


    def test_arc_reduce_two(self, prob_fixt):
        """Force the overconstrained."""

        arccon = prob_fixt._solver.arc_con
        arcs = arccon._get_arcs()

        arccon._spec.variables['B'].set_domain([1])

        cons = arcs[('B', 'E')]
        rval = arccon._arc_reduce(cons, 'B', 'E')

        assert rval == ArcStat.OVERCON


    def test_arc_consist(self, prob_fixt):

        assert prob_fixt._solver._arc_con.arc_consist([])

        for vname in 'ABCDE':

            vobj = prob_fixt._spec.variables[vname]
            assert vobj.nbr_values() == 1


    def test_ac_over(self, prob_fixt):

        prob_fixt._solver._arc_con._spec.variables['B'].set_domain([1])

        assert not prob_fixt._solver._arc_con.arc_consist([])




PETER = 'Peter'
PAUL = 'Paul'
JANE = 'Jane'

PEOPLE = (PETER, PAUL, JANE)

SAX = 'sax'
GUITAR = 'guitar'
DRUMS = 'drums'

F13 = '13'
CATS = 'cats'
HEIGHTS = 'heights'


class TestARcCon3Forbus:
    """This is build 3 from the forbus example:
    from _Artificial Intelligence_, problem 3-9, Winston, p444"""

    @pytest.fixture(params=[solver.Backtracking,
                            solver.NonRecBacktracking])
    def prob_fixt(self, request):

        forbus = csp.Problem(my_solver=request.param())

        forbus.arc_con = arc_consist.ArcCon3()

        for name in (PETER, PAUL, JANE):
            forbus.add_variable(f'{name}_plays', (SAX, GUITAR, DRUMS))
            forbus.add_variable(f'{name}_fears', (F13, CATS, HEIGHTS))

        forbus.add_constraint(cnstr.AllDifferent(),
                              [f'{name}_plays' for name in PEOPLE])
        forbus.add_constraint(cnstr.AllDifferent(),
                              [f'{name}_fears' for name in PEOPLE])

        forbus.add_constraint(cnstr.NotInValues([GUITAR]), [PETER + '_plays'])
        forbus.add_constraint(cnstr.NotInValues([HEIGHTS]), [PETER + '_fears'])

        forbus.add_constraint(cnstr.NotInValues([CATS]), [PAUL + '_fears'])
        forbus.add_constraint(cnstr.NotInValues([SAX]), [PAUL + '_plays'])

        for name in PEOPLE:

            forbus.add_constraint(cnstr.Nand(GUITAR, HEIGHTS),
                                  [f'{name}_plays', f'{name}_fears'])

            forbus.add_constraint(cnstr.Nand(SAX, CATS),
                                  [f'{name}_plays', f'{name}_fears'])

            forbus.add_constraint(cnstr.Nand(DRUMS, F13),
                                  [f'{name}_plays', f'{name}_fears'])

            forbus.add_constraint(cnstr.Nand(DRUMS, HEIGHTS),
                                  [f'{name}_plays', f'{name}_fears'])

        return forbus


    def test_ppj_steps(self, prob_fixt):
        """Do a few special steps to test the arc_consist proc.
        This confirms that the arc consistency will do useful work
        in the whole problem solution (test_ppj_solves)."""

        prob_fixt._spec.prepare_variables()

        # confirm preprocessor didn't solve the problem
        assert not all(var.nbr_values() == 1
                       for var in prob_fixt._spec.variables.values())

        # none of the variables are reduced to one value
        # print('Before:')
        for vname, vobj in prob_fixt._spec.variables.items():
            # print(vname, vobj.get_domain())
            assert vobj.nbr_values() > 1

        # force start down the right track (this is part of the answer)
        assigns = {'Peter_plays': DRUMS}

        # confirm that the arc_consist doesn't over constrain
        assert prob_fixt.arc_con.arc_consist(assigns)

        # print('AFTER:')
        # for vname, vobj in prob_fixt._spec.variables.items():
        #     print(vname, vobj.get_domain())

        # one pass of ArcCon3 almost solves the problem:
        assert prob_fixt._spec.variables['Peter_plays'].nbr_values() == 2
        assert prob_fixt._spec.variables['Paul_plays'].nbr_values() == 1
        assert prob_fixt._spec.variables['Jane_plays'].nbr_values() == 1
        assert prob_fixt._spec.variables['Peter_fears'].nbr_values() == 1
        assert prob_fixt._spec.variables['Paul_fears'].nbr_values() == 1
        assert prob_fixt._spec.variables['Jane_fears'].nbr_values() == 1


    def test_ppj_solves(self, prob_fixt):

        solution = {'Peter_plays': 'drums', 'Peter_fears': 'cats',
                    'Paul_plays': 'guitar', 'Paul_fears': '13',
                    'Jane_plays': 'sax', 'Jane_fears': 'heights'}

        assert prob_fixt.get_solution() == solution
