import pytest
from cases.parse_case import parse_case
from pytest_cases import case, parametrize

class OpCodesCases:

    @parametrize("asm_file_path,test_name",
                 [("tests/cases/6502_test_00.asm","test_00"),
                  ("tests/cases/6502_test_04.asm","test_04"),
                  ("tests/cases/6502_test_10.asm","test_10"),
                  ("tests/cases/6502_test_11.asm","test_11"),
                  ("tests/cases/6502_test_12.asm","test_12"),
                  ("tests/cases/6502_test_13.asm","test_13")
                 ])
    def hmc_6502_roms(self, asm_file_path, test_name):
        cases = parse_case(asm_file_path)
        return cases, test_name

