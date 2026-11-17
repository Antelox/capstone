#!/usr/bin/env python3
# Copyright © 2024 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: BSD-3

# Tests the error reporting of the yaml test case handling with the
# intentionally invalid and failing test files of suite/cstest/test/.

import logging
from pathlib import Path

import pytest
import yaml

from cstest.cstest import TestFile
from conftest import FailedTestFile, yaml_test_params

FIXTURE_DIR = Path(__file__).parents[3] / "suite" / "cstest" / "test"


def test_empty_file():
    with pytest.raises(ValueError, match="Empty file"):
        TestFile(FIXTURE_DIR / "empty_test_file.yaml")


def test_missing_mandatory_field():
    with pytest.raises(ValueError, match="Missing required mapping field"):
        TestFile(FIXTURE_DIR / "missing_madatory_field.yaml")


def test_invalid_file():
    with pytest.raises(yaml.YAMLError, match="cannot start any token"):
        TestFile(FIXTURE_DIR / "invalid_test_file.yaml")


def test_min_valid_file():
    test_file = TestFile(FIXTURE_DIR / "min_valid_test_file.yaml")
    for test_case in test_file.test_cases:
        assert test_case.check() == []


def test_invalid_arch():
    test_file = TestFile(FIXTURE_DIR / "invalid_cs_input.yaml")
    errors = test_file.test_cases[0].check()
    assert errors
    assert "'ar' is not mapped to a capstone architecture." in errors[0]


def test_wrong_insn_count():
    test_file = TestFile(FIXTURE_DIR / "invalid_cs_input.yaml")
    errors = test_file.test_cases[1].check()
    assert errors
    assert "0 != 0x1" in errors[0]


def test_unused_option(caplog):
    test_file = TestFile(FIXTURE_DIR / "invalid_cs_input.yaml")
    with caplog.at_level(logging.WARNING, "cstest"):
        test_file.test_cases[2].check()
    assert "Option: 'thum' not used" in caplog.text


def test_unparsable_file_param():
    # Files which can't be parsed must become a failing test parameter.
    params = yaml_test_params([FIXTURE_DIR / "empty_test_file.yaml"])
    assert len(params) == 1
    failed = params[0].values[0]
    assert isinstance(failed, FailedTestFile)
    assert "Empty file" in failed.check()[0]
