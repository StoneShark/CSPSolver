# -*- coding: utf-8 -*-
"""A constraint interface that allow rejection of
duplicate solutions.

Created on Sun Jan  5 11:21:20 2025
@author: Ann"""


from . import cnstr_base


class UniqueSolutionsIF(cnstr_base.Constraint):
    """An interface to allow rejection of duplicate solutions.
    The definition of 'duplicate' is left entirely to the
    derived classes.

    A derived class's satisfied method will be called during
    the solver's get_solution calls. It should return False, if
    the current assignment dictionary is known to be a duplicate
    solution and True otherwise.

    solution_found will be called when a new unique solution is
    found, keep whatever data is needed to assure future
    solutions are unique.

    This is still an abstract class (no satisfied defined).
    """

    ARC_CONSIST_CHECK_OK = cnstr_base.ArcConCheck.NEVER

    def solution_found(self, sol_dict):
        """A solution was found save it for future constraint
        tests."""


class UniqueSets(UniqueSolutionsIF):
    """The solution includes multiple variables that
    represent the same thing, do not allow duplicate
    sets of those values to be considered different
    solutions.

    vname_sets is a list of lists of variables names.
    Each sublist represents a 'set' of the same kinds
    of things. If the value sets assigned to the variables
    of each sublist are all equal, then the the solution
    is a duplicate.

    e.g. UniqueSets([['a', 'b'], ['c', 'd', 'e']])
    defines that
       1. the set of values assigned to a and b must be unique
       2. the set of values assigned to c, d, and e must be unique

    If {a: 2, b: 4, c: 3, d: 5, e: 7} is found, then

      {a: 4, b: 2, c: 3, d: 5, e: 7} is a duplicate (first set swapped values)
      {a: 2, b: 4, c: 5, d: 3, e: 7} is a duplicate (second set swapped values)
      {a: 4, b: 2, c: 5, d: 7, e: 3} is a duplicate (both sets swapped values)

      {a: 2, b: 4, c: 4, d: 3, e: 7} is a NOT duplicate (c)
      {a: 2, b: 6, c: 5, d: 3, e: 7} is a NOT duplicate (b)
    """

    def __init__(self, vname_sets):

        if not vname_sets:
            raise cnstr_base.ConstraintError(
                'No variable name sets specified for UniqueSets.')

        if (not isinstance(vname_sets, list)
                or not all(isinstance(vset, list) for vset in vname_sets)):
            raise cnstr_base.ConstraintError(
                'Expected a list of lists of variable names')

        super().__init__()
        self._vname_sets = vname_sets
        self._saved_solutions = []


    def _value_sets(self, sol_dict):
        """Return a list of sets of values corresponding to
        the vname_sets from sol_dict."""

        return [{sol_dict[v] for v in vset}
                for vset in self._vname_sets]


    def solution_found(self, sol_dict):
        """Save the value sets for the solution dictionary."""

        self._saved_solutions += [self._value_sets(sol_dict)]


    def satisfied(self, assignments):
        """Check for a unique solution.
        Before any solutions are found, no extra work is done.
        The test is not done until all assignments are made."""

        if not self._saved_solutions or self._params != len(assignments):
            return True

        new_val_sets = self._value_sets(assignments)

        return not any(all((vset1 == vset2
                            for (vset1, vset2) in zip(sol_val_sets,
                                                      new_val_sets)))
                       for sol_val_sets in self._saved_solutions)
