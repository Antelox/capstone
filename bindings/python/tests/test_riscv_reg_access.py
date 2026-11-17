import pytest
from capstone import *
from capstone.riscv import *


@pytest.fixture
def cs():
    md = Cs(CS_ARCH_RISCV, CS_MODE_RISCV64)
    md.option(CS_OPT_DETAIL, CS_OPT_DETAIL_REAL | CS_OPT_ON)
    return md


def disasm_one(cs, code):
    insns = list(cs.disasm(code, 0))
    assert len(insns) == 1
    return insns[0]


def test_riscv_syntax_detail_constants():
    assert CS_OPT_SYNTAX_REAL == 1 << 10
    assert CS_OPT_SYNTAX_UNCOMPRESSED_REAL == 1 << 11
    assert CS_OPT_SYNTAX_ALIAS == 1 << 13
    assert CS_OPT_DETAIL_UNCOMPRESSED_REAL == 1 << 2
    assert CS_OPT_DETAIL_ALIAS == 1 << 3


def test_addi(cs):
    # addi a0, a1, 10
    insn = disasm_one(cs, b"\x13\x85\xa5\x00")
    read, write = insn.regs_access()
    # a1 = RISCV_REG_X11, a0 = RISCV_REG_X10
    assert RISCV_REG_X11 in read
    assert RISCV_REG_X10 in write
    assert len(read) == 1
    assert len(write) == 1


def test_jalr(cs):
    # jalr ra, a1, 0 -> 0x000580e7 (rd=x1=ra, rs1=x11=a1, imm=0)
    insn = disasm_one(cs, b"\xe7\x80\x05\x00")
    read, write = insn.regs_access()
    # ra = RISCV_REG_X1
    assert RISCV_REG_X11 in read
    assert RISCV_REG_X1 in write
    assert len(read) == 1
    assert len(write) == 1


def test_lb(cs):
    # lb a0, 0(sp)
    insn = disasm_one(cs, b"\x03\x05\x01\x00")
    read, write = insn.regs_access()
    # sp = RISCV_REG_X2
    assert RISCV_REG_X2 in read
    assert RISCV_REG_X10 in write
    assert len(read) == 1
    assert len(write) == 1


def test_caddi(cs):
    # c.addi a0, 10 (0x0529)
    insn = disasm_one(cs, b"\x29\x05")
    read, write = insn.regs_access()
    # x10 is both read and written
    assert RISCV_REG_X10 in read
    assert RISCV_REG_X10 in write
    assert len(read) == 1
    assert len(write) == 1


def test_ecall(cs):
    # ecall
    insn = disasm_one(cs, b"\x73\x00\x00\x00")
    read, write = insn.regs_access()
    assert len(read) == 0
    assert len(write) == 0


def test_csrrw(cs):
    # csrrw a0, sstatus, a1
    insn = disasm_one(cs, b"\x73\x95\x05\x10")
    read, write = insn.regs_access()
    # CSRs should NOT be in the reg_access list
    assert RISCV_REG_X11 in read
    assert RISCV_REG_X10 in write
    assert len(read) == 1
    assert len(write) == 1
