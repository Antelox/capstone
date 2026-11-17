#!/usr/bin/env python3
# Copyright © 2024 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: BSD-3

# Runs the cstest yaml test cases. One parametrized test per yaml test case.
# All files and directories passed to pytest on the command line are
# searched recursively for yaml test files.


def test_yaml(cstest_case):
    errors = cstest_case.check()
    assert errors == [], "\n".join(errors)
