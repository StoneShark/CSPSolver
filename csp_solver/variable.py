# -*- coding: utf-8 -*-
"""Variables for the constraint problem.

Each has a domain and a mechanism for managing temporarily
reducing the domain while solving a problem.

Created on Wed May  3 07:31:25 2023
@author: Ann"""


import collections as col


class Variable:
    """A variable and it's domain (value list).

    The same value list might be provided to multiple variables,
    so use list to make a shallow copy (and convert any iterable
    that might not be a list).

    name - must be hashable, used for dicitonary keys.

    _domain - list values possible for variable. Preprocess on a
    contraint permanently removes values. Forward checking temporarily
    hides values from the domain.

    _hidden - list of values hidden since creation or the last push_domain.

    -nbr_remain - a stack (list) of the number of variables remaining
    in the domain, when push is called. Allows pop to compute how many
    values to restore."""

    def __init__(self, name, values):

        self.name = name
        self._domain = list(values)
        self._hidden = []
        self._nbr_remain = col.deque()


    def nbr_values(self):
        """return the number of remaining values.
        Zero values means the variable has been overconstrained."""
        return len(self._domain)


    def get_domain(self):
        """Return the domain values. If using in a list which will
        change the domain be sure to do a shallow copy with [:]."""

        return self._domain


    def set_domain(self, values):
        """Set the domain list and clear the state data to
        assure consistency.
        This is safe during preprocessing, but not at any other time."""

        self._domain = list(values)
        self._hidden = []
        self._nbr_remain.clear()


    def remove_dom_val(self, value):
        """Remove the value from the domain. This is permanent.
        Must have same proto/return as hide.

        Return True if there are domain values left, False otherwise."""

        self._domain.remove(value)
        return bool(self._domain)


    def reset_dhist(self):
        """Reset the domain history by returning any hidden values.
        Reset the local state variables."""

        self._domain += self._hidden
        self._hidden = []
        self._nbr_remain.clear()


    def push_domain(self):
        """Push a domain history.
        Record the number of values in domain."""

        self._nbr_remain.append(len(self._domain))


    def pop_domain(self):
        """Pop the domain history.
        Restore values that were hidden since the last push."""

        diff = self._nbr_remain.pop() - len(self._domain)
        if diff:
            self._domain += self._hidden[-diff:]
            del self._hidden[-diff:]


    def hide(self, value):
        """Temporarily hide a value from the domain by adding it to the
        hidden list and removing it from the domain.
        Must have same proto/return as remove_dom_val.

        Return True if there are domain values left, False otherwise."""

        self._domain.remove(value)
        self._hidden += [value]

        return bool(self._domain)
