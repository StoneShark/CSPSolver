# -*- coding: utf-8 -*-
"""Interface for storage of extra data in a constraint problem.

This maybe a second representation of the problem or simply
maybe a scatchpad for extra notes.

The assign method can detect inconsistencies and if does it
should not store the vname/value and should return False.

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
        This might be an update to an already assigned variable.

        The solver will call this each time it makes an assignement.

        Return False if a conflict is detected, True otherwise.
        When returning False do not add the value!"""


    @abc.abstractmethod
    def pop(self):
        """Undo the effects of the last assign call."""
