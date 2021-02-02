# if shazzam not installed
import sys
sys.path.append(".")

from reloading import reloading
from shazzam.Segment import SegmentType
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a
from shazzam.macros.aliases import color, vic
import shazzam.macros.sys as sys
from shazzam.drivers.assemblers.CC65 import CC65

# define your cross assembler
assembler = CC65("cc65", "third_party/cc65/bin/cl65")
prefs = assembler.get_code_format()
set_prefs(default_code_segment=assembler.get_code_segment(),
          code_format=prefs.code,
          comments_format=prefs.comments,
          directive_prefix=prefs.directive)

@reloading
def code():

    # define here or anywhere, doesn't matter, your variables

    with segment(0x0801, "start") as s:

        sys.basic_start()
        label("init")

        # Fibonacci calculator in 6502 asm
        # by Pedro Franceschi (pedrohfranceschi@gmail.com)
        # the accumulator in the end will hold the Nth fibonacci number

        ldx(imm(0x01))      # x = 1
        stx(at(0x00))       # stores x

        sec()               # clean carry#
        ldy(imm(0x07))      # calculates 7th fibonacci number (13) (change here if you want to calculate another number)
        tya()               # transfer y register to accumulator
        sbc(imm(0x03))      # handles the algorithm iteration counting
        tay()               # transfer the accumulator to the y register

        clc()               # clean carry
        lda(imm(0x02))      # a = 2
        sta(at(0x01))       # stores a

        label("loop")
        ldx(at(0x01))       # x = a
        adc(at(0x00))       # a += x
        sta(at(0x01))       # stores a
        stx(at(0x00))       # stores x
        dey()               # y -= 1
        bne(rel_at("loop")) # jumps back to loop if Z bit != 0 (y's decremention isn't zero yet)

        cpu, mmu, cycles_used = s.emulate(start_address="init", debug_mode=True)
        assert cpu.r.a == 13, f"7th fibonacci number is 13 not {cpy.r.a}"

    # generate listing
    gen_code(format_code=prefs, gen_listing=True)

    # finally assemble segments to PRG using cross assembler then crunch it!
    assemble_prg(assembler, start_address=0x0801)

if __name__ == "__main__":
    generate(code, "step_by_step")
