# -*- coding: utf-8 -*-
"""Boolean Constraints in Two Variables

Each constraint is
    var1 == val1  op  var2 == val2

where op is one of Nand, Or, IfThen, Xor or Nxor.

Only these five are defined here. The table below shows
how to implement all 16 boolean operators with more
primitive constraints.

     Operation       Boolean             Constraint to Use

 1.  False                               unsolvable problem
 2.  True                                no need to include

 3.  Transfer        A                   InValues
 4.  Transfer        B                   InValues

 5.  NOT             not A               NotInValues
 6.  NOT             not B               NotInValues

 7.  AND             A and B             InValues and InValues

 8.  NAND            not(A and B)        Nand

 9.  OR              A or B              Or
                                         OrCList (>= two operands,
                                                  but no preproc or forward)

10.  NOR             not(A or B)
                      = not A and not B  NotInValues and NotInValues

11.  Implication     if A then B
                      = not A or B       IfThen
12.  Implication     if B then A
                      = not B or A       IfThen

13.  Inhibition      A but not B
                      = A and not B      InValues and NotInValues
14.  Inhibition      B but not A
                      = B and not A      NotInValues and InValues

15.  XOR             A xor B
                      =  A != B          Xor
                                         OneOfCList (>= two operands,
                                                     but no preproc or forward)

16.  XNOR            not(A xor B)        Nxor


Created on Wed May  3 07:19:36 2023
@author: Ann"""


from . import cnstr_base


class BoolBinOpConstraint(cnstr_base.Constraint):
    """A constraint that saves two initial values."""

    def __init__(self, val1, val2):

        super().__init__()
        self._val1 = val1
        self._val2 = val2

    def __repr__(self):
        return self.__class__.__name__  + f'({self._val1}, {self._val2})'

    def set_variables(self, vobj_list):
        """Confirm that the provided values are in the appropriate
        domains."""

        super().set_variables(vobj_list)

        if self._val1 not in self._vobjs[0].get_domain():
            raise cnstr_base.ConstraintError(
                f'{self}: {self._val1} not in domain of {self._vnames[0]}')

        if self._val2 not in self._vobjs[1].get_domain():
            raise cnstr_base.ConstraintError(
                f'{self}: {self._val2} not in domain of {self._vnames[1]}')

    @staticmethod
    def reduce_to_required(unassigned_var, required_val):
        """Reduce the domain of the unassigned variable to
        the required value.

        return False if a domain was eliminated.
        True if nothing was changed.
        A set with the variable name in it, if a change was made."""

        rval = True
        for value in unassigned_var.get_domain_copy():
            if value != required_val:

                rval = {unassigned_var.name}
                if not unassigned_var.hide(value):
                    return False

        return rval


class Nand(BoolBinOpConstraint):
    """Nand: not (a and b)
    => not (var1 == val1 and var2 == val2)
    => var1 != val1 or var2 != val2."""

    def satisfied(self, assignments):
        """If all vals assigned do test,
        otherwise return True to keep doing assignments."""

        if len(assignments) == self._params:
            vals = list(assignments.values())
            return self._val1 != vals[0] or self._val2 != vals[1]
        return True

    @staticmethod
    def _forward_one_side(vala, vobja):
        """If the value is in the object's domain, remove it,
        returning False (if domain exhausted) or varname.
        Otherwise return True."""

        if vala in vobja.get_domain():
            return vobja.hide(vala) and {vobja.name}

        return True

    def forward_check(self, assignments):
        """If exactly one of the two variables is assigned to the
        expected value, removed the specified value from the other
        variable."""

        if not assignments or len(assignments) == self._params:
            return True

        var, val = list(assignments.items())[0]

        if var == self._vnames[0] and self._val1 == val:
            return self._forward_one_side(self._val2, self._vobjs[1])

        if var == self._vnames[1] and self._val2 == val:
            return self._forward_one_side(self._val1, self._vobjs[0])

        return True


class Or(BoolBinOpConstraint):
    """Or: a or b
    => var1 == val1 or var2 == val2"""

    def satisfied(self, assignments):
        """If all vals assigned do test,
        otherwise return True to keep doing assignments."""

        if len(assignments) == self._params:
            vals = list(assignments.values())
            return self._val1 == vals[0] or self._val2 == vals[1]
        return True

    def forward_check(self, assignments):
        """If exactly one of the two variables is assigned to the
        wrong value, reduce the domain of the other to the
        required value."""

        if not assignments or len(assignments) == self._params:
            return True

        var, val = list(assignments.items())[0]

        if var == self._vnames[0] and self._val1 != val:
            return self.reduce_to_required(self._vobjs[1], self._val2)

        if var == self._vnames[1] and self._val2 != val:
            return self.reduce_to_required(self._vobjs[0], self._val1)

        return True


class IfThen(BoolBinOpConstraint):
    """IfThen (also called implication): if a then b
    => not a or b
    => var1 != val1 or var2 == val2"""

    def satisfied(self, assignments):
        """Ff all vals assigned do test,
        otherwise return True to keep doing assignments."""

        if len(assignments) == self._params:
            vals = list(assignments.values())
            return self._val1 != vals[0] or self._val2 == vals[1]
        return True

    def forward_check(self, assignments):
        """If a is assigned and True, then b must be True,
        reduce it's domain."""

        if not assignments or len(assignments) == self._params:
            return True

        var, val = list(assignments.items())[0]

        if var == self._vnames[0] and self._val1 == val:
            return self.reduce_to_required(self._vobjs[1], self._val2)

        return True


class Xor(BoolBinOpConstraint):
    """Xor:  (a and not b) or (not a and b)
    => a != b
    => (var1 == val1) != (var2 == val2)"""

    def satisfied(self, assignments):
        """if all vals assigned do test,
        otherwise return True to keep doing assignments."""

        if len(assignments) == self._params:
            vals = list(assignments.values())
            return (self._val1 == vals[0]) != (self._val2 == vals[1])
        return True

    @staticmethod
    def _forward_one_side(assign_val, vala, valb, vobjb):
        """If the assigned value is vala, then remove valb from
        vobjb (if it's there). Otherwise, reduce vobjs domain
        to the required value (valb).
        Return True if nothing changed."""

        if vala == assign_val:
            if valb in vobjb.get_domain():
                return vobjb.hide(valb) and {vobjb.name}

            return True

        return Xor.reduce_to_required(vobjb, valb)

    def forward_check(self, assignments):
        """If exactly one of the two variables is assigned to the
        expected value, hide the other value. If exactly one of the
        variables is not assigned to the expected value, reduce the
        domain of the other to the required value."""

        if not assignments or len(assignments) == self._params:
            return True

        var, val = list(assignments.items())[0]

        if var == self._vnames[0]:
            return self._forward_one_side(val,
                                          self._val1,
                                          self._val2, self._vobjs[1])

        # assert var == self._vnames[1]
        return self._forward_one_side(val,
                                      self._val2,
                                      self._val1, self._vobjs[0])


class Nxor(BoolBinOpConstraint):
    """Nxor:  not (a xor b)
    => not((a and not b) or (not a and b))
    => bool(a) == bool(b)
    => (var1 == val1) == (var2 == val2)"""

    def satisfied(self, assignments):
        """if all vals assigned do test,
        otherwise return True to keep doing assignments."""

        if len(assignments) == self._params:
            vals = list(assignments.values())
            return (self._val1 == vals[0]) == (self._val2 == vals[1])
        return True

    @staticmethod
    def _forward_one_side(assign_val, vala, valb, vobjb):
        """If the assigned value is vala, then reduce vobjs domain
        to the required value (valb). Otherwise, remove valb from
        vobjb (if it's there).
        Return True if nothing changed."""

        if vala == assign_val:
            return Nxor.reduce_to_required(vobjb, valb)

        if valb in vobjb.get_domain():
            return vobjb.hide(valb) and {vobjb.name}

        return True

    def forward_check(self, assignments):
        """If exactly one of the two variables is assigned to the
        expected value, hide the other value. If exactly one of the
        variables is not assigned to the expected value, reduce the
        domain of the other to the required value."""

        if not assignments or len(assignments) == self._params:
            return True

        var, val = list(assignments.items())[0]

        if var == self._vnames[0]:
            return self._forward_one_side(val,
                                          self._val1,
                                          self._val2, self._vobjs[1])

        # assert var == self._vnames[1]
        return self._forward_one_side(val,
                                      self._val2,
                                      self._val1, self._vobjs[0])
