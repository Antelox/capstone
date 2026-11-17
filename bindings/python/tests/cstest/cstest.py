#!/usr/bin/env python3
# Copyright © 2024 Rot127 <unisono@quyllur.org>
# SPDX-License-Identifier: BSD-3

# Typing for Python3.8
from __future__ import annotations

import logging
import yaml
import capstone

from capstone import CsInsn, Cs, CS_ARCH_AARCH64, CS_MODE_64, CS_MODE_16

from cstest.cs_modes import configs
from cstest.details import compare_details
from cstest.compare import (
    compare_asm_text,
    compare_str,
    compare_tbool,
    compare_enum,
    compare_uint32,
    failures,
)
from pathlib import Path

log = logging.getLogger("cstest")


def get_cs_int_attr(cs, attr: str, err_msg_pre: str):
    try:
        attr_int = getattr(cs, attr)
        if not isinstance(attr_int, int):
            raise AttributeError(f"{attr} not found")
        return attr_int
    except AttributeError:
        log.warning(f"{err_msg_pre}: Capstone doesn't have the attribute '{attr}'")
        return None


def arch_bits(arch: int, mode: int) -> int:
    if arch == CS_ARCH_AARCH64 or mode & CS_MODE_64:
        return 64
    elif mode & CS_MODE_16:
        return 16
    return 32


class TestInput:
    __test__ = False

    def __init__(self, input_dict: dict):
        self.input_dict = input_dict
        if "bytes" not in self.input_dict:
            raise ValueError("Error: 'Missing required mapping field'\nField: 'bytes'.")
        if "options" not in self.input_dict:
            raise ValueError(
                "Error: 'Missing required mapping field'\nField: 'options'."
            )
        if "arch" not in self.input_dict:
            raise ValueError("Error: 'Missing required mapping field'\nField: 'arch'.")
        self.in_bytes = bytes(self.input_dict["bytes"])
        self.options = self.input_dict["options"]
        self.arch = self.input_dict["arch"]

        self.name = "" if "name" not in self.input_dict else self.input_dict["name"]
        if "address" not in self.input_dict:
            self.address: int = 0
        else:
            assert isinstance(self.input_dict["address"], int)
            self.address = self.input_dict["address"]
        self.handle = None
        self.arch_bits = 0

    def setup(self):
        log.debug(f"Init {self}")
        arch = get_cs_int_attr(capstone, self.arch, "CS_ARCH")
        if arch is None:
            cs_name = f"CS_ARCH_{self.arch.upper()}"
            arch = get_cs_int_attr(capstone, cs_name, "CS_ARCH")
            if arch is None:
                raise ValueError(
                    f"Couldn't init architecture as '{self.arch}' or '{cs_name}'.\n"
                    f"'{self.arch}' is not mapped to a capstone architecture."
                )
        new_mode = 0
        for opt in self.options:
            if "CS_MODE_" in opt:
                mode = get_cs_int_attr(capstone, opt, "CS_OPT")
                if mode is not None:
                    new_mode |= mode
                    continue
        self.handle = Cs(arch, new_mode)

        for opt in self.options:
            if "CS_MODE_" in opt:
                continue
            if "CS_OPT_" in opt and opt in configs:
                mtype = configs[opt]["type"]
                val = configs[opt]["val"]
                self.handle.option(mtype, val)
                continue
            log.warning(f"Option: '{opt}' not used")

        self.arch_bits = arch_bits(self.handle.arch, self.handle.mode)
        log.debug("Init done")

    def decode(self) -> list[CsInsn]:
        if not self.handle:
            raise ValueError("self.handle is None. Must be setup before.")
        return [i for i in self.handle.disasm(self.in_bytes, self.address)]

    def __str__(self):
        default = (
            f"TestInput {{ arch: {self.arch}, options: {self.options}, "
            f"addr: {self.address:x}, bytes: [ {','.join([f'{b:#04x}' for b in self.in_bytes])} ] }}"
        )
        if self.name:
            return f"{self.name} -- {default}"
        return default


class TestExpected:
    __test__ = False

    def __init__(self, expected_dict: dict):
        self.expected_dict = expected_dict
        self.insns = (
            list() if "insns" not in self.expected_dict else self.expected_dict["insns"]
        )

    def compare(self, actual_insns: list[CsInsn], bits: int):
        if len(actual_insns) != len(self.insns):
            failures.error(
                "Number of decoded instructions don't match (actual != expected): "
                f"{len(actual_insns)} != {len(self.insns):#x}"
            )
            return

        for a_insn, e_insn in zip(actual_insns, self.insns):
            compare_asm_text(a_insn, e_insn.get("asm_text"), bits)
            compare_str(a_insn.mnemonic, e_insn.get("mnemonic"), "mnemonic")
            compare_str(a_insn.op_str, e_insn.get("op_str"), "op_str")
            compare_enum(a_insn.id, e_insn.get("id"), "id")
            compare_tbool(a_insn.is_alias, e_insn.get("is_alias"), "is_alias")
            compare_tbool(a_insn.illegal, e_insn.get("illegal"), "illegal")
            compare_uint32(a_insn.size, e_insn.get("size"), "size")
            compare_enum(a_insn.alias_id, e_insn.get("alias_id"), "alias_id")
            compare_details(a_insn, e_insn.get("details"))


class TestCase:
    """A single test case of a yaml test file."""

    __test__ = False

    def __init__(self, test_case_dict: dict):
        self.tc_dict = test_case_dict
        if "input" not in self.tc_dict:
            raise ValueError("Mandatory field 'input' missing")
        if "expected" not in self.tc_dict:
            raise ValueError("Mandatory field 'expected' missing")
        self.input = TestInput(self.tc_dict["input"])
        self.expected = TestExpected(self.tc_dict["expected"])
        self.skip = "skip" in self.tc_dict
        if self.skip and "skip_reason" not in self.tc_dict:
            raise ValueError(
                "If 'skip' field is set a 'skip_reason' field must be set as well."
            )
        self.skip_reason = (
            self.tc_dict["skip_reason"] if "skip_reason" in self.tc_dict else ""
        )

    @property
    def name(self) -> str:
        return self.input.name

    def check(self) -> list[str]:
        """Runs the test case and returns the mismatch or error messages.
        An empty list means the test case passed."""
        try:
            self.input.setup()
        except Exception as e:
            return [f"Setup failed: {e}"]

        try:
            insns = self.input.decode()
        except Exception as e:
            return [f"Decode failed: {e}"]

        with failures.collecting() as messages:
            try:
                self.expected.compare(insns, self.input.arch_bits)
            except Exception as e:
                return [f"Comparison failed: {e}"]
        return messages


class TestFile:
    """A yaml test file with all its test cases."""

    __test__ = False

    def __init__(self, tfile_path: Path):
        self.path = tfile_path
        with open(tfile_path) as f:
            self.content = yaml.safe_load(f)
        if not self.content:
            raise ValueError("Empty file")
        if "test_cases" not in self.content:
            raise ValueError("Mandatory field 'test_cases' missing")
        self.test_cases = list()
        for tc_dict in self.content["test_cases"]:
            tc = TestCase(tc_dict)
            self.test_cases.append(tc)
