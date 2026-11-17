#!/usr/bin/env python3

# Capstone Python bindings, by Nguyen Anh Quynnh <aquynh@gmail.com>

from capstone import *
from capstone.x86 import *

X86_CODE32 = b"\x75\x01"


def disasm_mnemonics(md, code):
    return [insn.mnemonic for insn in md.disasm(code, 0x1000)]


def test_customized_mnemonic():
    md = Cs(CS_ARCH_X86, CS_MODE_32)

    # Disassemble X86 code with default instruction mnemonic
    assert disasm_mnemonics(md, X86_CODE32) == ["jne"]

    # Customize engine to change mnemonic from 'JNE' to 'JNZ'
    md.mnemonic_setup(X86_INS_JNE, "jnz")
    assert disasm_mnemonics(md, X86_CODE32) == ["jnz"]

    # Reset engine to use the default mnemonic
    md.mnemonic_setup(X86_INS_JNE, None)
    assert disasm_mnemonics(md, X86_CODE32) == ["jne"]
