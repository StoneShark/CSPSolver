# -*- coding: utf-8 -*-
"""Define classes for lists of constraints.

Constraints in a problem are ANDed together, these classes
allow not requiring that all constraints be met.

These should only be used if there is a good reason to collect
a subset of the constraints into a list:
    AtLeastNCList - require only a subset of the constraints be met
    AtMostNCList - require that not all of the constraints be met
    NOfCList - require exactly n of the constraints be met
    OneOfCList - require exactly one of the constraints be met
    OrCList - require at least one of the constraints be met

AtMostNCList, NOfCList and OneOfCLIST return True until all variable
assignments are made.

List constraints will slow the problem solving; don't use them
unless really needed.

Created on Wed May 10 17:23:37 2023
@author: Ann"""

# XXXX AtMostNCList & NOfCList return T until all assigns made (better way?)
# possibly could use ArcConCheck (but give it a better name)
# are these really worth more work?


from . import constraint as cnstr


class ListConstraint(cnstr.ConstraintIF):
    """ListConstraint allows ORing of arbitrary contraint types.
    This is still an abstract class as satisfied is not defined.

    Preprocessing, forward checking and arc consistency checking
    are not done on ListConstraints or their supporting constraints."""

    ARC_CONSIST_CHECK_OK = cnstr.ArcConCheck.NEVER

    def __init__(self, req_nbr):

        self._clist = []
        self._vnames = None
        self._params = 0
        self._req_nbr = req_nbr


    def __repr__(self):
        return self.__class__.__name__ + "()  " \
               + '[' + ', '.join([repr(con) for con in self._clist]) + ']'


    def get_vnames(self):
        """Return the list of variable names."""

        return self._vnames


    def set_constraints(self, clist):
        """Set the list of constraints.
        Only one call to this method may be made."""

        if not clist:
            raise ValueError(
                'No constraint list provided for ListConstraint.')
        if len(clist) == 1:
            raise ValueError(
                'Do not use ListConstraint with one constraint.')
        if self._params:
            raise cnstr.ConstraintError(
                'Do not call ListConstraint.set_constraints '
                'more than once per list constraint.')

        var_set = set()
        for constraint in clist:
            var_set |= set(constraint.get_vnames())

        self._params = len(var_set)
        self._vnames = list(var_set)
        self._clist = clist

        if self._req_nbr > len(self._clist):
            raise cnstr.ConstraintError(
                'ListConstraint.set_constraints: '
                'Required constraints too high for contraint list.')


    @staticmethod
    def _collect_vars(constraint, assignments):
        """Collect the constraint variables that have been assigned values.
        They must be in the order that they were in the constraint list.

        constraint: Constraint
        assignments: the list of currently assigned variables."""

        return {vname : assignments[vname]
                for vname in constraint.get_vnames()
                if vname in assignments}


    def preprocess(self):
        """Disable preprocess."""
        return False


    def forward_check(self, _):
        """Disable foward_check."""
        return True



class AtLeastNCList(ListConstraint):
    """A list of constraints of which req_nbr (or more) should be
    True. At least req_nbr constraints must be True."""

    def satisfied(self, assignments):
        """Count the number of constraints in the list that are
        satified. Return True when the satisfied count exceeds
        the required count."""

        count = 0
        for constraint in self._clist:

            cnstr_assign = self._collect_vars(constraint, assignments)
            if constraint.satisfied(cnstr_assign):
                count += 1

            if count >= self._req_nbr:
                return True

        return False


class AtMostNCList(ListConstraint):
    """A list of constraints of which req_nbr (or fewer) should be
    True. At most req_nbr constraints must be True."""

    def satisfied(self, assignments):
        """Count the number of constraints in the list that are
        satified. Some constraints may return True until a full
        assignment set is made, do not return False until all
        assignments are made.
        If the satified count exceeeds the required limit
        return False, otherwise return True. """

        all_assigned = len(assignments) == self._params
        count = 0

        for constraint in self._clist:

            cnstr_assign = self._collect_vars(constraint, assignments)
            if constraint.satisfied(cnstr_assign):
                count += 1

            if all_assigned and count > self._req_nbr:
                return False

        return (not all_assigned) or (all_assigned and count <= self._req_nbr)


class NOfCList(ListConstraint):
    """A list of constraints, exactly N of which must be True."""

    def satisfied(self, assignments):
        """Count the number of constraints in the list that are
        satified.  Some constraints may return True until a full
        assignment set is made, do not return False until all
        assignments are made. If we exceed req_nbr return false.
        Otherwise do the test after counting all."""

        all_assigned = len(assignments) == self._params
        count = 0

        for constraint in self._clist:

            cnstr_assign = self._collect_vars(constraint, assignments)
            if constraint.satisfied(cnstr_assign):
                count += 1

            if all_assigned and count > self._req_nbr:
                return False

        return (not all_assigned) or (all_assigned and count == self._req_nbr)


class OneOfCList(NOfCList):
    """A list of constraints, exactly one of which must be True.
    This returns True until all variables are assigned."""

    def __init__(self):
        super().__init__(1)


class OrCList(AtLeastNCList):
    """A list of constraints, one or more of which must be True.
    Use AtLeastN to short circuit to True as soon as one constraint
    returns True."""

    def __init__(self):
        super().__init__(1)
