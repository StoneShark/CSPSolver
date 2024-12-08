# -*- coding: utf-8 -*-
"""Choosing which variable to assign next is important in quickly solving
constraint problems. Define some common orders.

Use a class for two reasons:
    1. defines the interface required
    2. can get the full list of var choosers by getting the
       subclasses of VarChooser

A var_chooser object does not actually need to be instantiated.

The valid function checks assures that a chooser is valid as
either a class or object derived from VarChooser.

Created on Wed May 17 18:35:11 2023
@author: Ann"""


# %% imports

import abc
import functools as ft
import inspect


# %%   valid checker


def valid(chooser):
    """Make certain that chooser is ok.
    Catch an error sooner rather than later.

    The chooser doesn't actually need to be instantiated."""

    if ((inspect.isclass(chooser)
        and not issubclass(chooser, VarChooser)) or
        (not inspect.isclass(chooser)
         and not isinstance(chooser, VarChooser))):

        raise ValueError(
            'The variable chooser should be built upon VarChooser.')

    return True


# %% base VarChooser


class VarChooser(abc.ABC):
    """Base class for variable chooser.
    Used to select the next variable to assign from a list of
    unassigned variables.

    The provided VarChooser's don't actually need to be
    instantiated, because the method is static.
    Though interface spec isn't enforce without instantiation.

    The right chooser is important to the speed of the solver
    on a given problem."""

    @staticmethod
    @abc.abstractmethod
    def choose(vobjs, prob_spec, assignments):
        """Select the next variable to set from vobjs."""

    @classmethod
    def get_name(cls):
        """Return the name of the class (even if we have an instance)."""
        return cls.__name__


# %% concrete classes


class UseFirst(VarChooser):
    """Use the first one on the list i.e. incur almost
    no extra work choosing a variable."""

    @staticmethod
    def choose(vobjs, _1, _2):
        return vobjs[0]


class MaxVarName(VarChooser):
    """Choose the variable that has the longest name.
    Cheesy, but an easy way to control the order."""

    @staticmethod
    def choose(vobjs, _1, _2):
        return max(vobjs, key = lambda var : len(str(var.name)))


class MinDomain(VarChooser):
    """Choose the variable with the smallest remaining domain/range."""

    @staticmethod
    def choose(vobjs, _1, _2):
        return min(vobjs, key = lambda var : var.nbr_values())


class MaxDegree(VarChooser):
    """Choose the variable that is used in the most constraints."""

    @staticmethod
    def choose(vobjs, prob_spec, _):

        return max(vobjs,
                   key = lambda var : len(prob_spec.cnstr_dict[var.name]))


class DegreeDomain(VarChooser):
    """Collect the variables that are used in the most constraints
    then return the one with the smallest domain."""

    @staticmethod
    def choose(vobjs, prob_spec, assignments):

        maxdeg = 0
        varlist = []
        for var in vobjs:

            nbr_cnstr = len(prob_spec.cnstr_dict[var.name])
            if nbr_cnstr > maxdeg:
                maxdeg = nbr_cnstr
                varlist = [var]

            elif nbr_cnstr == maxdeg:
                varlist += [var]

        return MinDomain.choose(varlist, prob_spec, assignments)


class DomainDegree(VarChooser):
    """Collect the variables that all have the same smallest domain,
    then return the one with the largest Degree."""

    @staticmethod
    def choose(vobjs, prob_spec, assignments):

        mindom = 999999
        varlist = []
        for var in vobjs:

            dom = var.nbr_values()
            if dom < mindom:
                mindom = dom
                varlist = [var]

            elif dom == mindom:
                varlist += [var]

        return MaxDegree.choose(varlist, prob_spec, assignments)


class MaxAssignedNeighs(VarChooser):
    """Choose the variable that has the most 'neighbors' that have been
    assigned. Neighbors are 2 variables that are both listed in
    a single constraint."""

    @staticmethod
    def choose(vobjs, prob_spec, assignments):

        def cnstr_vals(assignments, vobj1):
            """Count the number of neighboring variables that have been assigned.
            Count each variable once even if it's in multiple constraints."""
            return len({vname
                        for const in prob_spec.cnstr_dict[vobj1.name]
                        for vname in const.get_vnames() if vname in assignments})

        return max(vobjs, key=ft.partial(cnstr_vals, assignments))
