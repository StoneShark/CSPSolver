# -*- coding: utf-8 -*-
"""Define a list of constraints.
These should only be used if there is a good reason to collect
a subset of the constraints into a list:
    AtLeastNCList - require only a subset of the constraints
    AtMostNCList - require that not all of the constraints
    OneOfCList - require exactly one of the constraints be met
    OrCList - require at least one of the constraints be met

List constraints will slow the problem solving; don't use them
unless really needed.

Created on Wed May 10 17:23:37 2023
@author: Ann"""

import operator as op

from . import constraint as cnstr


class ListConstraint(cnstr.ConstraintIF):
    """ListConstraint allows ORing of arbitrary contraint types.

    preprocess and forward_checking are not done on ListConstraints.
    Never do arc consistency checking on ListConstraints.
    Unless there's more software to support these."""

    ARC_CONSIST_CHECK_OK = cnstr.ArcConCheck.NEVER

    def __init__(self, comparer, req_nbr=1, exact=False):

        self._req_nbr = req_nbr
        self._exact = exact

        self._clist = []
        self._vnames = None

        if comparer not in (op.le, op.ge):
            raise NotImplementedError('ListConstraint expects <= or >=.')

        self._op = comparer


    def __repr__(self):
        return self.__class__.__name__  + \
            f'({self._req_nbr}, {self._exact})  ' + \
            '[' + ', '.join([repr(con) for con in self._clist]) + ']'


    def get_vnames(self):
        """Return the list of variable names."""

        return self._vnames


    def add_constraints(self, clist):
        """Add the list of constraints."""

        if not clist:
            raise ValueError(
                'No constraint list provided for ListConstraint.')
        if len(clist) == 1:
            raise ValueError(
                'Do not use ListConstraint with one constraint.')

        var_set = set()
        for constraint in clist:
            var_set |= set(constraint.get_vnames())

        self._vnames = list(var_set)
        self._clist = clist


    @staticmethod
    def _collect_vars(constraint, assignments):
        """Collect the constraint variables that have been assigned values.
        They must be in the order that they were in the constraint list.

        constraint: Constraint
        assignments: the list of currently assigned variables."""

        return {vname : assignments[vname]
                for vname in constraint.get_vnames()
                if vname in assignments}


    def satisfied(self, assignments):
        """Count the number of constraints in the list that are
        satified.

        Short circuit:
        If we exceed the count for AtMostN (<= or le), return False.
        If we exceed the count when exact, return False.
        If we reach the count for AtleastN (>= or ge), return True."""

        # pylint: disable=comparison-with-callable

        count = 0
        for constraint in self._clist:

            cnstr_assign = self._collect_vars(constraint, assignments)
            if constraint.satisfied(cnstr_assign):
                count += 1

            if (self._op == op.le or self._exact) and count > self._req_nbr:
                return False

            if self._op == op.ge and count == self._req_nbr:
                return True

        return ((self._exact and count == self._req_nbr) or
                (not self._exact and self._op(count, self._req_nbr)))


    def preprocess(self):
        """Disable preprocess."""
        return False


    def forward_check(self, _):
        """Disable foward_check."""
        return True



class AtLeastNCList(ListConstraint):
    """A list of constraints of which req_nbr (or more) should be
    True.

    If exact: exactly req_nbr constraints must be True.
    If not exact: at least req_nbr constraints must be True."""

    def __init__(self, req_nbr=1, exact=False):
        super().__init__(op.ge, req_nbr, exact)


class AtMostNCList(ListConstraint):
    """A list of constraints of which req_nbr (or fewer) should be
    True.

    If exact: exactly req_nbr constraints must be True.
    If not exact: at least req_nbr constraints must be True."""

    def __init__(self, req_nbr=1, exact=False):
        super().__init__(op.le, req_nbr, exact)


class OneOfCList(AtMostNCList):
    """A list of constraints, exactly one of which must be True.

    Use AtMostN to short circuit to False if more than 1 is True."""

    def __init__(self):
        super().__init__(1, True)

    def __repr__(self):
        return 'OneOFCList()  ' + \
               '[' + ', '.join([repr(con) for con in self._clist]) + ']'


class OrCList(AtLeastNCList):
    """A list of constraints, one or more of which must be True.

    Use AtLeastN to short circuit to True as soon as one constraint
    returns True."""

    def __init__(self):
        super().__init__(1, False)

    def __repr__(self):
        return 'OrCList()  ' + \
               '[' + ', '.join([repr(con) for con in self._clist]) + ']'
