


def parse_case(filename):

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

                if i < len(lines)-3 and not lines[i+3].startswith("test:") :
                    barr.append(int(lines[i+3][:2], 16))

            # print(f"adding case {case}: {barr.hex()}")

            cases[case] = barr

    return cases