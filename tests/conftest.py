# -*- coding: utf-8 -*-
"""Use pytest hooks to configure the test environment and
update tests:

Filter tests that run slow unless specifically requested
with --run_slow.

Created on Fri Dec 20 07:25:31 2024
@author: Ann"""


import pytest


def pytest_addoption(parser):
    parser.addoption("--run_slow", action="store_true", default=False)


def pytest_collection_modifyitems(config, items):

    if not config.getoption("--run_slow"):
        skipper = pytest.mark.skip(reason="Only run when --run_slow is given")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skipper)
