# Copyright © 2024 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: BSD-3

# Typing for Python3.8
from __future__ import annotations

from pathlib import Path

import pytest

from cstest.cstest import TestFile


class FailedTestFile:
    """Stand-in for a yaml file which could not be parsed.
    Always fails with the parse error so pytest reports it as a failure."""

    def __init__(self, path: Path, error: Exception):
        self.path = path
        self.error = error

    def check(self) -> list[str]:
        return [f"{self.path}: {self.error}"]


def yaml_test_params(yaml_paths) -> list:
    """Builds the pytest.param list for all test cases of the given yaml files."""
    params = []
    for ypath in sorted(yaml_paths):
        try:
            test_file = TestFile(ypath)
        except Exception as e:
            marks = []
            if "negative" in ypath.parts:
                # Test files which must fail. A pass fails the run (strict).
                marks.append(
                    pytest.mark.xfail(reason="negative test file", strict=True)
                )
            params.append(
                pytest.param(
                    FailedTestFile(ypath, e),
                    marks=marks,
                    id=f"{ypath.name}::invalid",
                )
            )
            continue
        seen = set()
        for i, tc in enumerate(test_file.test_cases):
            name = tc.name or f"test_case_{i}"
            if name in seen:
                name = f"{name}_{i}"
            seen.add(name)
            marks = [pytest.mark.skip(reason=tc.skip_reason)] if tc.skip else []
            if "negative" in ypath.parts:
                # Test cases which must fail. A pass fails the run (strict).
                marks.append(
                    pytest.mark.xfail(reason="negative test case", strict=True)
                )
            params.append(pytest.param(tc, marks=marks, id=f"{ypath.name}::{name}"))
    return params


def find_yaml_files(paths) -> list[Path]:
    """Finds all yaml test files below the given files or directories."""
    yaml_files = []
    for path in paths:
        path = Path(path)
        if path.suffix in (".yaml", ".yml"):
            yaml_files.append(path)
        elif path.is_dir():
            for suffix in ("*.yaml", "*.yml"):
                yaml_files.extend(path.rglob(suffix))
    return yaml_files


def pytest_addoption(parser):
    parser.addini(
        "cstest_yaml_dirs",
        "Default directories searched recursively for cstest yaml test files.",
        type="paths",
        default=[],
    )


@pytest.fixture
def cstest_case(request):
    """A single test case of a cstest yaml test file."""
    return request.param


def pytest_generate_tests(metafunc):
    """Parametrizes tests using the 'cstest_case' fixture with one test
    per yaml test case. The yaml files are searched in all files and
    directories passed on the command line. If none are given, the
    'cstest_yaml_dirs' ini option is used instead."""
    if "cstest_case" not in metafunc.fixturenames:
        return
    yaml_files = find_yaml_files(metafunc.config.args)
    if not yaml_files:
        yaml_files = find_yaml_files(metafunc.config.getini("cstest_yaml_dirs"))
    params = yaml_test_params(yaml_files)
    metafunc.parametrize("cstest_case", params, indirect=True)
