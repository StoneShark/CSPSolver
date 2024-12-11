# -*- coding: utf-8 -*-
"""Base constraint definitions:
    ArcConCheck enumeration
    Exception types
    ConstraintIF required interfaces
    Constraint common operations for constraints

Created on Wed May  3 07:19:36 2023
@author: Ann"""

# %% imports

import abc
import enum


# %% enum

class ArcConCheck(enum.Enum):
    """Does/How the constraint support consistency checking?

	ALWAYS
		- binary function - both values will be provided in arc
		consistency checking
		- satisfied test does a real test with partial assignments

	NEVER
		- ListConstraint
        - OneOrder
		- satisfied test returns True with partial assignments (params > 2)
        e.g. it simply allows the assignments to continue

    CHECK_INST
        - satisfied test returns True with partial assignments but
        if there are two variables/parameters for this instance
        arc consistency checking would be useful."""

    ALWAYS = enum.auto()
    NEVER = enum.auto()
    CHECK_INST = enum.auto()


# %%  exceptions


class ConstraintError(BaseException):
    """Raise ConstraintError if a constraint is poorly constructed,
    e.g. cannot be satisfied, invalid parameters
    Only do this during Constraint construction
    (__init__ or set_variables)."""


class PreprocessorConflict(BaseException):
    """Raise PreprocessorConflict if preprocessing the constraints
    results in an unsolvable problem."""


# %% interface


class ConstraintIF(abc.ABC):
    """Defines the required constraint interfaces.

    Override NAT_NBR_DOMAIN to True if the domain for this
    constraint should be limited to natural numbers (>= 0).

    ARC_CONSIST_CHECK_OK  see ArcConCheck enum on how to set."""


    NAT_NBR_DOMAIN = False
    ARC_CONSIST_CHECK_OK = ArcConCheck.ALWAYS

    def arc_con_ok(self):
        """ Will only be called for classes with
        ARC_CONSIST_CHECK_OK == ArcConCheck.CHECK_INST

        Provide actual implementation so that if
        ARC_CONSIST_CHECK_OK == ArcConCheck.NEVER
        the class does not need to do anything else.

        Return True if a satisfied call with a two variable
        assignment will do a real test (e.g. satisfied always
        tests paritial assignments, or two variables is
        a complete assignment for this instance)."""
        _ = self

        return False

    @abc.abstractmethod
    def get_vnames(self):
        """Return the list of variable names.

        This is used to build the constraint dictionary."""

    @abc.abstractmethod
    def satisfied(self, assignments):
        """Determine if the constraint can be satisfied with the (possibly
        partial) assingments. Do one of:

        1. Return False if the constraint cannot be satisfied.

        2. If there are unassigned variables: return True (required
        for backtracking solvers).

        3. If the expected number of variables are assigned:
        Return True if satisfied, False otherwise.

        assignements: dict - variable : value
        will only contain variables to which the constraint applies,
        but still might be a partial list (not all values assigned yet)."""

    @abc.abstractmethod
    def preprocess(self):
        """Called before we have any assignments.
        Reduce the domains to only values that can be part of the solution.

        RETURN - True if constraint fully applied,
        False if not fully applied and not overconstrained,
        Raise an exception if over constrained."""

    @abc.abstractmethod
    def forward_check(self, assignments):
        """Forward hiding of domain values from unassigned variables
        based on those that are assigned. If a set of changed variables
        are return the forward checking can be propagated (this is not
        required).

        assignments - variables that have been assigned values (so far)

        Return:
            1. False - if any domain has been eliminated (falsy is not ok)
            2. True - if no domains were changed (or empty set).
            3. Otherwise - a set of variable names whose domain was changed."""


# %% common operations


class Constraint(ConstraintIF):
    """Base class for constraints that does many common operations.

    Does not provide a default for satisfied. A trivial satisfied
    (return True) can be used if the default preprocess method
    and _test_over_satis are not used and preprocess always fully
    applies the constraint.

    The default forward_check does nothing."""

    def __init__(self):

        self._vobjs = None
        self._vnames = None
        self._params = 0
        self._arc_con_ok = False


    def set_variables(self, vobj_list):
        """Set the variables present in a full assignment.

        Classes should override this is additional error checking
        can be done or if properties of the vnames list are needed
        (e.g. duplicate)."""

        self._vobjs = vobj_list
        self._vnames = [v.name for v in vobj_list]
        self._params = len(vobj_list)

        if len(set(self._vnames)) != len(self._vnames):
            raise ConstraintError(
                'Duplicate variable names (try lambda wrapper).')

        self._arc_con_ok = self._params == 2


    def get_variables(self):
        """Return the list of variables."""

        return self._vobjs


    def get_vnames(self):
        """Return the list of variable names."""

        return self._vnames


    def arc_con_ok(self):
        """Return the _arc_con_ok val."""
        return self._arc_con_ok


    def _preproc_singles(self, vobj):
        """When a constraint effects only variable, it can be fully
        applied now by removing values from the domain that don't meet
        constraint."""

        for value in vobj.get_domain()[:]:
            if not self.satisfied({vobj: value}):
                vobj.remove_dom_val(value)

        if not vobj.nbr_values():
            raise PreprocessorConflict(
                f'{vobj.name} overconstrained by {self}.')


    def _preproc_doubles(self, vobj1, vobj2):
        """When the constraint has two variables, test it for each
        pair of values in the repective domains, collect the values
        that satistfied and update the domains to the new set of values."""

        newd1 = set()
        newd2 = set()

        for val1 in vobj1.get_domain():
            for val2 in vobj2.get_domain():

                if self.satisfied({vobj1.name: val1, vobj2.name: val2}):
                    newd1 |= {val1}
                    newd2 |= {val2}

        vobj1.set_domain(newd1)
        vobj2.set_domain(newd2)

        dsize1 = vobj1.nbr_values()
        dsize2 = vobj2.nbr_values()

        if not dsize1:
            raise PreprocessorConflict(
                f'{vobj1.name} and {vobj2.name} overconstrained by {self}.')

        return dsize1 == dsize2 == 1


    def preprocess(self):
        """Called before we have any assignments but with all of the variable
		objects that this instance of the constraint will apply to.
        Reduce the domains to only values that can be part of the solution.

        RETURN - True if constraint fully applied,
        False if not fully applied and not overconstrained,
        Raise an exception if over constrained."""

        if self._params == 1:
            self._preproc_singles(self._vobjs[0])
            return True

        if self._params == 2:
            return self._preproc_doubles(self._vobjs[0], self._vobjs[1])

        return self._test_over_satis()


    def _test_over_satis(self):
        """Is a set of variable assignments possible to statisfy
        the constraint?

        Not if the domain of any variable has been eliminated.
        Not if we have a full set of assignments that do not
        satisfy the constraint.

        Return True all variables assigned and meet constraint
        False no overconstraints and don't know if constraint is met."""

        # pylint: disable=compare-to-zero
        # want code for the two if's to have the same structure

        if any(vobj.nbr_values() == 0 for vobj in self._vobjs):

            vnames = ', '.join(str(vobj.name) for vobj in self._vobjs
                               if vobj.nbr_values() == 0)
            msg = f'Preprocess domain eliminated by {self} for {vnames}.'
            raise PreprocessorConflict(msg)

        if all(vobj.nbr_values() == 1 for vobj in self._vobjs):

            constr_assign = {vobj.name: vobj.get_domain()[0]
                             for vobj in self._vobjs}
            if self.satisfied(constr_assign):
                return True

            astr = str(constr_assign)
            msg = f'Preprocess assignments for {self} ' + \
                  f'are overconstrained: {astr}.'
            raise PreprocessorConflict(msg)

        return False


    def forward_check(self, assignments):
        """Forward hiding of domain values from unassigned variables
        based on those that are assigned."""
        _ = self

        return True


    def print_domains(self):
        """Print the domains of the variables."""
        for vobj in self._vobjs:
            print(vobj.name, vobj.get_domain())
