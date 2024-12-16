# CSP Solver #

The Constraint Satifaction Problem (CSP) Solver contains classes to represent and experiment with CSP problems. 

A CSP is defined by:

1. a collection of variables each with a domain of possible values
2. a series of constraints on those variables and possible assigned values

A solution to a CSP is the list of variables with value assignments.

## Experimenter ##

The CSP Solver includes an experimenter that can be used to evaluate different solution approaches to a problem via command line arguments. The solvers, variable chooser, arc consistency checker may be selected. Several profiling (timing) options are supported. The experimenter can be used to determine if there is a unique solution to the problem, can find one solution to the problem, or can find all the solutions to the problem.

To evaluate different representations of a problem, several may be provided to the experimenter for comparison.

The experimenter is invoked by calling

	experimenter.do_stuff(build_funcs, show_func)

where **build_funcs** is either a single build function or a list of build functions.
Each build function gets a pre-built csp\_solver. Problem and the 
build function should add variables and their domains, and any constraints to the problem. The solver, variable chooser and arc consistency checker can be set to defaults for the problem. The alternate build functions can be different representations of the same problem or different problems.

and where **show_func** is a function that when given a dictionary whose keys are variables and values are their assignments displays a solution. 

## Constraints ##

The following constraints are provided:

- BoolFunction
- AllDifferent
- AllEqual
- MaxSum
- ExactSum
- MinSum
- InValues
- NotInValues
- AtLeastNNotIn
- OneOrder
- LessThan
- LessThanEqual

Five more constraints are provided to provide a full set of boolean constraints (all 16, see intro comment in [cnstr_binary.py](https://github.com/StoneShark/CSPSolver/blob/main/csp_solver/constraint/cnstr_binary.py). Each is of the form var1 == val1  op  var2 == val2:

- NAND
- OR
- IfThen
- XOR
- NXOR

Constraints that behave somewhat like sets are available. These allow constraining the number of values assigned to a group of variables:

- ExactlyNIn
- AtLeastNIn
- AtMostNIN
- AtLeastNNotIn

Additionally, a grouping of constraints may be applied with list constraints. The constraints are ANDed in a CSP; these constraints allow creating ORed relationships. List constraints should not be used if the problem can stated without them; they do not support preprocessing, forward checking, or arc consistency checking.

- AtLeastNCList - require only a subset of the constraints be met
- AtMostNCList - require that not all of the constraints be met
- NOfCList - require an exact number of constraints be met
- OneOfCList - require exactly one of the constraints be met
- OrCList - require at least one of the constraints be met

## Solvers ##

Three solvers are provided:

- Backtracking
- NonRecBacktracking
- MinConflictsSolver

## Variable Chooser ##

Choosing the next variable to assign can greatly improve solver time. The following are included:

- UseFirst - choose the variables in the order they were created. This is advantageous in that it does not incur extra decision making.
- MaxVarName - choose the variable with the longest variable name. It's a cheesy but easy way to control the order of variable selection.
- MinDomain - choose the variable with the smallest remaining domain next.
- MaxDegree - choose the variable that is used in the most constraints next.
- DegreeDomain - select the variable with the smallest domain from those with the largest degree (most constraints).  Sort order is maximum degree then minimum domain. This is the default var_chooser.
- DomainDegree - select the variable with the largest domain from those with the smalled domain. Sort order is minimum domain then maximum degree.
- MaxAssignedNeighs - choose the variable listed in constraints along with other variables (neighbors) that have the most assigned values.

## Compatibility ##
CSP Solver requires only standard python 3.12 or later.

A makefile provides some developement scripts. A couple optional targets in the makefile use grep. Pytest is the test environment.
