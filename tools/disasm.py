#!/usr/bin/python3

'''

 Simple 6502 disassembler made in python
 only supports the mos version official opcodes

 Copyright (c) 2018, 2019 Arthur Ferreira

 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be included in
 all copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 THE SOFTWARE.

'''

import argparse
import sys
import os

parser = argparse.ArgumentParser(description='6502 disassembler in python by Arthur Ferreira')
parser.add_argument('-i', metavar='<input file>', type=str, help='the 6502 binary file to disassemble' , required=True)
parser.add_argument('-o', metavar='<output file>', type=str, help='stdout if not specified'            , required=False)
parser.add_argument('-a', metavar='<start address>', type=str, help='in Hexadecimal (FF00 for example)', required=False)
cmdargs = parser.parse_args()

if cmdargs.i:
    try:
        input_file = open(cmdargs.i, 'rb')
    except OSError as e:
        print('ERROR : failed to open input file : ' + cmdargs.i)
        exit(1)
else:
    input_file = sys.stdin

if cmdargs.o:
    if os.path.isfile(cmdargs.o):
        os.remove(cmdargs.o)
    output_file = open(cmdargs.o, 'x')   # fails if file already exists
else:
    output_file = sys.stdout

if cmdargs.a:
    address = int(cmdargs.a, 16)
else:
    address = 0

mnemonics = [
  'BRK', 'ORA', '???', '???', '???', 'ORA', 'ASL', '???', 'PHP', 'ORA', 'ASL', '???', '???', 'ORA', 'ASL', '???',
  'BPL', 'ORA', '???', '???', '???', 'ORA', 'ASL', '???', 'CLC', 'ORA', '???', '???', '???', 'ORA', 'ASL', '???',
  'JSR', 'AND', '???', '???', 'BIT', 'AND', 'ROL', '???', 'PLP', 'AND', 'ROL', '???', 'BIT', 'AND', 'ROL', '???',
  'BMI', 'AND', '???', '???', '???', 'AND', 'ROL', '???', 'SEC', 'AND', '???', '???', '???', 'AND', 'ROL', '???',
  'RTI', 'EOR', '???', '???', '???', 'EOR', 'LSR', '???', 'PHA', 'EOR', 'LSR', '???', 'JMP', 'EOR', 'LSR', '???',
  'BVC', 'EOR', '???', '???', '???', 'EOR', 'LSR', '???', 'CLI', 'EOR', '???', '???', '???', 'EOR', 'LSR', '???',
  'RTS', 'ADC', '???', '???', '???', 'ADC', 'ROR', '???', 'PLA', 'ADC', 'ROR', '???', 'JMP', 'ADC', 'ROR', '???',
  'BVS', 'ADC', '???', '???', '???', 'ADC', 'ROR', '???', 'SEI', 'ADC', '???', '???', '???', 'ADC', 'ROR', '???',
  '???', 'STA', '???', '???', 'STY', 'STA', 'STX', '???', 'DEY', '???', 'TXA', '???', 'STY', 'STA', 'STX', '???',
  'BCC', 'STA', '???', '???', 'STY', 'STA', 'STX', '???', 'TYA', 'STA', 'TXS', '???', '???', 'STA', '???', '???',
  'LDY', 'LDA', 'LDX', '???', 'LDY', 'LDA', 'LDX', '???', 'TAY', 'LDA', 'TAX', '???', 'LDY', 'LDA', 'LDX', '???',
  'BCS', 'LDA', '???', '???', 'LDY', 'LDA', 'LDX', '???', 'CLV', 'LDA', 'TSX', '???', 'LDY', 'LDA', 'LDX', '???',
  'CPY', 'CMP', '???', '???', 'CPY', 'CMP', 'DEC', '???', 'INY', 'CMP', 'DEX', '???', 'CPY', 'CMP', 'DEC', '???',
  'BNE', 'CMP', '???', '???', '???', 'CMP', 'DEC', '???', 'CLD', 'CMP', '???', '???', '???', 'CMP', 'DEC', '???',
  'CPX', 'SBC', '???', '???', 'CPX', 'SBC', 'INC', '???', 'INX', 'SBC', 'NOP', '???', 'CPX', 'SBC', 'INC', '???',
  'BEQ', 'SBC', '???', '???', '???', 'SBC', 'INC', '???', 'SED', 'SBC', '???', '???', '???', 'SBC', 'INC', '???']

addressing = [
  'imp', 'inx', 'imp', 'imp', 'imp', 'zpg', 'zpg', 'imp', 'imp', 'imm', 'acc', 'imp', 'imp', 'abs', 'abs', 'imp',
  'rel', 'iny', 'imp', 'imp', 'imp', 'zpx', 'zpx', 'imp', 'imp', 'aby', 'imp', 'imp', 'imp', 'abx', 'abx', 'imp',
  'abs', 'inx', 'imp', 'imp', 'zpg', 'zpg', 'zpg', 'imp', 'imp', 'imm', 'acc', 'imp', 'abs', 'abs', 'abs', 'imp',
  'rel', 'iny', 'imp', 'imp', 'imp', 'zpx', 'zpx', 'imp', 'imp', 'aby', 'imp', 'imp', 'imp', 'abx', 'abx', 'imp',
  'imp', 'inx', 'imp', 'imp', 'imp', 'zpg', 'zpg', 'imp', 'imp', 'imm', 'acc', 'imp', 'abs', 'abs', 'abs', 'imp',
  'rel', 'iny', 'imp', 'imp', 'imp', 'zpx', 'zpx', 'imp', 'imp', 'aby', 'imp', 'imp', 'imp', 'abx', 'abx', 'imp',
  'imp', 'inx', 'imp', 'imp', 'imp', 'zpg', 'zpg', 'imp', 'imp', 'imm', 'acc', 'imp', 'ind', 'abs', 'abs', 'imp',
  'rel', 'iny', 'imp', 'imp', 'imp', 'zpx', 'zpx', 'imp', 'imp', 'aby', 'imp', 'imp', 'imp', 'abx', 'abx', 'imp',
  'imp', 'inx', 'imp', 'imp', 'zpg', 'zpg', 'zpg', 'imp', 'imp', 'imp', 'imp', 'imp', 'abs', 'abs', 'abs', 'imp',
  'rel', 'iny', 'imp', 'imp', 'zpx', 'zpx', 'zpy', 'imp', 'imp', 'aby', 'imp', 'imp', 'imp', 'abx', 'imp', 'imp',
  'imm', 'inx', 'imm', 'imp', 'zpg', 'zpg', 'zpg', 'imp', 'imp', 'imm', 'imp', 'imp', 'abs', 'abs', 'abs', 'imp',
  'rel', 'iny', 'imp', 'imp', 'zpx', 'zpx', 'zpy', 'imp', 'imp', 'aby', 'imp', 'imp', 'abx', 'abx', 'aby', 'imp',
  'imm', 'inx', 'imp', 'imp', 'zpg', 'zpg', 'zpg', 'imp', 'imp', 'imm', 'imp', 'imp', 'abs', 'abs', 'abs', 'imp',
  'rel', 'iny', 'imp', 'imp', 'imp', 'zpx', 'zpx', 'imp', 'imp', 'aby', 'imp', 'imp', 'imp', 'abx', 'abx', 'imp',
  'imm', 'inx', 'imp', 'imp', 'zpg', 'zpg', 'zpg', 'imp', 'imp', 'imm', 'imp', 'imp', 'abs', 'abs', 'abs', 'imp',
  'rel', 'iny', 'imp', 'imp', 'imp', 'zpx', 'zpx', 'imp', 'imp', 'aby', 'imp', 'imp', 'imp', 'abx', 'abx', 'imp']


while True:

    b = input_file.read(1)
    if not b:
        break

    opcode = int.from_bytes(b, byteorder='little', signed=False)
    mnemonic = mnemonics[opcode]
    output_file.write(hex(address).replace('0x', '').upper().zfill(4) + '    ' +
                      hex(opcode).replace('0x', '').upper().zfill(2) + ' ')
    address += 1

    # implied
    if addressing[opcode] == 'imp':
        output_file.write('        ' + mnemonic + '\n')
        continue

    # accumulator
    if addressing[opcode] == 'acc':
        output_file.write('        ' + mnemonic + ' A\n')
        continue

    # one byte arguments :
    b = input_file.read(1)
    if not b:
        sys.stderr.write('ERROR : unexpected end of file')
        break

    operand = int.from_bytes(b, byteorder='little', signed=False)
    operand = hex(operand).replace('0x', '').upper().zfill(2)
    operand_b = operand[0:2] + ' ' + operand[2:]

    output_file.write(operand_b)
    address += 1

    # immediate
    if addressing[opcode] == 'imm':
        output_file.write('      ' + mnemonic + ' #$' + operand + '\n')
        continue

    # relative
    if addressing[opcode] == 'rel':
        output_file.write('      ' + mnemonic + ' $' + operand + '\n')
        continue

    # zero page
    if addressing[opcode] == 'zpg':
        output_file.write('      ' + mnemonic + ' $' + operand + '\n')
        continue

    # zero page, X indexed
    if addressing[opcode] == 'zpx':
        output_file.write('      ' + mnemonic + ' $' + operand + ',X\n')
        continue

    # zero page, Y indexed
    if addressing[opcode] == 'zpy':
        output_file.write('      ' + mnemonic + ' $' + operand + ',Y\n')
        continue

    # X indexed, indirect
    if addressing[opcode] == 'inx':
        output_file.write('      ' + mnemonic + ' $(' + operand + ',X)\n')
        continue

    # indirect, Y indexed
    if addressing[opcode] == 'iny':
        output_file.write('      ' + mnemonic + ' $(' + operand + '),Y\n')
        continue

    # adding a second byte to the argument :
    b = input_file.read(1)
    if not b:
        sys.stderr.write('ERROR : unexpected end of file')
        break

    operand2 = int.from_bytes(b, byteorder='little', signed=False)
    operand2 = hex(operand2).replace('0x', '').upper().zfill(2)
    output_file.write(operand2 + '    ' + mnemonic)
    operand = operand2 + operand
    address += 1

    # indirect
    if addressing[opcode] == 'ind':
        output_file.write(' $(' + operand + ')\n')
        continue

    # absolute
    if addressing[opcode] == 'abs':
        output_file.write(' $' + operand + '\n')
        continue

    # absolute, X indexed
    if addressing[opcode] == 'abx':
        output_file.write(' $' + operand + ',X\n')
        continue

    # absolute, Y indexed
    if addressing[opcode] == 'aby':
        output_file.write(' $' + operand + ',Y\n')
        continue

input_file.close()
output_file.close()
# <end of program>