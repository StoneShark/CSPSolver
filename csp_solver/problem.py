# -*- coding: utf-8 -*-
"""Problem is the main object for a constraint problem.

A Problem has
    Solver object: the algorithm to solver the problem.
    ProblemSpec object: all of the data associated with the problem.

Use the interface functions to add variables and their domains
and the list of constraints.

Three additional features are provided:

    forward propogation of domain reduction
    arc consistency checking
    "extra data" as a scratch pad for data associated with the problem

Three functions provide provide solutions:
    get_solution
    get_all_solutions
    more_than_one_solution

Created on Wed May  3 07:45:13 2023
@author: Ann"""

# %% imports

from . import problem_spec
from . import solver


# %% problem

class Problem:
    """A constraint propagation problem, defined by a series of
    variables and their domains, plus a list of contraints."""

    def __init__(self, my_solver=None):
        """Init the problem."""

        self._solver = my_solver if my_solver else solver.Backtracking()
        self._spec = problem_spec.ProblemSpec()


    @property
    def pspec(self):
        """Return the problem spec.
        It's best not use this for anything other than reference;
        that is, don't change anything except with other interface
        functions."""
        return self._spec


    @property
    def solver(self):
        """Return the solver."""
        return self._solver

    @solver.setter
    def solver(self, new_solver):
        """Set the solver but keep the selected var_chooser, arc_con
        and extra representation."""

        if not isinstance(new_solver, solver.Solver):
            raise ValueError('solver must be built on solver.Solver')

        chooser = self._solver.chooser
        arc_con = self._solver.arc_con
        forward = self._solver.forward
        extra = self._solver.extra

        self._solver = new_solver

        self._solver.chooser = chooser
        self._solver.arc_con = arc_con
        self._solver.forward = forward
        self._solver.extra = extra

    def solver_name(self):
        """Return the name of the solver."""
        return self._solver.__class__.__name__


    @property
    def var_chooser(self):
        """Return the chooser from the solver."""
        return self._solver.chooser

    @var_chooser.setter
    def var_chooser(self, chooser):
        """Set the variable chooser in the selected solver.
        Can either be an instance of VarChooser or the class."""

        self._solver.chooser = chooser

    def var_chooser_name(self):
        """Return the name of the var_chooser."""
        return self._solver.chooser.get_name()


    @property
    def arc_con(self):
        """Return the arc_con property from the solver."""
        return self._solver.arc_con

    @arc_con.setter
    def arc_con(self, arc_con):
        """Set the arc consistency helper."""

        self._solver.arc_con = arc_con
        self._solver.arc_con.set_pspec(self._spec)

    def arc_con_name(self):
        """Return a printable name for arc_con."""

        arc_con = self._solver.arc_con
        return arc_con and arc_con.__class__.__name__


    @property
    def extra_data(self):
        """Return the extra property from the solver."""
        return self._solver.extra

    @extra_data.setter
    def extra_data(self, extra):
        """Give the solver the extra data repreresentation."""

        self._solver.extra = extra


    @property
    def forward_check(self):
        """Return the forward status from the solver."""
        return self._solver.forward

    @forward_check.setter
    def forward_check(self, value):
        """Set the forward check in the solver."""
        self._solver.forward = value

    def enable_forward_check(self):
        """Enable the forward checking in the solver."""

        self._solver.enable_forward_check()


    def add_variable(self, var_name, values):
        """Add a variable and it's domain to the problem."""

        self._spec.add_variable(var_name, values)


    def add_variables(self, variables, domain):
        """Add multiple variables and their domain to the problem.
        Variable creation copies the domain."""
        self._spec.add_variables(variables, domain)


    def add_constraint(self, constraint, variables):
        """Add a constraint and associated variables to the problem."""

        self._spec.add_constraint(constraint, variables)


    def add_list_constraint(self, list_con, con_var_pairs):
        """Add a list constraint.

        Example:
            problem.add_list_constraint(AtLeastNCList(2, False),
                                        [(lambda a, b : a*2 == b, ['a', 'b']),
                                         (MaxSum(4), ['a', 'b', 'c']),
                                         (AllDifferent(), ['a', 'd', 'f'])]
        """

        self._spec.add_list_constraint(list_con, con_var_pairs)


    def set_unique_sol_constraint(self, constraint, variables):
        """Set the unique solution constraint."""

        self._spec.set_unique_sol_constraint(constraint, variables)


    def get_solution(self):
        """Call the solver to return a solution to the problem."""

        self._spec.natural_numbers_required()
        self._spec.prepare_variables()
        return self._solver.get_solution(self._spec, solver.SolveType.ONE)


    def get_all_solutions(self):
        """Call the solver to return all solutions to the problem."""

        self._spec.natural_numbers_required()
        self._spec.prepare_variables()
        return self._solver.get_solution(self._spec, solver.SolveType.ALL)


    def more_than_one_solution(self):
        """Only care if there is one solution or more than one
        solution."""

        self._spec.natural_numbers_required()
        self._spec.prepare_variables()
        return self._solver.get_solution(self._spec,
                                         solver.SolveType.MORE_THAN_ONE)


    def print_domains(self):
        """A debugging function to print out the variable names and
        their domains."""

        for name, vobj in self._spec.variables.items():
            print(name, vobj.get_domain())


    def print_constraints(self):
        """A debugging function to print out the constraints
        and their variables."""

        for con in self._spec.constraints:
            print(con, con.get_vnames())
