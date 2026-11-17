#!/usr/bin/env python3
# Copyright © 2024 Peace-Maker <peacemakerctf@gmail.com>
# SPDX-License-Identifier: BSD-3

import pytest
import capstone.arm64
import capstone.sysz_const
from capstone import *
import capstone.aarch64
import capstone.arm
import capstone.systemz

AARCH64_CODE = b"\x21\x7c\x02\x9b\x21\x7c\x00\x53\x00\x40\x21\x4b\xe1\x0b\x40\xb9"
SYSZ_CODE = b"\xed\x00\x00\x00\x00\x1a\x5a\x0f\x1f\xff\xc2\x09\x80\x00\x00\x00\x07\xf7\xeb\x2a\xff\xff\x7f\x57\xe3\x01\xff\xff\x7f\x57\xeb\x00\xf0\x00\x00\x24\xb2\x4f\x00\x78"


all_tests = (
    (CS_ARCH_ARM64, CS_MODE_ARM, AARCH64_CODE, "ARM64"),
    (CS_ARCH_SYSZ, CS_MODE_BIG_ENDIAN, SYSZ_CODE, "SysZ"),
)


# Test arm64 and sysz compatibility layer
@pytest.mark.parametrize(
    "arch,mode,code",
    [
        pytest.param(arch, mode, code, id=comment)
        for arch, mode, code, comment in all_tests
    ],
)
def test_compatibility_disasm(arch, mode, code):
    md = Cs(arch, mode)
    md.detail = True
    insns = list(md.disasm(code, 0x1000))
    assert insns
    for insn in insns:
        insn.cc


def test_aarch64_constants():
    assert capstone.arm64.ARM64_CC_AL == capstone.aarch64.AArch64CC_AL
    assert capstone.arm64.ARM64_INS_FDIV == capstone.aarch64.AARCH64_INS_FDIV


def test_sysz_constants():
    assert capstone.systemz.SYSZ_INS_LG == capstone.systemz.SYSTEMZ_INS_LG


def test_riscv_mode_constant():
    assert CS_MODE_RISCVC == CS_MODE_RISCV_C
    assert "CS_MODE_RISCVC" in capstone.__all__


def test_arm_cc_constants():
    assert capstone.arm.ARM_CC_MI == capstone.arm.ARMCC_MI
    assert capstone.arm.ARM_CC_INVALID == capstone.arm.ARMCC_Invalid
