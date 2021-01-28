# if shazzam not installed
import sys
sys.path.append(".")

from reloading import reloading
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a
from shazzam.macros.aliases import color, vic
from shazzam.drivers.assemblers.CC65 import CC65

# define your cross assembler
assembler = CC65("cc65", "/home/shazz/projects/c64/bin/cl65")
prefs = assembler.get_code_format()
set_prefs(default_code_segment=assembler.get_code_segment(),
          code_format=prefs.code,
          comments_format=prefs.comments,
          directive_prefix=prefs.directive)

@reloading
def code():

    # define here or anywhere, doesn't matter, your variables


    # CC65 generates basic header, no macro needed just to define the CODE segment
    with segment(0x0801, assembler.get_code_segment()) as s:

        jsr(at(0x0e544))        # ROM routine to clear the screen Clear screen.Input: – Output: – Used registers: A, X, Y.

        lda(imm(0))
        sta(at(vic.border_col)) # set border color
        sta(at(vic.bck_col))    # and window color to black

        lda(imm(0x18))          # a = 0x018 = 0001 100 0
        sta(at(0xd018))         # set Memory setup register to char memory 4 (3 bits 0x2000-$27FF)
                                # screen memory to 1 ($0400-$07FF)

        ldx(imm(0))
        label("write")
        lda(at("msg"),x)        # a = charAt(msg)
        jsr(at(0xffd2))         # KERNAL function to write to output:
                                # CHROUT. Write byte to default output.
                                # (If not screen, must call OPEN and CHKOUT beforehands.)
                                # Input: A = Byte to write.
                                # Output: –
                                # Used registers: –
                                # Real address: ($0326),$F1CA.
        inx()                   # x++
        cpx(imm(40))            # loop if x != 40 (msg length)
        bne(rel_at("write"))

        ldx(imm(0))             # reset x
        label("setcolor")
        lda(imm(0x05))          # a = 5  => color for font is green
        sta(at(0xd800),x)       # colorRAM(x) = 5
        inx()                   # x++
        cpx(imm(40))            # do it 40 times
        bne(rel_at("setcolor"))

        label("loop")
        jmp(at("loop"))

        label("msg")
        byte("WELCOME TO THE MATRIX - THE 8BITS MATRIX")

    with segment(0x1ffe, "charset") as s:       #0x2000 - 2 header bytes
        incbin(open("resources/aeg_collection_12.64c", "rb").read())

    # generate listing
    gen_code(format_code=prefs, gen_listing=True)

    # finally assemble segments to PRG using cross assembler then crunch it!
    assemble_prg(assembler, start_address=0x0801)

if __name__ == "__main__":
    generate(code, "hello_world")
