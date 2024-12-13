# -*- coding: utf-8 -*-
"""Collect the constraint problem specification into a dataclass.

Created on Thu May 18 06:23:28 2023
@author: Ann"""


# %% imports

import collections as col
import dataclasses as dc

from . import constraint as cnstr
from . import list_constraint as lcnstr
from . import variable


# %% prob spec

@dc.dataclass
class ProblemSpec:
    """The data for the problem specification.

    Data class fields include:
        variables is a dictionary of var_name: var_obj.

        contraints is a list of constraints.

        cnstr_dict is a dictionary created before calling the solver
        which supports lookup of constraints which use a particular
        variable:
           var_name : constraints with var in them
    """

    variables: dict = dc.field(default_factory=dict)

    constraints: list = dc.field(default_factory=list)

    cnstr_dict: col.defaultdict = dc.field(
        default_factory=lambda : col.defaultdict(list))


    def add_variable(self, var_name, values):
        """Add a variable and it's domain to the problem."""

        if var_name in self.variables:
            raise ValueError('var name not unique')

        self.variables[var_name] = variable.Variable(var_name, values)


    def add_variables(self, variables, domain):
        """Add multiple variables and their domains to the problem.
        Variable creation copies the domain."""

        for var_name in variables:
            self.add_variable(var_name, domain)


    def _finish_constraint(self, constraint, variables):
        """Convert functions in BoolFunction objects and add the
        variables to the constraint."""

        if not isinstance(constraint, cnstr.Constraint):
            if callable(constraint):
                constraint = cnstr.BoolFunction(constraint)
            else:
                raise ValueError(
                    'Constaint must be subclass of Contraint or callable.')

        if constraint.get_vnames():
            raise ValueError(
                f'{constraint} has variables assigned (constraint reused?).')

        constraint.set_variables([self.variables[vname]
                                  for vname in variables])

        return constraint


    def add_constraint(self, constraint, variables):
        """Add a constraint and associated variables to the problem."""

        constraint = self._finish_constraint(constraint, variables)
        self.constraints += [constraint]


    def set_list_constraints(self, list_con, con_var_pairs):
        """Add a list constraint.

        list_con: ListConstraint
        con_var_pairs: list of tuples (constraint, variables)
        """

        if not isinstance(list_con, lcnstr.ListConstraint):
            if isinstance(list_con, cnstr.Constraint):
                raise ValueError(
                    'Use add_constraint for individual Constraints')
            raise ValueError('Unexpected object type in set_list_constraint.')

        clist = []
        for constraint, variables in con_var_pairs:
            clist += [self._finish_constraint(constraint, variables)]

        list_con.set_constraints(clist)
        self.constraints += [list_con]


    def natural_numbers_required(self):
        """Collect the variables referenced in constraints that require
        natural numbers. Check their domains for compliance."""

        nat_nbr_vars = set()
        for constraint in self.constraints:
            if constraint.NAT_NBR_DOMAIN:
                nat_nbr_vars.update(constraint.get_vnames())

        for vname in nat_nbr_vars:
            if any(dval < 0 for dval in self.variables[vname].get_domain()):
                msg = 'Constraints used require Natural Numbers domains' + \
                     f' (>= 0). See {vname}.'
                raise ValueError(msg)


    def prepare_variables(self):
        """Preprocess the constraints.

        If the preprocessor fully handled the constraint, remove it.
        Build the constraint dictionary."""

        for constraint in self.constraints[:]:

            if constraint.preprocess():
                self.constraints.remove(constraint)

            else:
                for vname in constraint.get_vnames():
                    self.cnstr_dict[vname] += [constraint]
