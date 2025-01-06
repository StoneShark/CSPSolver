# -*- coding: utf-8 -*-
"""Common Concrete Constraints

Created on Wed May  3 07:19:36 2023
@author: Ann"""

import functools as ft

from . import cnstr_base


class BoolFunction(cnstr_base.Constraint):
    """A functional constraint.  Assignments might be a partial list.

    There are two ways the function is called:

    1. If var_args is True, the function is called with parameters
    that we have (the function gets the assignment dictionary).
    No test is made to see if the assignments are complete.

    2. Call the function with positional arguments but only
    when we have all the assignments (var_args == False).
    Arguments are in the same order as they were in the
    add_constraint call.
    Otherwise, if we don't have all the assignments,
    return True to keep assigning variables."""

    ARC_CONSIST_CHECK_OK = cnstr_base.ArcConCheck.CHECK_INST

    def __init__(self, func, var_args=False):

        if not callable(func):
            raise cnstr_base.ConstraintError(
                'func not callable in BoolFunction.')

        super().__init__()
        self._func = func
        self._var_args = var_args


    def __repr__(self):

        if isinstance(self._func, ft.partial):
            fname = f'{self._func.func.__name__}{self._func.args}'
            return f'BoolFunctions({fname}, {self._var_args})'

        return f'BoolFunction({self._func.__name__}, {self._var_args})'


    def satisfied(self, assignments):
        """Test the given assignements."""

        if self._var_args:
            return self._func(assignments)

        if len(assignments) == self._params:
            return self._func(*assignments.values())

        return True


    def forward_check(self, assignments):
        """If there is one unassigned variable left, reduce it's domain."""

        if len(assignments) + 1 != self._params:
            return True

        for vobj in self._vobjs:
            if vobj.name not in assignments:
                break
        else:
            vobj = None

        rval = True
        for value in vobj.get_domain()[:]:

            if not self.satisfied(assignments | {vobj.name: value}):
                rval = {vobj.name}
                if not vobj.hide(value):
                    return False

        return rval


class AllDifferent(cnstr_base.Constraint):
    """All assigned values must be different.

    It's fine if we don't have all the assigned values yet,
    test those that we have. If they are not all different,
    we can short circuit with a False"""

    def satisfied(self, assignments):
        """Test the given assignements."""
        _ = self

        values = assignments.values()
        return len(values) == len(set(values))


    def preprocess(self):
        """Override the default method.
        Satisfied with one var is True; the default would
        delete the whold domain.

        RETURN - True if constraint fully applied,
        False if not fully applied and not overconstrained,
        Raise an exception if over constrained."""

        return self._test_over_satis()


    def forward_check(self, assignments):
        """Hide the values that have already been assigned from
        the domains of those that have not yet been assigned."""

        # pylint: disable=duplicate-code
        # the inner loop is different! would be very confusing code to change

        assign_vals = set(assignments.values())
        if len(assign_vals) == self._params:
            return True

        changes = set()
        for vobj in self._vobjs:
            if vobj.name in assignments:
                continue

            for value in assign_vals:
                if value in vobj.get_domain():
                    changes |= {vobj.name}

                    if not vobj.hide(value):
                        return False

        return changes


class AllEqual(cnstr_base.Constraint):
    """All assigned values must be the same.

    It's fine if we don't have all the assigned values yet,
    test those that we have. If they are not all equal,
    we can short circuit with a False"""

    def satisfied(self, assignments):
        """Test the given assignements."""
        _ = self

        values = list(assignments.values())
        return all(values[0] == val for val in values[1:])


    def preprocess(self):
        """Override the default method.
        Satisfied with one var is True; the default would
        delete the whold domain.

        RETURN - True if constraint fully applied,
        False if not fully applied and not overconstrained,
        Raise an exception if over constrained."""

        return self._test_over_satis()


    def forward_check(self, assignments):
        """If any of the values have been set, then hide any other
        values from the domains of the unset variables."""

        known_val = list(assignments.values())[0]

        changes = self.hide_bad_values(
                        assignments,
                        lambda _, value: value == known_val)
        return changes


class InValues(cnstr_base.Constraint):
    """Assigned variables must be in the provided set."""

    def __init__(self, good_vals):
        if not good_vals:
            raise cnstr_base.ConstraintError(
                'No good_values specified for InValues.')

        super().__init__()
        self._good_vals = good_vals


    def __repr__(self):
        return f'InValues({self._good_vals})'


    def satisfied(self, assignments):
        """Test the given assignements.
        Preprocess completely handles except when in list constraints."""

        return all(val in self._good_vals for val in assignments.values())


    def preprocess(self):
        """Remove domain values that are not in the set.
        Call _test_over_satis to test for overconstraint, ignore return value.
        RETURN - True - constraint always fully applied"""

        for vobj in self._vobjs:
            for value in vobj.get_domain()[:]:
                if value not in self._good_vals:
                    vobj.remove_dom_val(value)

        self._test_over_satis()
        return True


class NotInValues(cnstr_base.Constraint):
    """Assigned variables must not be in the provided set."""

    def __init__(self, bad_vals):
        if not bad_vals:
            raise cnstr_base.ConstraintError(
                'No bad_values specified for NotInValues.')

        super().__init__()
        self._bad_vals = bad_vals


    def __repr__(self):
        return f'NotInValues({self._bad_vals})'


    def satisfied(self, assignments):
        """Test the given assignements.
        Preprocess completely handles except when in list constraints."""

        return all(val not in self._bad_vals for val in assignments.values())


    def preprocess(self):
        """Remove domain values that are in the set.
        Call _test_over_satis to test for overconstraint, ignore return value.
        RETURN - True - constraint always fully applied"""

        for vobj in self._vobjs:
            for value in vobj.get_domain()[:]:
                if value in self._bad_vals:
                    vobj.remove_dom_val(value)

        self._test_over_satis()
        return True


class OneOrder(cnstr_base.Constraint):
    """Variable values may only be assigned in increasing order.

    This constraint can sometimes be used to remove duplicate
    solutions when multiple variables represent the same kind
    of thing."""

    ARC_CONSIST_CHECK_OK = cnstr_base.ArcConCheck.CHECK_INST

    def satisfied(self, assignments):
        """Check for increasing value order."""
        _ = self

        dsize = len(assignments)
        if dsize == 1:
            return True

        vals = list(assignments.values())
        return all(vals[i] <= vals[i + 1] for i in range(dsize - 1))


class LessThan(cnstr_base.Constraint):
    """val1 < val2"""

    def set_variables(self, vobj_list):
        """Check for exactly two variables."""

        super().set_variables(vobj_list)

        if self._params != 2:
            raise cnstr_base.ConstraintError(
                f'{self} works on exactly two variables.')


    def satisfied(self, assignments):
        """Test the constraint."""

        if len(assignments) == self._params:
            vals = list(assignments.values())
            return vals[0] < vals[1]

        return True


    def preprocess(self):
        """val1 < val2
        1. remove all values from var1 that are
        greater than or equal to the max of dom2
        2. remove all values from var2 that are
        less than or equal to min of dom1"""

        vobj1 = self._vobjs[0]
        vobj2 = self._vobjs[1]

        min_dom1 = min(vobj1.get_domain())
        max_dom2 = max(vobj2.get_domain())

        for val in vobj1.get_domain()[:]:
            if val >= max_dom2:
                vobj1.remove_dom_val(val)

        for val in vobj2.get_domain()[:]:
            if val <= min_dom1:
                vobj2.remove_dom_val(val)

        return self._test_over_satis()


    def forward_check(self, assignments):
        """If the first variable is assigned and the second is not,
        limit the domain of the seconds to values >= val1.
        If the second variable is assigned and the first is not,
        limit the domain of the first to values < val2."""

        if not assignments or len(assignments) == self._params:
            return True
        change = False

        if self._vnames[0] in assignments:
            val1 = assignments[self._vnames[0]]

            for val2 in self._vobjs[1].get_domain()[:]:

                if val1 >= val2:
                    change = True
                    if not self._vobjs[1].hide(val2):
                        return False

            return {self._vnames[1]} if change else True

        # else:

        val2 = assignments[self._vnames[1]]

        for val1 in self._vobjs[0].get_domain()[:]:

            if val1 >= val2:
                change = True
                if not self._vobjs[0].hide(val1):
                    return False

        return {self._vnames[0]} if change else True



class LessThanEqual(cnstr_base.Constraint):
    """val1 <= val2"""

    def set_variables(self, vobj_list):
        """Check for exactly two variables."""

        super().set_variables(vobj_list)

        if self._params != 2:
            raise cnstr_base.ConstraintError(
                f'{self} works on exactly two variables.')


    def satisfied(self, assignments):
        """Test the constraint."""

        if len(assignments) == self._params:
            vals = list(assignments.values())
            return vals[0] <= vals[1]

        return True


    def preprocess(self):
        """val1 < val2
        1. remove all values from var1 that are
        greater than or equal to the max of dom2
        2. remove all values from var2 that are
        less than or equal to min of dom1"""

        vobj1 = self._vobjs[0]
        vobj2 = self._vobjs[1]

        min_dom1 = min(vobj1.get_domain())
        max_dom2 = max(vobj2.get_domain())

        for val in vobj1.get_domain()[:]:
            if val > max_dom2:
                vobj1.remove_dom_val(val)

        for val in vobj2.get_domain()[:]:
            if val < min_dom1:
                vobj2.remove_dom_val(val)

        return self._test_over_satis()


    def forward_check(self, assignments):
        """If the first variable is assigned and the second is not,
        limit the domain of the seconds to values >= val1.
        If the second variable is assigned and the first is not,
        limit the domain of the first to values < val2."""

        if not assignments or len(assignments) == self._params:
            return True
        change = False

        if self._vnames[0] in assignments:
            val1 = assignments[self._vnames[0]]

            for val2 in self._vobjs[1].get_domain()[:]:

                if val1 > val2:
                    change = True
                    if not self._vobjs[1].hide(val2):
                        return False

            return {self._vnames[1]} if change else True

        # else:

        val2 = assignments[self._vnames[1]]

        for val1 in self._vobjs[0].get_domain()[:]:

            if val1 > val2:
                change = True
                if not self._vobjs[0].hide(val1):
                    return False

        return {self._vnames[0]} if change else True
