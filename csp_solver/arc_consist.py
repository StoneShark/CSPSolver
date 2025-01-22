# -*- coding: utf-8 -*-
"""Arc consistency checker.

Created on Mon Jun 19 15:55:41 2023
@author: Ann"""


# %% imports

import abc
import collections as col
import enum
import itertools as it

from .constraint.cnstr_base import ArcConCheck
from . import problem_spec

# %% enum

class ArcStat(enum.Enum):
    """Return vals from arc_reduce."""

    OVERCON = enum.auto()
    CHANGED = enum.auto()
    NONE = enum.auto()


# %% valid

def valid(arc_con):
    """Return True is arc_con is an acceptable arc consistency
    helper.  Must be None (disable arc consistency) or an object
    derived from ArcConIF."""

    if arc_con is None:
        return True

    if not isinstance(arc_con, ArcConIF):
        raise ValueError(
            'The arc consistency helper should be built upon ArcConIF.')

    return True


# %% ArcCon interface

class ArcConIF(abc.ABC):
    """Interface Arc Consistency Helpers."""

    def __init__(self):

        self._spec = None


    def set_pspec(self, pspec):
        """Save the problem spec for furture reference."""

        if not isinstance(pspec, problem_spec.ProblemSpec):
            raise ValueError('ArcConIF.set_pspec needs a ProblemSpec.')

        self._spec = pspec


    @classmethod
    def derived(cls):
        """A class method to find all classes derived from this class."""

        dclasses = cls.__subclasses__()
        return dclasses + [item for dclass in dclasses
                           for item in dclass.__subclasses__()]


    @abc.abstractmethod
    def arc_consist(self, assigned):
        """Adjust the domains of the variables according to
        an arc consistency algorithm.

        Return False if the problem becomes overconstrained;
        True otherwise."""



# %% ArcCon3

class ArcCon3(ArcConIF):
    """Use the AC-3 algorithm to improve arc consistency of the
    problem."""

    def __init__(self):

        super().__init__()
        self._all_arcs = None


    def _get_arcs(self):
        """Build the dictionary of arcs, constraints between two
        variables.  Key: (var name 1, var name 2)  Value: list of
        constraints involving those two variables -- that
        support arc consistency checking."""

        arcs = col.defaultdict(list)
        for vn1, vn2 in it.combinations(self._spec.variables.keys(), 2):

            for con in self._spec.cnstr_dict[vn1]:

                if con.ARC_CONSIST_CHECK_OK == ArcConCheck.NEVER:
                    continue

                if con.ARC_CONSIST_CHECK_OK == ArcConCheck.CHECK_INST \
                   and not con.arc_con_ok():
                    continue

                if con in self._spec.cnstr_dict[vn2]:
                    arcs[(vn1, vn2)] += [con]
                    arcs[(vn2, vn1)] += [con]

        self._all_arcs = arcs.copy()
        return arcs


    @staticmethod
    def _any_value_sats(cons, vn1, val1, vn2, dom2):
        """Return True if any value in dom2 meets all the constraits
        in cons with val1, False otherwise.

        Do the following operation, but deal with the order of
        variables in the assignment dictionary (directional edges):

            any(all(con.satisfied(assigns) for con in cons)
                for val2 in dom2)
        """

        for val2 in dom2:
            for con in cons:

                if con.get_vnames()[0] == vn1:
                    assigns = {vn1 : val1, vn2 : val2}
                else:
                    assigns = {vn2 : val2, vn1 : val1}

                if not con.satisfied(assigns):
                    # current value doesn't meet all cons, go on to next
                    break

            else:
                #  only get here if no break => all cons met by val1, val2
                return True

        return False


    def _arc_reduce(self, cons, vn1, vn2):
        """Remove values of the domain of vn1 when there is
        not any value of vn2/dom2 that meets all the constraints.

        Return ArcStat."""

        status = ArcStat.NONE

        vobj1 = self._spec.variables[vn1]
        vobj2 = self._spec.variables[vn2]

        dom2 = vobj2.get_domain()

        for val1 in vobj1.get_domain_copy():

            if not self._any_value_sats(cons, vn1, val1, vn2, dom2):
                if not vobj1.hide(val1):
                    return ArcStat.OVERCON

                status = ArcStat.CHANGED

        return status


    def arc_consist(self, assigned):
        """Use the AC-3 algorithm to improve arc consistency of the
        problem.

        1. Create a dictionary of the arcs or copy the one we have.

        2. Reduce each arc in arcs, moving any previously processed
        arcs back into arcs if there was a reduction.

        3. Add the just processed arc into previously processed arcs.

        Return False if we've overconstrained the problem (eliminated
        all domain values for any variable), True otherwise."""

        arcs = self._all_arcs.copy() if self._all_arcs else self._get_arcs()
        proc_arcs = {}

        while arcs:
            (vn1, vn2), cons = arcs.popitem()
            if vn1 in assigned:
                continue

            arc_stat = self._arc_reduce(cons, vn1, vn2)

            if arc_stat == ArcStat.OVERCON:
                return False

            if arc_stat == ArcStat.CHANGED:

                for edges, old_cons in proc_arcs.items():
                    if vn1 in edges and vn2 not in edges:

                        # want vn1 second in tuple below
                        oedges = reversed(edges) if vn1 == edges[0] else edges

                        arcs[oedges] = old_cons

            proc_arcs[(vn1, vn2)] = cons

        return True
