# -*- coding: utf-8 -*-
"""
Created on Tue Jun 20 05:42:11 2023

@author: Ann
"""


import csp_solver as csp


def make_vars(pairs):
    """Given a list of name, domain pairs
    return a list of variable objects."""

    return [csp.Variable(name, dom) for name, dom in pairs]


class ExtraData(csp.extra_data.ExtraDataIF):
    """A class that meet the IF but does nothing"""
    def assign(self, var, val):
        pass

    def pop():
        pass
