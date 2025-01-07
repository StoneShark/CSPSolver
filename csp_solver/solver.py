# -*- coding: utf-8 -*-
"""The interface for the constraint solvers and
three solvers:
    Backtracking
    NonRecBacktracking
    MinConflictsSolver

Created on Wed May  3 07:56:04 2023
@author: Ann"""


# %% imports

import abc
import collections as col
import enum
import functools as ft
import random

from . import arc_consist
from . import extra_data
from . import var_chooser


# %%   enums

class SolveType(enum.Enum):
    """Number of solutions we are seeking."""

    ONE = enum.auto()
    ALL = enum.auto()
    MORE_THAN_ONE = enum.auto()


# %%   solver base class

class Solver(abc.ABC):
    """Abstract base class for solvers."""

    def __init__(self, forward_check=False, problem_spec=None):
        """The interface get_solution will override the
        problem specification."""

        self._spec = problem_spec
        self._nbr_variables = len(self._spec.variables) if problem_spec else 0

        self._chooser = var_chooser.DegreeDomain
        self._arc_con = None
        self._forward = forward_check
        self._extra = None

        self._solve_type = SolveType.ONE


    @classmethod
    def derived(cls):
        """A class method to find all classes derived from this class."""

        dclasses = cls.__subclasses__()
        return dclasses + [item for dclass in dclasses
                           for item in dclass.__subclasses__()]

    @property
    def chooser(self):
        """Return the chooser property."""
        return self._chooser

    @chooser.setter
    def chooser(self, chooser):
        """Select the variable chooser.  Can be the class or instance."""
        if var_chooser.valid(chooser):
            self._chooser = chooser


    @property
    def arc_con(self):
        """Get the arc consistency checker."""
        return self._arc_con

    @arc_con.setter
    def arc_con(self, arc_con):
        """Set an arc consistency helper.
        None to disable or a valid class."""

        if arc_consist.valid(arc_con):
            self._arc_con = arc_con


    @property
    def forward(self):
        """Get the forward check property."""
        return self._forward

    @forward.setter
    def forward(self, value):
        """Set the forward check value."""
        self._forward = value


    def enable_forward_check(self):
        """Enable the forward checking in the solver."""
        self._forward = True


    @property
    def extra(self):
        """Return the extra data representation."""
        return self._extra

    @extra.setter
    def extra(self, extra):
        """Use an extra data representation.  Save the it.

        This might be called to copy solver params from one solver
        to another (must work extra == None)."""
        if extra and not isinstance(extra, extra_data.ExtraDataIF):
            raise ValueError('extra_data must be built on extra_data.ExtraDataIF')

        self._extra = extra


    def _assign_extra(self, var, val):
        """If and extra data object was provided, call it's assign
        method, returning the result."""

        if self._extra:
            return self._extra.assign(var, val)
        return True


    def _pop_extra(self):
        """If an extra data object was provided, call it's pop method."""

        if self._extra:
            self._extra.pop()


    @staticmethod
    def _select_assignments(var_names, assignments):
        """Collect the constraint variables that have been assigned values.
        They must be in the order that they were in the constraint list."""

        return {vname : assignments[vname] for vname in var_names
                if vname in assignments}


    def _consistent(self, var_name, assignments):
        """For each constraint that uses var_name,
        check to see if the associated variables satistfy the constraint
        If any constraint is not satified return False, otherwise True"""

        for constraint in self._spec.cnstr_dict[var_name]:

            const_assign = self._select_assignments(constraint.get_vnames(),
                                                    assignments)
            if not constraint.satisfied(const_assign):
                return False

        return True


    def _all_consistent(self, assignments):
        """Check all constraints against all assignments.
        If any constraint is not satified return False, otherwise True"""

        for constraint in self._spec.constraints:

            const_assign = self._select_assignments(constraint.get_vnames(),
                                                    assignments)
            if not constraint.satisfied(const_assign):
                return False

        return True


    def _forward_check(self, var_name, assignments):
        """Do the forward check on the constrains that use var_name.
        If the domains of any variables are changed re-run their
        forward_check. Even though forward checks are only on
        assignments, the values assigned to other varaibles
        (not var_name) might constrain the domain more.

        Return:  If the forward check overcontrains the problem return False,
        to backtrack (or what ever the sovler wants to do); otherwise True."""

        if not self._forward:
            return True

        fc_vars = set([var_name])
        while fc_vars:

            vname = fc_vars.pop()
            for cons in self._spec.cnstr_dict[vname]:

                const_assign = self._select_assignments(cons.get_vnames(),
                                                        assignments)

                fc_rval = cons.forward_check(const_assign)
                if fc_rval is False:
                    return False

                if fc_rval is True:
                    continue

                fc_vars |= fc_rval

        return True


    def _stop_solver(self, solutions):
        """Return True if we've meet the SolveType criteria."""

        return (solutions and
                (self._solve_type == SolveType.ONE or
                 (self._solve_type == SolveType.MORE_THAN_ONE and
                  len(solutions) > 1)))


    @abc.abstractmethod
    def get_solution(self, problem_spec, solve_type):
        """Return solutions: ONE, ALL or
        MORE_THAN_ONE stops at two solutions, use to determine
        if solution is unique.

        variables a dictionary of var_name : var_object

        const_dict is a dictionary of
         var_name : list of tuples ( Constraint, all_var_names_for_contraint )"""


# %%  recursive backtracking

class Backtracking(Solver):
    """Simple recursive backtracking solver."""

    def _forw_arc_processing(self, solutions, local_assigns, unassigned, vobj):
        """Do the forward process and arc consistency checking."""

        for tempv in unassigned:
            tempv.push_domain()

        still_good = True
        if self._arc_con:
            still_good = self._arc_con.arc_consist(local_assigns)

        if still_good and self._forward_check(vobj.name, local_assigns):
            self._search_solution(solutions, local_assigns)

        if self._stop_solver(solutions):
            return solutions

        for tempv in unassigned:
            tempv.pop_domain()

        return solutions


    def _search_solution(self, solutions, assignments):
        """Search for one or more solutions."""

        if len(assignments) == self._nbr_variables:
            if self._spec.usol_cnstr:
                self._spec.usol_cnstr.solution_found(assignments)

            solutions += [assignments]
            return solutions

        unassigned = [vobj for v_name, vobj in self._spec.variables.items()
                      if v_name not in assignments]
        vobj = self._chooser.choose(unassigned, self._spec, assignments)
        unassigned.remove(vobj)

        for value in vobj.get_domain()[:]:

            local_assigns = assignments | {vobj.name : value}
            if not self._assign_extra(vobj.name, value):
                continue

            if not self._consistent(vobj.name, local_assigns):
                self._pop_extra()
                continue

            if self._forward:
                solutions = self._forw_arc_processing(solutions,
                                                      local_assigns, unassigned,
                                                      vobj)
            else:
                solutions = self._search_solution(solutions, local_assigns)

            if self._stop_solver(solutions):
                return solutions

            self._pop_extra()

        return solutions


    def get_solution(self, problem_spec, solve_type=SolveType.ONE):

        self._spec = problem_spec
        self._nbr_variables = len(self._spec.variables)

        if self._arc_con:
            self._arc_con.set_pspec(problem_spec)
        self._solve_type = solve_type

        solutions = self._search_solution(solutions = [], assignments = {})

        if not solutions:
            return None

        if self._solve_type == SolveType.ONE:
            return solutions[0]

        return solutions


# %% non recursive backtracking

class NonRecBacktracking(Solver):
    """A backtracking solver that does not use recursion."""

    def __init__(self, forward_check=False, problem_spec=None):
        """Store some variables common to most methods.
        They still need to be passed to base class and var chooser.

        _assignments the current list of assignments

        _unassigned  a list of unassigned variables

        _queue       a queue of tuples: var name, values, unassigned vars:

                     var name: a variable with a current assignment

                     values: remaining values for var name (untested)

                     unasigned vars: the variables that were unassigned
                     when var name was assigned
        """

        super().__init__(forward_check, problem_spec)

        self._assignments = {}
        self._unassigned = []
        self._queue = col.deque()


    def _choose_new_var(self):
        """Choose a new variable for assignment updating the unassigned list.
        Adjust the variable domains if we pop from the queue.

        Return var_name and values for the variable."""

        if len(self._assignments) == self._nbr_variables:
            var_name, values, self._unassigned = self._queue.pop()

            if self._forward:
                for tempv in self._unassigned:
                    tempv.pop_domain()

        else:
            self._unassigned = [var
                                for v_name, var in self._spec.variables.items()
                                if v_name not in self._assignments]
            vobj = self._chooser.choose(self._unassigned,
                                        self._spec,
                                        self._assignments)

            var_name = vobj.name
            values = vobj.get_domain()[:]
            self._unassigned.remove(vobj)

        return var_name, values


    def _choose_new_assign(self, var_name, values):
        """Choose a new value for var_name from values updating
        assignments. If there are no values left for var_name,
        check the queue for more variables.

        Return var_name and values if an assignment can be made,
        else False."""

        if not values:

            del self._assignments[var_name]

            while self._queue:
                self._pop_extra()
                var_name, values, self._unassigned = self._queue.pop()

                if self._forward:
                    for tempv in self._unassigned:
                        tempv.pop_domain()

                if values:
                    break

                del self._assignments[var_name]

            else:   # if not queue and not values
                return False

        self._assignments[var_name] = values.pop()
        return var_name, values


    def _still_consistent(self, var_name):
        """Test the new assignment to see if the solution is still
        consistent. If consistent, adjust the domain histories
        as appropriate."""

        if not self._assign_extra(var_name, self._assignments[var_name]):
            return False

        if not self._consistent(var_name, self._assignments):
            return False

        if self._forward:
            for tempv in self._unassigned:
                tempv.push_domain()

        still_good = True
        if self._arc_con:
            still_good = self._arc_con.arc_consist(self._assignments)

        if still_good and self._forward_check(var_name, self._assignments):
            return True

        if self._forward:
            for tempv in self._unassigned:
                tempv.pop_domain()

        return False


    def _solution_iter(self):
        """Search for solutions. Do as iterator to simplify keeping
        our place."""

        self._assignments = {}
        self._unassigned = []
        self._queue = col.deque()

        while True:

            if len(self._assignments) == self._nbr_variables:
                if self._spec.usol_cnstr:
                    self._spec.usol_cnstr.solution_found(self._assignments)

                yield self._assignments.copy()
                if not self._queue:
                    return

            var_name, values = self._choose_new_var()

            while True:

                # might pop the queue and assign a new val to prev asign'ed var
                rval = self._choose_new_assign(var_name, values)
                if not rval:
                    return

                var_name, values = rval

                if self._still_consistent(var_name):
                    break

            self._queue.append((var_name,
                                values.copy(),
                                self._unassigned.copy()))


    def get_solution(self, problem_spec, solve_type=SolveType.ONE):

        self._spec = problem_spec
        self._nbr_variables = len(self._spec.variables)

        if self._arc_con:
            self._arc_con.set_pspec(problem_spec)
        self._solve_type = solve_type

        if self._solve_type == SolveType.ONE:
            return next(self._solution_iter(), None)

        if self._solve_type == SolveType.ALL:
            return list(self._solution_iter()) or None

        if self._solve_type == SolveType.MORE_THAN_ONE:
            solver_iter = self._solution_iter()
            sol1 = next(solver_iter, None)
            if sol1:
                sol2 = next(solver_iter, None)
                if sol2:
                    return [sol1, sol2]
            return [sol1]

        assert False, "Unknown solver type"


# %% bare non recursive backtracker

class BareNRBack(NonRecBacktracking):
    """A backtracking solver that does not use recursion
    AND does not check for extra data, forward checking
    or arc consistency checking.
    This eliminates testing if the option is used."""


    @NonRecBacktracking.arc_con.setter
    def arc_con(self, value):
        """raise exception -- property may not be set"""
        if value:
            raise ValueError("BareNRBack does not support arc consistency.")

    @NonRecBacktracking.forward.setter
    def forward(self, value):
        """raise exception -- property may not be set"""
        if value:
            raise ValueError("BareNRBack does not support forward checking.")

    def enable_forward_check(self):
        """raise exception -- property may not be set"""
        raise ValueError("BareNRBack does not support forward checking.")

    @NonRecBacktracking.extra.setter
    def extra(self, value):
        """raise exception -- property may not be set"""
        if value:
            raise ValueError("BareNRBack does not support extra data.")


    def _choose_new_assign(self, var_name, values):
        """Choose a new value for var_name from values updating
        assignments. If there are no values left for var_name,
        check the queue for more variables.

        Return var_name and values if an assignment can be made,
        else False."""

        if not values:
            del self._assignments[var_name]

            while self._queue:
                var_name, values, self._unassigned = self._queue.pop()
                if values:
                    break

                del self._assignments[var_name]

            else:   # if not queue and not values
                return False

        self._assignments[var_name] = values.pop()
        return var_name, values


    def _still_consistent(self, var_name):
        """Test the new assignment to see if the solution is still
        consistent."""

        return self._consistent(var_name, self._assignments)



# %% Minimum Conflicts Solver

class MinConflictsSolver(Solver):
    """Search for a solution by choosing a random solution
    then refining it by choosing a variable that violates a constraint,
    then choosing a new value for that variable that minimizes the
    number of conflicts. Repeat until solution found (or max steps)."""


    def __init__(self, steps=1000):
        """Save the number of steps."""
        super().__init__()
        self._steps = steps


    def _count_satisfied(self, assigns, vname, value):
        """Count the number constraints that are satisfied for
        vname with the partial assignments (assign + vname : value)"""

        satis = 0
        for constraint in self._spec.cnstr_dict[vname]:

            const_assign = self._select_assignments(constraint.get_vnames(),
                                                    assigns | {vname : value})
            if constraint.satisfied(const_assign):
                satis += 1

        return satis


    def _choose_init_assigns(self):
        """Greedily choose the initial assignments."""

        assignments = None

        for vname, vobj in self._spec.variables.items():

            if not assignments:
                assignments = {vname : vobj.get_domain()[0]}
                continue

            max_sat_key = ft.partial(self._count_satisfied,
                                     assignments, vname)

            assignments |= {vname :
                            max(vobj.get_domain(), key = max_sat_key)}

        return assignments


    def _count_conflicts(self, assigns):
        """Count the number constraints that are NOT satisfied.
        The number of conflicts will be minimized."""

        score = 0
        for constraint in self._spec.constraints:

            const_assign = self._select_assignments(constraint.get_vnames(),
                                                    assigns)
            if not constraint.satisfied(const_assign):
                score += 1
        return score


    def _choose_new_value(self, var_name, assignments):
        """Update the assignments with a new value for var_name
        that minimizes the number of constraint violations.

        Keep the current value if all other values have more
        constraint violations."""

        value = assignments[var_name]

        domain = self._spec.variables[var_name].get_domain()[:]
        domain.remove(value)

        mincount = self._count_conflicts(assignments)
        minvalues = [value]

        for value in domain:
            assignments[var_name] = value

            count = self._count_conflicts(assignments)

            if count == mincount:
                minvalues += [value]

            elif count < mincount:
                mincount = count
                minvalues = [value]

        value = random.choice(minvalues)
        assignments[var_name] = value


    def _search_solution(self):
        """Execute the search algorithm."""

        assignments = self._choose_init_assigns()

        consistent = False
        for _ in range(self._steps):

            if self._all_consistent(assignments):
                consistent = True
                break

            conflict_vars = [vname
                             for vname, vobj in self._spec.variables.items()
                             if not self._consistent(vname, assignments)]

            var_name = random.choice(conflict_vars)

            self._choose_new_value(var_name, assignments)

        if consistent:
            return assignments

        print('Exeeded search steps.')
        return None


    def get_solution(self, problem_spec, solve_type=SolveType.ONE):
        """Only one solution is returned."""

        self._spec = problem_spec
        self._nbr_variables = len(self._spec.variables)
        self._solve_type = solve_type

        if self._solve_type != SolveType.ONE:
            raise NotImplementedError(
                'MinConflictsSolver will only find one solution.')

        return self._search_solution()
