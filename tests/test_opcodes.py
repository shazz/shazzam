

import sys
sys.path.append(".")
from shazzam.py64gen import *
from shazzam.py64gen import Register as r

import pytest
from cases.parse_case import parse_case
from pytest_cases import parametrize_with_cases
from tests.cases_opcodes import OpCodesCases


# tests from https://github.com/mwales/6502-tests/tree/master/hmc-6502/roms

@parametrize_with_cases('cases,test_name', cases=OpCodesCases, prefix='hmc')
def test_hmc_6502_roms(cases, test_name):

    with segment(0x0, test_name) as s:
        for instr, res in cases.items():
            bc = eval(instr)
            assert bc == res, f"{instr} should generate byte code ${res.hex('$', 3)} and not ${bc.hex('$', 3)}."

def test_lda():

    with segment(0x0, "lda_imm") as s:
        for i in range(255+1):
            assert lda(imm=i) == bytearray([Instruction.opcodes.index(["lda","imm"]), i])

        with pytest.raises(ValueError):
            lda(imm=256)
        with pytest.raises(ValueError):
            lda(imm=1000)

    with segment(0x0, "lda_abs_zpg") as s:
        for i in range(0x100):
            assert lda(abs_adr=i) == bytearray([Instruction.opcodes.index(["lda","zpg"]), i & 0xff])

        for i in range(0x100, 0xffff+1):
            assert lda(abs_adr=i) == bytearray([Instruction.opcodes.index(["lda","abs"]), i & 0xff, (i >>8) & 0xff])

        with pytest.raises(ValueError):
            lda(abs_adr=0x10000)

    with segment(0x0, "lda_abs_label") as s:
        label("label1")
        lda(label="label1")

        # with pytest.raises(ValueError):
        #     lda(label="")

    # with pytest.raises(ValueError):
    #     with segment(0x0, "lda_abs_label") as s:
    #         lda(label="label2")

