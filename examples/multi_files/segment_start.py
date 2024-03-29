# if shazzam not installed
import sys
sys.path.append(".")

from shazzam.Segment import SegmentType
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a
from shazzam.macros.aliases import color, vic
import shazzam.macros.sys as sys

with segment(0x0801, "start") as s:

    sys.basic_start()

    jsr(at(0xe544))        # ROM routine to clear the screen Clear screen.Input: – Output: – Used registers: A, X, Y.

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


