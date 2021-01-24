import pytest
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
        cases = self._parse_case(asm_file_path)
        return cases, test_name

    def _parse_case(self, filename):

        with open(filename, "r") as f:
            lines = f.readlines()

        cases = { }
        for i in range(len(lines)):
            if lines[i].startswith("test:"):
                case = lines[i][6:]

                barr = bytearray()
                # 1st operand
                barr.append(int(lines[i+1][:2], 16))

                # 2nd operand
                if i < len(lines)-2 and not lines[i+2].startswith("test:"):
                    barr.append(int(lines[i+2][:2], 16))

                    # 3rd operand
                    if i < len(lines)-3 and not lines[i+3].startswith("test:") :
                        barr.append(int(lines[i+3][:2], 16))

                # print(f"adding case {case}: {barr.hex()}")

                cases[case] = barr

        return cases

