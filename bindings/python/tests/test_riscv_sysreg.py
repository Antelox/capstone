from capstone import *
from capstone.riscv import *
from capstone.riscv_const import *


def test_riscv_sysreg():
    # csrr a0, sstatus (0x10002573)
    # csrr a0, mtvec   (0x30502573)
    # csrr a0, mcause  (0x34202573)
    CODE = b"\x73\x25\x00\x10\x73\x25\x50\x30\x73\x25\x20\x34"

    expected_sysregs = [
        RISCV_SYSREG_SSTATUS,
        RISCV_SYSREG_MTVEC,
        RISCV_SYSREG_MCAUSE,
    ]

    md = Cs(CS_ARCH_RISCV, CS_MODE_RISCV64)
    md.detail = True

    found_sysregs = []
    insns = list(md.disasm(CODE, 0))
    for insn in insns:
        csr_ops = [op for op in insn.operands if op.type == RISCV_OP_CSR]
        assert csr_ops, "No CSR operand found"
        found_sysregs.append(csr_ops[0].csr)

    assert len(insns) == 3
    assert found_sysregs == expected_sysregs
