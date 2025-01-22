

SOURCES = csp_solver/*.py csp_solver/constraint/*.py
TESTS = tests/conftest.py tests/stubs.py tests/test_*.py 

all: clean all_tests pylint

final: all examples experimenter


#  clean
#
#  remove most of the accumulated stuff from builds
#  generally causes any other target to re-run

.PHONY : clean
clean:
	-rmdir /S /Q __pycache__
	-rmdir /S /Q csp_solver\\__pycache__
	-rmdir /S /Q csp_solver\\constraint\\__pycache__
	-rmdir /S /Q tests\\__pycache__
	-rmdir /S /Q examples\\__pycache__
	-rmdir /S /Q examples\\BattleBoats\\__pycache__
	-rmdir /S /Q examples\\MasterMind\\__pycache__
	-rmdir /S /Q .pytest_cache
	-del pylint_report.txt
	-rmdir /S /Q htmlcov
	-del .coverage


#  pylint
#
#  run the pylint on all source files together

pylint: pylint_report.txt $(SOURCES) .pylintrc

pylint_report.txt: $(SOURCES) .pylintrc
	-del pylint_report.txt
	-pylint --output pylint_report.txt --rcfile .pylintrc --recursive yes csp_solver
	type pylint_report.txt


#  unit_tests
#
#  run all the unit tests and create a coverage report

unit_tests: $(SOURCES) $(TESTS)
	-coverage run --branch -m pytest -m unittest
	coverage html


#  all_tests
#
#  run all tests (do not include slow examples)

all_tests: $(SOURCES) $(TESTS)
	-coverage run --branch -m pytest
	coverage html


#  examples
#
#  run the example tests and show the output, include the slow examples

.PHONY: examples
examples:
	@echo Running all __test_examples__ sections with pytest (including the slow ones).
	pytest -vs tests/test_z_examples.py --run_slow


#  test individual files
#	usage:   make <testfile>.test
#       example: make test_var.test
#  where <testfile> is a file of tests in the 'tests' directory
#  this rules cleans all previous coverage data and runs the one
#  files of tests. This can be used to make certain that the
#  code is actually tested and not just run as part of another
#  test.

.PHONY: %.test
%.test: 
	-coverage run --branch -m pytest tests\\$(subst .test,.py,$@)
	coverage html


# Three places to look for things that need doing:
#   1. unit test_coverage
#   2. pylint issues
#   3. TODO in code

.PHONY : TODO
TODO:  unit_tests pylint
	grep TODO csp_solver/*py csp_solver/constraint/*py tests/*py examples/*py


.PHONY: list
list:
	@grep -Eo "^[a-zA-Z0-9\\/._]+:" makefile | sed -e "s/://" | sed -e "/PHONY/d" | sort


# experimenter
#
# run the experimenter with a bunch of different options

.PHONY: experimenter
experimenter:
	python examples\\queens.py --solver all
	python examples\\queens.py --solver Backtracking --forward on
	python examples\\queens.py --solver Backtracking --forward on --arc_consist ArcCon3
	python examples\\einstein.py --solver NonRecBacktracking
	python examples\\einstein.py --solver NonRecBacktracking --forward on
	python examples\\einstein.py --solver NonRecBacktracking --var_chooser all
	python examples\\forbus.py --build all
	python examples\\forbus.py --build all --forward on
	python examples\\forbus.py --build 1
	python examples\\forbus.py --build 2 --var_chooser MinDomain
	python examples\\forbus.py --build 3 --var_chooser UseFirst
	python examples\\forbus.py --build 4 --var_chooser MaxAssignedNeighs
	python examples\\sendmore.py --build 2
	python examples\\sendmore.py --build 2 --arc_consist ArcCon3 --forward on
	python examples\\BattleBoats\\bboat_cnstr.py --build 2
	python examples\\BattleBoats\\bboat_extra.py --build 2
	python examples\\BattleBoats\\bboat_cnstr.py --build all --sol_type unique 
	python examples\\BattleBoats\\bboat_cnstr.py --build 15 --sol_type all
