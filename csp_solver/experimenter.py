# -*- coding: utf-8 -*-
"""Experimenter - parses command line arguements to perform actions

Two interfaces are required to be passed to do_stuff:

 1. build - a function that gets a problem which must add the
    variables and constraints for the problem.

    Aternatively, a list of build functions can  be provided.
    If they are an additional option is provided to select
    which build.

 2. show_solution - a function that gets a solution (as an
    assignment dictionary) and the build index used; it
    should print an understandable version of the solution.

Created on Thu Jun 15 15:45:11 2023
@author: Ann"""


# %% imports

import argparse
import cProfile
import datetime
import sys
import textwrap
import timeit

from . import arc_consist
from . import problem
from . import solver
from . import var_chooser


# %% constants

SOLVERS = None
VAR_CHOOSERS = None
ARC_CONSIST = None

def load_class_lists():
    """Only load these when they are needed.
    Loading when importing the module does bad things in the
    test suite (i.e. there are bad classes defined)."""
    # pylint: disable=global-statement

    global SOLVERS, VAR_CHOOSERS, ARC_CONSIST

    SOLVERS = {slvr.__name__ : slvr for slvr in solver.Solver.derived()}

    VAR_CHOOSERS = {varc.__name__ : varc
                    for varc in var_chooser.VarChooser.derived()}

    ARC_CONSIST = {arc_con.__name__ : arc_con
                   for arc_con in arc_consist.ArcConIF.derived()}
    ARC_CONSIST['none'] = None


ALL = 'all'
KEEP = 'keep'
UNIQUE = 'unique'
ONE = 'one'
ON = 'on'
OFF = 'off'

DONT_SET = {KEEP, ALL}

PROFILE = 'profile'
TIMEIT_ONE = 'timeit_one'
TIMEIT = 'timeit'

TIMERS = ['none', PROFILE, TIMEIT_ONE, TIMEIT]
FORWARDS = [ON, OFF, KEEP]
SOLS = [ONE, UNIQUE, ALL]

STD_INDENT = '    '


# %% experiments

def set_forward(cargs, prob_inst):
    """Set the forward check per command line args."""

    if cargs.forward == ON:
        prob_inst.forward_check = True
    elif cargs.forward == OFF:
        prob_inst.forward_check = False


def build_the_problem(cargs, build):
    """Build the problem. Change the sovler, var_chooser,
    forward_checking and arc consistency if the args
    are specified."""

    # classes not loaded until needed
    if not SOLVERS:
        load_class_lists()

    prob_inst = problem.Problem()
    build(prob_inst)

    if cargs.solver not in DONT_SET:
        prob_inst.solver = SOLVERS[cargs.solver]()

    if cargs.var_chooser not in DONT_SET:
        # var choosers don't need to be instantiated
        prob_inst.var_chooser = VAR_CHOOSERS[cargs.var_chooser]

    if cargs.arc_consist not in DONT_SET:
        prob_inst.arc_con = ARC_CONSIST[cargs.arc_consist]()

    set_forward(cargs, prob_inst)

    return prob_inst


def print_prob_desc(cargs, build, prob_inst):
    """Print the problem parameters as built."""

    print('Build:', build.__name__)
    if cargs.solver != ALL:
        print('Solver:', prob_inst.solver_name())
    if cargs.var_chooser != ALL:
        print('Chooser:', prob_inst.var_chooser_name())
    print('Arc Consist:', prob_inst.arc_con_name())
    print('Forward check:', 'On' if prob_inst.forward_check else 'Off')
    print()


def run_the_choosers(cargs, build):
    """Run all the chooser, timing them."""

    # classes not loaded until needed
    if not VAR_CHOOSERS:
        load_class_lists()

    first = True
    for chooser in VAR_CHOOSERS.values():

        prob_inst = build_the_problem(cargs, build)
        prob_inst.var_chooser = chooser
        set_forward(cargs, prob_inst)
        if first:
            print_prob_desc(cargs, build, prob_inst)
            print('Timing each var_chooser (each might not find solution):')
            first = False

        print(f'{chooser.__name__:20}',
              f'{timeit.timeit(prob_inst.get_solution, number=1):10}')


def run_the_solvers(cargs, build):
    """Run all the sovlers, timing them."""

    # classes not loaded until needed
    if not SOLVERS:
        load_class_lists()

    first = True
    for slvr in SOLVERS.values():

        prob_inst = build_the_problem(cargs, build)
        prob_inst.solver = slvr()
        set_forward(cargs, prob_inst)
        if first:
            print_prob_desc(cargs, build, prob_inst)
            print('Timing each solver (each might not find solution):')
            first = False

        print(f'{slvr.__name__:25}',
              f'{timeit.timeit(prob_inst.get_solution, number=1):10}')


def solve_the_problem(cargs, prob_inst):
    """Solve the problem."""

    if cargs.sol_type == ALL:
        return prob_inst.get_all_solutions()

    if cargs.sol_type == UNIQUE:
        return prob_inst.more_than_one_solution()

    return prob_inst.get_solution()


def build_and_solve(cargs, build):
    """Build and solve the problem."""

    solve_the_problem(cargs, build_the_problem(cargs, build))


def print_results(show_solution, cargs, sol, bindex):
    """Decide what solutions to print."""

    if cargs.sol_type == ALL and sol:
        print(f'\nFound {len(sol)} solutions.')

    elif cargs.sol_type == UNIQUE:
        if len(sol) == 1:
            print('\nSolution is unique.')
        else:
            print('\nThere is not a unique solution.')

    elif not cargs.sol_type == ALL and sol:
        if cargs.show_n:
            print('\n')
            show_solution(sol, bindex)
        return

    else:
        print('\nNo solutions')
        return

    if cargs.show_n and len(sol) > cargs.show_n:
        print("Showing first 5 solutions:\n")

    for one_sol in sol[:cargs.show_n]:
        show_solution(one_sol, bindex)


def solve_it(cargs, build, bindex, show_solution):
    """Run the problem solver.

    The problem can only be solved once, so TIMEIT (x100)
    actually times the build and solve."""

    if cargs.timer == TIMEIT:
        print('Run time (x100):',
              timeit.timeit(lambda : build_and_solve(cargs, build),
                            number=100))
        return

    prob_inst = build_the_problem(cargs, build)
    print_prob_desc(cargs, build, prob_inst)

    if cargs.timer == PROFILE:
        cProfile.runctx('solve_the_problem(cargs, prob_inst)',
                        globals(), locals())
        return

    if cargs.timer == TIMEIT_ONE:
        print('Run time:',
              timeit.timeit(lambda : solve_the_problem(cargs, prob_inst),
                            number=1))
        return

    start = datetime.datetime.now()
    print('Start Time:', start)
    sol = solve_the_problem(cargs, prob_inst)

    print('Solve time:', datetime.datetime.now() - start)
    print_results(show_solution, cargs, sol, bindex)


# %%  define the parser


class MultilineFormatter(argparse.HelpFormatter):
    """We want paragraphs in the description!
    From:  https://stackoverflow.com/users/4672928/flaz14
    on: https://stackoverflow.com/questions/3853722
    """

    def _fill_text(self, text, width, indent):

        text = self._whitespace_matcher.sub(' ', text).strip()

        paragraphs = text.split('|n ')
        out_text = ''

        for paragraph in paragraphs:
            fpara = textwrap.fill(paragraph, width,
                                  initial_indent=indent,
                                  subsequent_indent=indent) + '\n\n'
            out_text += fpara

        return out_text


def define_parser(nbr_builds):
    """Define the command line arguements."""

    if not SOLVERS:
        load_class_lists()

    parser = argparse.ArgumentParser(
        usage='%(prog)s [--help] [options]',
        description="""%(prog)s uses
        an experimenter that allows setting many of the
        CSP options from the command line. Error checking is not
        very robust.
        |n
        If --timer is used, the answer is not printed. Take care
        that the combination of solver parameters actually finds
        an answer before interpreting the timer results.
        |n
        If --timer is not used, the 'wall clock' time to compute the
        solution will be shown.
        |n
        Only one 'all' value may be used: --solver, --var_chooser,
        --build, or --sol_type.
        """,
        formatter_class=MultilineFormatter)

    parser.add_argument('--solver', action='store',
                        choices=list(SOLVERS.keys()) + [ALL, KEEP],
                        default=KEEP,
                        help="""Select the solver.
                        'keep' does not change the solver from the
                        build function.
                        'all' will report the solve time for each of
                        solvers (the solutions are not reported,
                        none might have been found).
                        Default: %(default)s""")

    parser.add_argument('--var_chooser', action='store',
                        choices=list(VAR_CHOOSERS.keys()) + [ALL, KEEP],
                        default=KEEP,
                        help="""Select the variable chooser.
                        'keep' does not change the var_chooser
                        from the build function.
                        'all' will report the solve time for each
                        of the choosers (the solutions are not reported,
                        none might have been found).
                        Default: %(default)s""")

    parser.add_argument('--arc_consist', action='store',
                        choices=list(ARC_CONSIST.keys()) + [KEEP],
                        default=KEEP,
                        help="""Select the arc consistency helper.
                        'keep' does not change the from the build fucntion.
                        'none' to disable the arc consistency check.
                        Default: %(default)s""")

    parser.add_argument('--forward', action='store',
                        choices=FORWARDS, default=KEEP,
                        help="""Enable the forward checking with 'on';
                        disable with 'off'. Use as built with 'keep'.
                        Default: %(default)s""")

    parser.add_argument('--timer', action='store',
                        choices=TIMERS, default='none',
                        help="""Choose a timer.
                        When using a timer the solution is not printed.
                        'profile' and 'timeit_one' display the time to
                        solve the problem not including the build function.
                        'timeit' displays the time to execute the
                        build function and the solver 100 times.
                        Default: %(default)s""")

    parser.add_argument('--sol_type', action='store',
                        choices=SOLS, default='one',
                        help="""Select solve approach:
                            'one' find one solution, 'unique' determine if
                            there is more than one solution, 'all' find all
                            solutions.
                            Default: %(default)s""")

    parser.add_argument('--build', action='store',
                        choices=[str(i) for i in range(1,nbr_builds+1)] + [ALL],
                        default='1',
                        help="""Which of multiple build functions should be run.
                        This option is limited to the number of build functions
                        provided to the experimenter. 'all' will run all builds.
                        Default: %(default)s""")

    parser.add_argument('--show_n', action='store', default=5,
                        type=int,
                        help="""0 will prevent any solution from being
                        printed.  If multiple solutions found, show at
                        most n of them (only if --all or --unique).
                        Default: %(default)s""")

    return parser


def parse_args(nbr_builds):
    """Define the command line parser and use it to build
    cargs."""

    parser = define_parser(nbr_builds)

    try:
        cargs = parser.parse_args()
    except argparse.ArgumentError:
        parser.print_help()
        sys.exit()

    if (cargs.sol_type in (ALL, UNIQUE)
            and cargs.solver == solver.MinConflictsSolver.__name__):
        print('MinConflictsSolver can only find one solution.')
        cargs.sols = ONE

    if (cargs.solver == solver.MinConflictsSolver.__name__
            and cargs.var_chooser != KEEP):
        print("Var chooser isn't used with MinConflictSolver.")
        cargs.var_chooser = KEEP

    if (cargs.forward == OFF
            and cargs.arc_consist != KEEP
            and ARC_CONSIST[cargs.arc_consist]):
        print("Arc Consistency behavior is not well defined without --forward on.")

    if cargs.build == ALL and nbr_builds == 1:
        cargs.build = '1'

    all_count = [cargs.build == ALL,
                 cargs.var_chooser == ALL,
                 cargs.solver == ALL,
                 cargs.sol_type == ALL].count(True)
    if all_count > 1:
        print("Only one ALL type option may be selected.")
        sys.exit()

    return cargs


# %%  do_stuff (main)

def print_doc_str(doc_str):
    """Print the doc str removing any leading indent"""

    if not doc_str:
        return

    for line in doc_str.splitlines():
        if line[:4] == STD_INDENT:
            print(line[4:])
        else:
            print(line)
    print()


def do_stuff(build_param, show_solution):
    """The main interface to the experimenter.
    Check the parameters, parse the command line arguements, and
    then do something."""

    nbr_builds = 1
    if isinstance(build_param, list):
        nbr_builds = len(build_param)

    elif not callable(build_param) or not callable(show_solution):
        raise ValueError(
            'Usage:  do_stuff(build_func or list of build_funcs, show_func)')

    cargs = parse_args(nbr_builds)

    if cargs.build == ALL:
        for bindex, build in enumerate(build_param):
            print_doc_str(build.__doc__)
            solve_it(cargs, build, bindex, show_solution)
            print('\n')
        return

    if isinstance(build_param, list):
        build = build_param[int(cargs.build) - 1]
    else:
        build = build_param

    print_doc_str(build.__doc__)

    if cargs.solver == ALL:
        run_the_solvers(cargs, build)
        return

    if cargs.var_chooser == ALL:
        run_the_choosers(cargs, build)
        return

    solve_it(cargs, build, int(cargs.build) - 1, show_solution)
