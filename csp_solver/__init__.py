# -*- coding: utf-8 -*-
"""A constraint satisfaction problem solver.

Created on Sat Dec  7 10:49:39 2024
@author: Ann"""


from .problem import Problem
from .problem_spec import ProblemSpec
from .variable import Variable

from . import constraint as cnstr

from . import arc_consist
from . import extra_data
from . import list_constraint
from . import solver
from . import var_chooser
