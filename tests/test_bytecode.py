

def test_disa_bytecode():

    with open("tests/cases/bytecode/CODE.lst", "r") as gen_f, open("tests/cases/bytecode/CODE_disa.lst", "r") as disa_f:
        # skip headers
        disa_lines = disa_f.readlines()[10:]
        gen_lines = gen_f.readlines()[9:]

        nb_line = 0
        for gen_line, disa_line in zip(gen_lines, disa_lines):

            # print(gen_line[:4], cc65_line[2:6])
            gen_address = int(gen_line[:4], 16)
            disa_address = int(disa_line[:4], 16)

            assert gen_address == disa_address,  f"[{nb_line+10}/{nb_line+11}] ${gen_address:04X} vs ${disa_address:04X}"

            gen_bytecode = gen_line[8:17]
            disa_bytecode = disa_line[8:17]

            assert gen_bytecode == disa_bytecode, f"[{nb_line+10}/{nb_line+11}] at ${gen_address:04X}, bytecode is different: '{gen_bytecode}' vs '{disa_bytecode}'"

            nb_line += 1


def test_cc65_bytecode():

    with open("tests/cases/bytecode/CODE.lst", "r") as gen_f, open("tests/cases/bytecode/CODE.cc65_lst", "r") as cc65_f:
        # skip headers
        cc65_lines = cc65_f.readlines()[13:]
        gen_lines = gen_f.readlines()[9:]


        delta_cc65 = 0
        for i in range(len(gen_lines)):

            gen_line = gen_lines[i]
            cc65_line = cc65_lines[delta_cc65+i]

            # print(gen_line[:4], cc65_line[2:6])
            gen_address = int(gen_line[:4], 16)
            cc65_address = int(cc65_line[2:6], 16) + 0x0801

            assert gen_address == cc65_address,  f"[{i+10}/{i+14+delta_cc65}] ${gen_address:04X} vs ${cc65_address:04X}"

            gen_bytecode = gen_line[8:17]
            cc65_bytecode = cc65_line[11:20]

            if cc65_bytecode.strip() == '':
                delta_cc65 += 1
                cc65_line = cc65_lines[delta_cc65+i]
                cc65_bytecode = cc65_line[11:20]

            if 'rr' in cc65_bytecode:
                print(f"cc65 bytecode address not resolved: {cc65_bytecode}")
            else:
                assert gen_bytecode == cc65_bytecode, f"[{i+10}/{i+14+delta_cc65}] at ${gen_address:04X}, bytecode is different: '{gen_bytecode}' vs '{cc65_bytecode}'"

