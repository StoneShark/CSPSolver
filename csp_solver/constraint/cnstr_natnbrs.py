# -*- coding: utf-8 -*-
"""Constraints that assume natural numbers (>= 0).

Created on Sun Dec 15 12:43:51 2024
@author: Ann"""


from . import cnstr_base


class MaxSum(cnstr_base.Constraint):
    """Assigned variables must sum to less than or equal to max.

    Assumes all variables have natural integer domains (>= 0)."""

    NAT_NBR_DOMAIN = True

    def __init__(self, maxsum):

        super().__init__()
        self._maxsum = maxsum


    def __repr__(self):
        return f'MaxSum({self._maxsum})'


    def satisfied(self, assignments):
        """Test the given assignements."""

        return sum(assignments.values()) <= self._maxsum


    def preprocess(self):
        """Remove values that are too large.

        If all combinations of assignments satisfies the constraint
        (sum of max of each domain), return True.

        RETURN - True if constraint fully applied,
        False if not fully applied and not overconstrained,
        Raise an exception if over constrained."""

        if super().preprocess():
            return True

        for vobj in self._vobjs:
            for value in vobj.get_domain()[:]:
                if value > self._maxsum:
                    vobj.remove_dom_val(value)

        if self._test_over_satis():
            return True

        if sum(max(vobj.get_domain()) for vobj in self._vobjs) <= self._maxsum:
            return True

        return False


    def forward_check(self, assignments):
        """The asssignments are either a final sum or a partial sum,
        hide domain values from the unset variables that would violate
        the max_sum constraint."""

        cur_sum = sum(assignments.values())

        changes = self.hide_bad_values(
                        assignments,
                        lambda _, value: value + cur_sum <= self._maxsum)
        return changes


class ExactSum(cnstr_base.Constraint):
    """Assigned variables must sum to equal value.

    Assumes all variables have natural integer domains (>= 0)."""

    NAT_NBR_DOMAIN = True

    def __init__(self, exactsum):

        super().__init__()
        self._exactsum = exactsum


    def __repr__(self):
        return f'ExactSum({self._exactsum})'


    def satisfied(self, assignments):
        """Test the given assignements."""

        cur_sum = sum(assignments.values())

        if len(assignments) == self._params:
            return cur_sum == self._exactsum

        return cur_sum <= self._exactsum


    def preprocess(self):
        """Remove values that are too large.

        RETURN - True if constraint fully applied,
        False if not fully applied and not overconstrained,
        Raise an exception if over constrained."""

        if super().preprocess():
            return True

        for vobj in self._vobjs:
            for value in vobj.get_domain()[:]:
                if value > self._exactsum:
                    vobj.remove_dom_val(value)

        return self._test_over_satis()


    def forward_check(self, assignments):
        """The asssignments are either a final sum or a partial sum,
        hide domain values from the unset variables that would violate
        the max_sum constraint."""

        cur_sum = sum(assignments.values())

        changes = self.hide_bad_values(
                        assignments,
                        lambda _, value: value + cur_sum <= self._exactsum)
        return changes


class MinSum(cnstr_base.Constraint):
    """Assigned variables must sum to >= to minsum.

    Assumes all variables have natural integer domains (>= 0)."""

    NAT_NBR_DOMAIN = True
    ARC_CONSIST_CHECK_OK = cnstr_base.ArcConCheck.CHECK_INST

    def __init__(self, minsum):

        super().__init__()
        self._minsum = minsum


    def __repr__(self):
        return f'MinSum({self._minsum})'


    def satisfied(self, assignments):
        """Only test the given assignements when we have all of the
        assignments. Return True otherwise, to keep making assignments."""

        if len(assignments) == self._params:
            return sum(assignments.values()) >= self._minsum

        return True


    def preprocess(self):
        """Use parent preprocessor to handle single variable constraints.

        If the max value of variable does not sum to more than _minsum,
        raise overconstraint error.

        If all combinations of assignments satisfies the constraint
        (sum of min of each domain), return True.

        RETURN - True if constraint fully applied,
        False if not fully applied and not overconstrained,
        Raise an exception if over constrained."""

        if super().preprocess():
            return True

        if sum(max(vobj.get_domain()) for vobj in self._vobjs) < self._minsum:

            vnames = ', '.join(vobj.name for vobj in self._vobjs)
            msg = f'Preprocess detected overconstraint by {self} for {vnames}.'
            raise cnstr_base.PreprocessorConflict(msg)

        if sum(min(vobj.get_domain()) for vobj in self._vobjs) >= self._minsum:
            return True

        return False
