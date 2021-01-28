import sys
sys.path.append("..")

from shazzam.Instruction import Instruction
import argparse
import re

anonymous_labels = []
variables = []
nb_tabs = 1

def add_label(val):
    tabs = nb_tabs*'\t'

    # if val.startswith("."):
    #     l = val[1:]
    #     anonymous_labels.append(l)
    #     return f'\t{l} = get_anonymous_label("{l}")'
    # else:
    return f'{tabs}label("{val}")\n'

def add_var(var):

    c = f"\t{''.join(var).replace('$', '0x').replace('=', ' = ')}\n"
    variables.append(var[0])
    return c

def add_opcode(val, operands):

    tabs = nb_tabs*'\t'
    op = f'{tabs}{val}('

    if val in find_branch_opcodes():
        op += f'rel_at("{operands[0]}")'

    else:
        if len(operands) > 0:
            ope1 = operands[0]

            if "#" in ope1:
                if ope1.startswith('#$'):
                    ope1 = f'0x{ope1[2:]}'
                else:
                    ope1 = f'{ope1[1:]}'

                op += f'imm({ope1})'
            elif "(" in ope1:
                if ope1.startswith('($'):
                    ope1 = f'(0x{ope1[2:]})'
                elif ope1[1:] in variables:
                    ope1 = ope1[1:]
                op += f'ind_at{ope1}'
            else:
                if ope1.startswith('$'):
                    op += f'at(0x{ope1[1:]})'
                elif ope1[1:] in anonymous_labels:
                    op += f'at({ope1[1:]})'
                elif ope1[1:] in variables:
                    op += f'at({ope1[1:]})'
                else:
                    if ope1.startswith("<"):
                        ope1 = ope1[1:]

                    if '+' in ope1:
                        ops = ope1.split('+')

                        if ops[0] not in variables:
                             ops[0] = f'"{ops[0]}"'

                        op += f'at({ops[0]})+{ops[1]}'
                    else:
                        if ope1 not in variables:
                             ope1 = f'"{ope1}"'

                        op += f'at({ope1})'

            if len(operands) > 1:
                ope2 = ''.join(operands[1:])
                op += ope2

    op += ')\n'
    return op

def find_opcode(val):
    for opcode in Instruction.opcodes:
        if opcode[0] == val:
            return opcode[0]

    return None

def call_macro(val):
    tabs = nb_tabs*'\t'
    mac = f"{tabs}{val}()\n"
    return mac

def gen_macro(val):
    mac = f"\n\tdef {val}():\n"
    return mac


def find_branch_opcodes():
    opcodes = []
    for opcode in Instruction.opcodes:
        if opcode[1] == 'rel':
            opcodes.append(opcode[0])

    return opcodes

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    parser.add_argument('output')
    args = parser.parse_args()

    with open(args.filename, "r") as f_in:
        lines = f_in.readlines()

    output = []

    for i, line in enumerate(lines):
        line = line.strip()
        if len(line) > 0:

            chunks = line.split(";")
            code = chunks[0].strip()
            comment = chunks[1] if len(chunks) > 1 else ""
            code_parts = re.split(' +', code)

            if len(code_parts) > 0 and code_parts[0] != '':

                print(code_parts)

                if len(code_parts) > 1 and "=" in code_parts[1]:
                    output.append(add_var(code_parts))

                elif code_parts[0].startswith("!macro"):
                    nb_tabs += 1
                    output.append(gen_macro(code_parts[1]))

                elif code_parts[0].endswith("}"):
                    nb_tabs -= 1
                    output.append('\n')

                elif code_parts[0].startswith("+"):
                    output.append(call_macro(code_parts[0][1:]))

                elif code_parts[0].endswith(":"):
                    output.append(add_label(code_parts[0][0:-1]))

                    if len(code_parts) > 1:
                        opcode = find_opcode(code_parts[1])
                        if opcode:
                            output.append(add_opcode(opcode, code_parts[2:]))

                        elif code_parts[1].startswith("+"):
                            output.append(call_macro(code_parts[1][1:]))

                else:
                    opcode = find_opcode(code_parts[0])
                    if opcode:
                        output.append(add_opcode(opcode, code_parts[1:]))

    with open(args.output, "w") as f_out:
        f_out.writelines(output)
