The examples should be run from the directory that they are in.

The experimenter is used with each unless specified otherwise.

To see the experimenter options:
         python boris.py --help


BattleBoats      solutions to the solitary battleship puzzles from
                 Games magazine. Constraints specific to the puzzle
                 are created by extending csp_solver.constraint.Constraint
                 into 8 new constraint types. A unique variable choosing
                 order is used. Several representations are provided.
                 Some are very bad--it is an NP-complete problem.
                 Example puzzles are included.

boris            an example from the web that was used to explain arc 
                 consistency.

build_sudoku     an example of using CSP to generate sudoku puzzles with
                 unique solutions.

einstein         a moderately complex CSP which uses some IfThen and
                 BoolFunction (lambda) constraints.

forbus           demonstrates four different representations of the same 
                 problem: 
                    1. naive with 3 variable sets and requiring OneOrder
                    2. better with 2 variable sets but still using lambda 
                       constraints
                    3. even better using Nand constraints
                    4. a bad representation but shows how list constraints
                       can be used

futoshiki        a CSP to solve a Futoshiki puzzle using the natural number
                 constraint LessThan.

hashi            a Hashiwokaker solver. A puzzle grid is automatically
                 converted to a CSP and solved. functools.partial is used
                 to prepare a function with extra parameters for a BoolFunction
                 constraint. var_args=True is used with that BoolFunction.

kakuros          a CSP to solve a Kakuros puzzle using the natural number
                 constraint ExactSum.

MasterMind       examples using CSP to solve master mind puzzles. After each
                 guess, new constraints are added to a CSP. Puzzles 1 to 4
                 are four position and six colors. Puzzles 5 and 6 are six 
                 positions and nine colors. These examples demonstrate
                 effective use of the SetConstraints and ListConstraints.
                 The experimenter is only used with mmind_6_exp.py.

math_ex          an example of solving a small system of equations with a 
                 CSP. The experimenter is not used in this example, but 
                 three solvers are used.

queens           a CSP to solve the 8 queens problem which shows using 
                 functools.partial to setup a BoolFunction constraint.

sendmore         a CSP to solve the send + more = money problem. Two
                 representations are shown:
                    1. a naive approach that is slow to solve
                    2. a more sophisticated approach that uses:
                          helper variables -- carries in each position
                          simple sum functions with carries
                 This example shows BoolFunction (which is created by
                 add_constraint when given a function) with var_args
                 both True and False.

sudoku           a CSP solver for Sudoku puzzles. The magic is all in the
                 definition of the AllDifferent unit lists.

