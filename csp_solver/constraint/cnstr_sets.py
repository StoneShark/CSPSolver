# -*- coding: utf-8 -*-
"""Constraints that behave a bit like sets.

Given a list of variables; possible assignments (elements);
and a required number (req_nbr), enforce a constraint on the
number assignments with specified values:

    ExactlyNIn
    AtLeastNIn
    AtMostNIn

    AtLeastNNotIn

Arc consistency checking is limited for all SetConstraints.

Created on Sun Dec 15 12:55:13 2024
@author: Ann"""


from . import cnstr_base


class SetConstraint(cnstr_base.Constraint):
    """Constrain the assignments with a particular set of values.
    This is still an abstract class because satisfied is not defined.

    Each class defines how elements are used."""


    ARC_CONSIST_CHECK_OK = cnstr_base.ArcConCheck.CHECK_INST


    def __init__(self, elements, req_nbr):

        super().__init__()
        self._elements = elements
        self._req_nbr = req_nbr


    def __repr__(self):
        return self.__class__.__name__ + \
            f'({self._elements}, {self._req_nbr})'


    def set_variables(self, vobj_list):
        """Check for construction error."""

        super().set_variables(vobj_list)

        if self._req_nbr == self._params:
            raise cnstr_base.ConstraintError(
                f'{self}: req_nbr == number variables, '
                'use InValues/NotInValues.')

        if self._req_nbr > self._params:
            raise cnstr_base.ConstraintError(
                f'{self}: req_nbr must be < number variables.')


    def preprocess(self):
        """Disable preprocessing.
        If its a good constraint (i.e. set_variables accepted it),
        then there is nothing else we can do."""
        _ = self
        return False


    def counts(self, assignments):
        """Count the number of assignments in elements,
        and compute the number of unassigned variables."""

        nbr_good = sum(1 for val in assignments.values()
                       if val in self._elements)
        nbr_unassigned = self._params - len(assignments)

        return nbr_good, nbr_unassigned



class ExactlyNIn(SetConstraint):
    """The number of assignments with values in _elements
    must be exactly _req_nbr.

    Return false if we have too many (even with partial assignments)
    or there are not enough unassigned variables to get to req_nbr,
    otherwise return True until we have all the assignments,
    otherwise test for assigned number."""


    def satisfied(self, assignments):
        """Test the given assignements."""

        nbr_good, nbr_unassigned = self.counts(assignments)

        if (nbr_good > self._req_nbr
            or nbr_unassigned + nbr_good < self._req_nbr):
            return False

        if nbr_unassigned:
            return True

        return nbr_good == self._req_nbr


    def forward_check(self, assignments):
        """If we have exactly the number of good assignments,
        we can remove the good values from the unassigned variables."""

        nbr_good, nbr_unassigned = self.counts(assignments)

        if nbr_unassigned and nbr_good == self._req_nbr:
            # remove good_values (elements) from unassigned variables
            return self.hide_bad_values(
                            assignments,
                            lambda _, value: value not in self._elements)

        if nbr_unassigned + nbr_good < self._req_nbr:
            # constraint can't be met
            return False

        if nbr_unassigned + nbr_good == self._req_nbr:
            return self.hide_bad_values(
                            assignments,
                            lambda _, value: value in self._elements)

        return True


class AtLeastNIn(SetConstraint):
    """The number of assignments with values in _elements
    must be >= _req_nbr.

    Return True until we have all of the assignments.
    Then test if there are too few assignments."""


    def satisfied(self, assignments):
        """Test the given assignements."""

        nbr_good, nbr_unassigned = self.counts(assignments)

        if nbr_unassigned + nbr_good < self._req_nbr:
            # constraint can't be met
            return False

        if nbr_unassigned:
            return True

        return nbr_good >= self._req_nbr


    def forward_check(self, assignments):
        """Reduce the domain of the remaining variables if we can be
        certain that they must all be in good values."""

        nbr_good, nbr_unassigned = self.counts(assignments)

        if nbr_good >= self._req_nbr:
            # constraint met, more are ok
            return True

        if nbr_unassigned + nbr_good < self._req_nbr:
            # constraint can't be met
            return False

        if nbr_unassigned + nbr_good == self._req_nbr:
            return self.hide_bad_values(
                            assignments,
                            lambda _, value: value in self._elements)
        return True


class AtMostNIn(SetConstraint):
    """The number of assignments with values in _elements
    must be <= _req_nbr.

    Return false if we have too many (even with partial assignments),
    otherwise return True until we have all the assignments,
    otherwise test for assigned number."""


    def satisfied(self, assignments):
        """Test the given assignements."""

        nbr_good, nbr_unassigned = self.counts(assignments)

        if nbr_good > self._req_nbr:
            return False

        if nbr_unassigned:
            return True

        return nbr_good <= self._req_nbr


    def forward_check(self, assignments):
        """If we have exactly the number of good assignments
        (max number of good assignments), we can remove the
        good values from the unassigned variables."""

        nbr_good, nbr_unassigned = self.counts(assignments)

        if nbr_unassigned and nbr_good == self._req_nbr:
            return self.hide_bad_values(
                            assignments,
                            lambda _, value: value not in self._elements)

        return True


# %% the not in constraint

class AtLeastNNotIn(SetConstraint):
    """Required number of values in must not be in elements.
    Return True until we have have all the assignments.
    """

    def satisfied(self, assignments):
        """Test the given assignements."""

        if len(assignments) < self._params:
            return True

        nbr_bad = sum(1 for val in assignments.values()
                      if val not in self._elements)

        return nbr_bad >= self._req_nbr


    def forward_check(self, assignments):
        """Reduce the domain of the remaining variables if we can be
        certain that they must all be in bad_vals."""

        nbr_bad = sum(1 for val in assignments.values()
                      if val not in self._elements)
        nbr_unassigned = self._params - len(assignments)

        if nbr_bad >= self._req_nbr:
            # constraint already met
            return True

        if nbr_unassigned + nbr_bad < self._req_nbr:
            # constraint can't be met
            return False

        changes = self.hide_bad_values(
                        assignments,
                        lambda _, value: value not in self._elements)
        return changes
