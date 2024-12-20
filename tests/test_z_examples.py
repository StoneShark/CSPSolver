# -*- coding: utf-8 -*-
"""Confirm that examples run, no evaluation of the
result is done. Fails on crashes.

Each example file decides what the test should be
by wrapping a section of code with:
    if __name__ == '__test_examples__':

or including '__test_exmples__' to run the whole file.

If a modules has no test it should include:

    if __name__ == '__test_examples__':
        skipped = True
        reason = 'Support module'  # or other explaination

Created on Thu Dec 19 07:20:46 2024
@author: Ann"""

import os
import runpy

import pytest

TEST_EXAMPLE = '__test_example__'
SKIPPED = 'skipped'
REASON = 'reason'

runs_slow = ['battleboats_two',
             # these don't work:  'battleboats_three', 'battleboats_extra',
            'master_mind_5',
            'master_mind_6']


def get_examples():
    """Collect every .py file in the examples directory.
    If the example is listed in runs_slow, mark the test
    as slow."""

    examples = []
    for dpath, _, files in os.walk(os.path.join('.', 'examples')):
        for file in files:

            if file[-3:] == '.py':

                param = os.path.join(dpath, file)
                if any(slowex in file for slowex in runs_slow):
                    param = pytest.param(param, marks=pytest.mark.slow)

                examples += [param]

    return examples


@pytest.mark.parametrize('epath', get_examples())
def test_example(epath):
    """If the test has the TEXT_EXAMPLE tag,
    run the modules with that name.
    Otherwise, report a test failure."""

    with open(epath, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    if TEST_EXAMPLE not in ''.join(lines):
        pytest.fail(reason="No __test_example__ in file.")

    gdict = runpy.run_path(epath, run_name=TEST_EXAMPLE)

    if gdict.get(SKIPPED, False):
        pytest.skip(reason=gdict.get(REASON, 'No reason given'))
