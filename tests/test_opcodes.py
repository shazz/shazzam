

import sys
sys.path.append(".")
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as X, RegisterY as Y, RegisterACC as A

import pytest
from pytest_cases import parametrize_with_cases
from tests.cases_opcodes import OpCodesCases


# tests from https://github.com/mwales/6502-tests/tree/master/hmc-6502/roms

@parametrize_with_cases('cases,test_name', cases=OpCodesCases, prefix='hmc')
def test_hmc_6502_roms(cases, test_name):

    with segment(0x0, test_name, check_address_dups=False) as s:
        for instr, res in cases.items():
            bc = eval(instr).bytecode
            assert bc == res, f"{instr} should generate byte code ${res.hex('$', 3)} and not ${bc.hex('$', 3)}."

def test_lda():

    with segment(0x0, "lda_imm", check_address_dups=False) as s:
        for i in range(255+1):
            assert lda(imm(i)).bytecode == bytearray([Instruction.opcodes.index(["lda","imm"]), i]), f"error for i = {i}"

        with pytest.raises(ValueError):
            lda(imm(256))
        with pytest.raises(ValueError):
            lda(imm(1000))

    with segment(0x0, "lda_abs_zpg", check_address_dups=False) as s:
        for i in range(0x100):
            assert lda(at(i)).bytecode == bytearray([Instruction.opcodes.index(["lda","zpg"]), i & 0xff]), f"error for i = {i}"

        for i in range(0x100, 0xffff+1):
            assert lda(at(i)).bytecode == bytearray([Instruction.opcodes.index(["lda","abs"]), i & 0xff, (i >>8) & 0xff]), f"error for i = {i}"

        with pytest.raises(ValueError):
            lda(at(0x10000))

    with segment(0x0, "lda_abs_label", check_address_dups=False) as s:
        label("label1")
        lda(at("label1"))

        with pytest.raises(ValueError):
            lda(at(""))

    # with pytest.raises(ValueError):
    #     with segment(0x3000, "lda_abs_label") as s:
    #         lda(at("label2"))

