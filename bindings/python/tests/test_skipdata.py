#!/usr/bin/env python3

# Capstone Python bindings, by Nguyen Anh Quynnh <aquynh@gmail.com>

import pytest
from capstone import *

X86_CODE32 = b"\x8d\x4c\x32\x08\x01\xd8\x81\xc6\x34\x12\x00\x00\x00\x91\x92"
RANDOM_CODE = b"\xed\x00\x00\x00\x00\x1a\x5a\x0f\x1f\xff\xc2\x09\x80\x00\x00\x00\x07\xf7\xeb\x2a\xff\xff\x7f\x57\xe3\x01\xff\xff\x7f\x57\xeb\x00\xf0\x00\x00\x24\xb2\x4f\x00\x78"

all_tests = (
    (CS_ARCH_X86, CS_MODE_32, X86_CODE32, "X86 32 (Intel syntax)", None),
    (CS_ARCH_ARM, CS_MODE_ARM, RANDOM_CODE, "Arm", None),
)


@pytest.mark.parametrize(
    "arch,mode,code,syntax",
    [
        pytest.param(arch, mode, code, syntax, id=comment)
        for arch, mode, code, comment, syntax in all_tests
    ],
)
def test_skipdata(arch, mode, code, syntax):
    md = Cs(arch, mode)
    if syntax is not None:
        md.syntax = syntax
    md.skipdata = True

    # Default "data" instruction's name is ".byte". To rename it to "db", just use
    # the code below.
    md.skipdata_setup = ("db", None, None)

    insns = list(md.disasm(code, 0x1000))
    assert insns
    assert all(insn.mnemonic for insn in insns)
