# -*- coding: utf-8 -*-
"""Bring the constraint pieces together.
They were in one file until they got too big.

Created on Sat Jun 17 10:57:05 2023
@author: Ann"""

# collect all the constraints into one module
# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

from .cnstr_base import *
from .cnstr_binary import *
from .cnstr_concrete import *
from .cnstr_natnbrs import *
from .cnstr_sets import *
from .cnstr_unique import *
