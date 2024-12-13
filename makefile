

SOURCES = csp_solver/*.py csp_solver/constraint/*.py
TESTS = tests/test_*.py


all: unit_tests pylint


#  unit_tests
#
#  run all the unit tests and create a coverage report

unit_tests: htmlcov/index.html $(SOURCES) $(TESTS)
	-coverage run --branch -m pytest
	coverage html


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


#  pylint
#
#  run the pylint on all source files together

pylint: pylint_report.txt $(SOURCES) .pylintrc

pylint_report.txt: $(SOURCES) .pylintrc
	-del pylint_report.txt
	-pylint --output pylint_report.txt --rcfile .pylintrc --recursive yes csp_solver
	type pylint_report.txt


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
	-rmdir /S /Q .pytest_cache
	-del pylint_report.txt
	-rmdir /S /Q htmlcov
	-del .coverage


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


###########################################################

# a rule to do a bit of everything to see if anything crashes

.PHONY: experimenter
experimenter:
	python examples\\queens.py --solver all
	python examples\\queens.py --solver Backtracking
	python examples\\queens.py --solver MinConflictsSolver
	python examples\\einstein.py --solver NonRecBacktracking
	python examples\\einstein.py --solver NonRecBacktracking --forward
	python examples\\einstein.py --solver NonRecBacktracking --var_chooser all
	python examples\\forbus.py --build 1
	python examples\\forbus.py --build 2 --var_chooser MinDomain
	python examples\\forbus.py --build 3 --var_chooser UseFirst
	python examples\\forbus.py --build 4 --var_chooser MaxAssignedNeighs
	python examples\\sendmore.py --build 2
	python examples\\sendmore.py --build 2 --arc_consist ArcCon3 --forward
	python examples\\BattleBoats\\battleboats.py --build 3


############################################################
## run examples below here


%.slvrs:
	python examples\\$(subst .slvrs,.py,$@) --solver Backtracking
	python examples\\$(subst .slvrs,.py,$@) --solver NonRecBacktracking
	python examples\\$(subst .slvrs,.py,$@) --solver MinConflictsSolver

# usage make forbus.bnbr
forbus.%:
	python examples\\forbus.py --solver Backtracking --build $(subst forbus.,$(space),$@)
	python examples\\forbus.py --solver NonRecBacktracking --build $(subst forbus.,$(space),$@)
	python examples\\forbus.py --solver MinConflictsSolver --build $(subst forbus.,$(space),$@)


.PHONY : back
back:
	python examples\\queens.py
	python examples\\einstein.py
	python examples\\forbus.py

.PHONY : backforw
backforw:
	python examples\\queens.py --forward
	python examples\\einstein.py --forward
	python examples\\forbus.py --forward

.PHONY : nrback
nrback:
	python examples\\queens.py --solver NonRecBacktracking
	python examples\\einstein.py --solver NonRecBacktracking
	python examples\\forbus.py --solver NonRecBacktracking

.PHONY : nrbackforw
nrbackforw:
	python examples\\queens.py --solver NonRecBacktracking --forward
	python examples\\einstein.py --solver NonRecBacktracking --forward
	python examples\\forbus.py --forward
