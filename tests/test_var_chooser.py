# -*- coding: utf-8 -*-
"""
Created on Thu May 11 09:18:00 2023
@author: Ann"""

# %% imports

import pytest
pytestmark = pytest.mark.unittest

import csp_solver as csp

import stubs

# %% good vs bad


GOOD_CHOOSERS = csp.var_chooser.VarChooser.__subclasses__()

class BadChooser(csp.var_chooser.VarChooser):
    pass


# %% a short cut


def make_cnstr(variables):
    """Don't care what the constraint is."""

    con = csp.cnstr.AllEqual()
    con.set_variables(variables)
    return con


# %%   test choose

class TestVarC:

    @pytest.mark.parametrize('vchsr', GOOD_CHOOSERS)
    def test_good_interfaces(self, vchsr):
        """build each to confirm that it defines the required interface"""
        assert vchsr()

    def test_no_interfaces(self):
        """build each to confirm that it defines the required interface"""
        with pytest.raises(TypeError):
            assert BadChooser()


    def test_set_chooser(self):

        slvr = csp.solver.Backtracking()

        assert slvr._chooser == csp.var_chooser.DegreeDomain
        assert 'DegreeDomain' in csp.var_chooser.DegreeDomain.get_name()

        slvr.chooser = csp.var_chooser.UseFirst
        assert slvr._chooser == csp.var_chooser.UseFirst

        with pytest.raises(ValueError):
            slvr.chooser = 5

        with pytest.raises(ValueError):
            slvr.chooser = object()


    def test_UseFirst(self):

        vos = stubs.make_vars([('v1', [1,2]), ('vlong', [1,2]),
                               ('v123', [1,2]), ('a', [1,2])])

        assert csp.var_chooser.UseFirst.choose(vos, None, None).name == 'v1'
        assert 'UseFirst' in csp.var_chooser.UseFirst.get_name()

    def test_var_mname(self):

        vos = stubs.make_vars([('v1', [1,2]), ('vlong', [1,2]),
                               ('v123', [1,2]), ('a', [1,2])])
        assert csp.var_chooser.MaxVarName.choose(vos, None, None).name == 'vlong'
        assert csp.var_chooser.MaxVarName().choose(vos, None, None).name == 'vlong'

    def test_var_mdomain(self):

        vos = stubs.make_vars([('v1', [1,2,3]),('v2', [1,6,3]),
                               ('v3', [1,2]),('v4', [1,2,5,5])])
        assert csp.var_chooser.MinDomain.choose(vos, None, None).name == 'v3'
        assert csp.var_chooser.MinDomain().choose(vos, None, None).name == 'v3'

    def test_mdegree(self):

        vlist =[('v1', [1,2]),('v2', [1,6]),('v3', [1,2]),('v4', [1,2])]
        vos = stubs.make_vars(vlist)

        cdict = { 'v1' : [make_cnstr([vos[0], vos[1]]),
                          make_cnstr([vos[0], vos[2]])],

                  'v2' : [make_cnstr([vos[0], vos[1]]),
                          make_cnstr([vos[0], vos[2]]),
                          make_cnstr([vos[0], vos[3]])],

                  'v3' : [make_cnstr([vos[0], vos[1]])],

                  'v4' : [make_cnstr([vos[0], vos[3]])]}


        pspec = csp.ProblemSpec(variables = vos,
                                         cnstr_dict = cdict)

        assert csp.var_chooser.MaxDegree.choose(vos, pspec, None).name == 'v2'
        assert csp.var_chooser.MaxDegree().choose(vos, pspec, None).name == 'v2'


    def test_degdom_deg(self):

        vos = stubs.make_vars([('v1', [1,2]),('v2', [1,6]),
                               ('v3', [1,2]),('v4', [1,2])])

        cdict = { 'v1' : [make_cnstr([vos[0], vos[1]]),
                          make_cnstr([vos[0], vos[2]])],

                  'v2' : [make_cnstr([vos[1], vos[0]]),
                          make_cnstr([vos[1], vos[2]]),
                          make_cnstr([vos[1], vos[3]])],

                  'v3' : [make_cnstr([vos[2], vos[1]])],

                  'v4' : [make_cnstr([vos[3], vos[0]])]}

        pspec = csp.ProblemSpec(variables = vos, cnstr_dict = cdict)

        assert csp.var_chooser.DegreeDomain.choose(vos, pspec, None).name == 'v2'
        assert csp.var_chooser.DegreeDomain().choose(vos, pspec, None).name == 'v2'


    def test_degdom_dom(self):


        vos = stubs.make_vars([('v1', [1,2,3]),('v2', [1,6,3]),
                               ('v3', [1,2]),('v4', [1,2,5,5])])

        cdict = { 'v1' : [make_cnstr([vos[0], vos[1]]),
                          make_cnstr([vos[0], vos[2]])],

                  'v2' : [make_cnstr([vos[1], vos[0]]),
                          make_cnstr([vos[1], vos[2]]),
                          make_cnstr([vos[1], vos[3]])],

                  'v3' : [make_cnstr([vos[2], vos[0]]),
                          make_cnstr([vos[2], vos[1]]),
                          make_cnstr([vos[2], vos[3]])],

                  'v4' : [make_cnstr([vos[3], vos[0]])]}

        pspec = csp.ProblemSpec(variables = vos, cnstr_dict = cdict)

        assert csp.var_chooser.DegreeDomain.choose(vos, pspec, None).name == 'v3'
        assert csp.var_chooser.DegreeDomain().choose(vos, pspec, None).name == 'v3'


    def test_domdeg_dom(self):


        vos = stubs.make_vars([('v1', [1,2,3]),('v2', [1,6,3]),
                               ('v3', [1,2]),('v4', [1,2,5,5])])

        cdict = { 'v1' : [make_cnstr([vos[0], vos[1]]),
                          make_cnstr([vos[0], vos[2]])],

                  'v2' : [make_cnstr([vos[1], vos[0]]),
                          make_cnstr([vos[1], vos[2]]),
                          make_cnstr([vos[1], vos[3]])],

                  'v3' : [make_cnstr([vos[2], vos[0]]),
                          make_cnstr([vos[2], vos[1]]),
                          make_cnstr([vos[2], vos[3]])],

                  'v4' : [make_cnstr([vos[3], vos[0]])]}

        pspec = csp.ProblemSpec(variables = vos, cnstr_dict = cdict)

        assert csp.var_chooser.DomainDegree.choose(vos, pspec, None).name == 'v3'
        assert csp.var_chooser.DomainDegree().choose(vos, pspec, None).name == 'v3'


    def test_domdeg_deg(self):

        vos = stubs.make_vars([('v1', [1,2]),('v2', [1,6]),
                               ('v3', [1,2]),('v4', [1,2])])

        cdict = { 'v1' : [make_cnstr([vos[0], vos[1]]),
                          make_cnstr([vos[0], vos[2]])],

                  'v2' : [make_cnstr([vos[1], vos[0]]),
                          make_cnstr([vos[1], vos[2]]),
                          make_cnstr([vos[1], vos[3]])],

                  'v3' : [make_cnstr([vos[2], vos[1]])],

                  'v4' : [make_cnstr([vos[3], vos[0]])]}

        pspec = csp.ProblemSpec(variables = vos, cnstr_dict = cdict)

        assert csp.var_chooser.DomainDegree.choose(vos, pspec, None).name == 'v2'
        assert csp.var_chooser.DomainDegree().choose(vos, pspec, None).name == 'v2'



    def test_massignn(self):

        vos = stubs.make_vars([('v1', [1,2,3]),('v2', [1,6,3]),
                               ('v3', [1,2]),('v4', [1,2,5,5]),
                               ('v5', [1,3])])

        con = csp.cnstr.NotInValues(3)
        con.set_variables([vos[4]])

        cdict = { 'v1' : [make_cnstr([vos[0], vos[1]]),
                          make_cnstr([vos[0], vos[2]])],

                  'v2' : [make_cnstr([vos[1], vos[0]]),
                          make_cnstr([vos[1], vos[2]]),
                          make_cnstr([vos[1], vos[3]])],

                  'v3' : [make_cnstr([vos[2], vos[0]]),
                          make_cnstr([vos[2], vos[1]]),
                          make_cnstr([vos[2], vos[4]])],

                  'v4' : [make_cnstr([vos[3], vos[4]])],

                  'v5' : [con]}

        pspec = csp.ProblemSpec(variables = vos,
                                      cnstr_dict = cdict)

        assign = { 'v1' : 1, 'v4' : 3}

        assert csp.var_chooser.MaxAssignedNeighs.choose(
            vos, pspec, assign).name == 'v2'
        assert csp.var_chooser.MaxAssignedNeighs().choose(
            vos, pspec, assign).name == 'v2'
