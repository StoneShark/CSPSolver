# -*- coding: utf-8 -*-
"""Experimenter - parses command line arguements to perform actions

Two interfaces are required to be passed to do_stuff:

 1. build - a function that gets a problem which must add the
    variables and constraints for the problem.

    Aternatively, a list of build functions can  be provided.
    If they are an additional option is provided to select
    which build.

 2. show_solution - a function that gets a solution (as an
    assignment dictionary) and should print an understandable
    version of the solution.

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

SOLVERS = {slvr.__name__ : slvr()
           for slvr in solver.Solver.__subclasses__()}

VAR_CHOOSERS = {varc.__name__ : varc
                for varc in var_chooser.VarChooser.__subclasses__()}

ARC_CONSIST = {arc_con.__name__ : arc_con()
               for arc_con in arc_consist.ArcConIF.__subclasses__()}
ARC_CONSIST['none'] = None

ALL = 'all'
KEEP = 'keep'


PROFILE = 'profile'
TIMEIT_ONE = 'timeit_one'
TIMEIT = 'timeit'

TIMERS = ['none', PROFILE, TIMEIT_ONE, TIMEIT]


# %% experiments


def run_the_choosers(cargs, build):
    """Run all the chooser, timing them."""

    print('Timing each var_chooser (each might not find solution):')
    for chooser in VAR_CHOOSERS.values():

        prob_inst = problem.Problem()

        if cargs.forward:
            prob_inst.enable_forward_check()

        build(prob_inst)
        prob_inst.var_chooser = chooser

        print(f'{chooser.__name__:20}',
              f'{timeit.timeit(prob_inst.get_solution, number = 1):10}')


def run_the_solvers(cargs, build):
    """Run all the sovlers, timing them."""

    print('Timing each solver (each might not find solution):')
    for slvr in SOLVERS.values():

        prob_inst = problem.Problem(slvr)

        if cargs.forward:
            prob_inst.enable_forward_check()

        build(prob_inst)

        print(f'{slvr.__class__.__name__:25}',
              f'{timeit.timeit(prob_inst.get_solution, number = 1):10}')


def build_the_problem(cargs, build):
    """Build the problem. Change the sovler and var_chooser if the args
    specified."""

    prob_inst = problem.Problem()

    build(prob_inst)

    if cargs.solver != KEEP:
        prob_inst.solver = SOLVERS[cargs.solver]

    if cargs.var_chooser != KEEP:
        prob_inst.var_chooser = VAR_CHOOSERS[cargs.var_chooser]

    if cargs.arc_consist != KEEP:
        prob_inst.arc_con = ARC_CONSIST[cargs.arc_consist]

    if cargs.forward:
        prob_inst.enable_forward_check()

    return prob_inst


def solve_the_problem(cargs, prob_inst):
    """Solve the problem."""

    if cargs.all:
        return prob_inst.get_all_solutions()

    if cargs.unique:
        return prob_inst.more_than_one_solution()

    return prob_inst.get_solution()


def build_and_solve(cargs, build):
    """Build and solve the problem."""

    solve_the_problem(cargs, build_the_problem(cargs, build))


def solve_it(cargs, build, show_solution):
    """Run the problem solver.

    The problem can only be solved once, so TIMEIT (x100)
    actually times the build and solve."""

    if cargs.timer == TIMEIT:
        print('Run time (x100):',
              timeit.timeit(lambda : build_and_solve(cargs, build),
                            number = 100))
        return

    prob_inst = build_the_problem(cargs, build)

    print('Build:', build.__name__)
    print('Solver:', prob_inst.solver_name())
    print('Chooser:', prob_inst.var_chooser_name())
    print('Arc Consist:', prob_inst.arc_con_name())
    print('Forward check:', 'On' if prob_inst.forward_check else 'Off')

    if cargs.timer == PROFILE:
        cProfile.runctx('solve_the_problem(cargs, prob_inst)',
                        globals(), locals())

    elif cargs.timer == TIMEIT_ONE:
        print('Run time:',
              timeit.timeit(lambda : solve_the_problem(cargs, prob_inst),
                            number = 1))
    else:

        start = datetime.datetime.now()
        print('Start Time:', start)

        sol = solve_the_problem(cargs, prob_inst)

        print('Solve time:', datetime.datetime.now() - start)

        if cargs.all:
            print(f'\nFound {len(sol)} solutions.')

        elif cargs.unique:
            if len(sol) == 1:
                print('Solution is unique.')
                show_solution(sol[0])
            else:
                print('There is not a unique solution.')

        elif sol:
            show_solution(sol)

        else:
            print('\nNo solutions')


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

    parser.add_argument('--forward', action='store_true',
                        help="""Enable forward checking. If not specified,
                        does not change from the build function.""")

    parser.add_argument('--timer', action='store',
                        choices=TIMERS, default='none',
                        help="""Choose a timer.
                        When using a timer the solution is not printed.
                        'profile' and 'timeit_one' display the time to
                        solve the problem not including the build function.
                        'timeit' displays the time to execute the
                        build function and the solver 100 times.
                        Default: %(default)s""")

    parser.add_argument('--all', action='store_true',
                        help="""Search for all the solutions.
                            Cannot be used with --unique.
                            Default: %(default)s""")

    parser.add_argument('--unique', action='store_true',
                        help="""Determine if there is more than one solution.
                            Cannot be used with --all.
                            Default: %(default)s""")

    if nbr_builds:
        parser.add_argument('--build', action='store',
                            choices=range(1,nbr_builds+1), default=1,
                            type=int,
                            help="""Which of multiple build functions should be run.
                            This option is only available if the experimenter
                            was given more than one build function.
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

    if cargs.all and cargs.unique:
        print('--all and --unique cannot both be used.')
        sys.exit()

    return cargs


# %%  do_stuff (main)


def do_stuff(build_param, show_solution):
    """The main interface to the experimenter.
    Check the parameters, parse the command line arguements, and
    then do something."""

    nbr_builds = 0
    if isinstance(build_param, list):
        nbr_builds = len(build_param)

    elif not callable(build_param) or not callable(show_solution):
        raise ValueError(
            'Usage:  do_stuff(build_func or list of build_funcs, show_func)')

    cargs = parse_args(nbr_builds)

    build = build_param[cargs.build -1] if nbr_builds else build_param
    if build.__doc__:
        print(textwrap.fill(build.__doc__), '\n')

    if cargs.solver == ALL:
        run_the_solvers(cargs, build)
        sys.exit()

    if cargs.var_chooser == ALL:
        run_the_choosers(cargs, build)
        sys.exit()

    if ((cargs.all or cargs.unique)
            and cargs.solver == solver.MinConflictsSolver.__name__):
        print('MinConflictsSolver can only find one solution.')
        cargs.all = False
        cargs.unique = False

    if cargs.solver == solver.MinConflictsSolver.__name__  \
        and cargs.var_chooser != KEEP:
        print("Var chooser isn't used with MinConflictSolver.")
        sys.exit()

    if (not cargs.forward and cargs.arc_consist != KEEP
        and ARC_CONSIST[cargs.arc_consist]):
        print("Arc Consistency behavior is not well defined without --forward.")

    solve_it(cargs, build, show_solution)
