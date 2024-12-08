# -*- coding: utf-8 -*-
"""Interface for storage of extra data in a constraint problem.

Created on Sun Jul  2 18:16:34 2023
@author: annda"""


import abc


class ExtraDataIF(abc.ABC):
    """The interface definitions for the extra data option
    for the solver.

    assign -  called immediately after an assignment but
    before any constraint methods are called.

    pop - called if assign return True and a subsequent
    constraint method found a conflict."""

    @abc.abstractmethod
    def assign(self, var, val):
        """Reflect assigning val to var in the extra data.

        The solver will call this each time it makes an assignement.

        Return False if a conflict is detected, True otherwise."""


    @abc.abstractmethod
    def pop(self):
        """Undo the effects of the last assign call."""
