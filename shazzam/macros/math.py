import math
import logging
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a
from shazzam.macros.aliases import color, vic

logger = logging.getLogger("shazzam")

# ------------------------------------------------------------------------
# add16(n1, n2, res)
# 16 bits addition
# ------------------------------------------------------------------------
def add16(n1, n2, res):
    clc()
    lda(at(n1))
    adc(at(n2))
    sta(at(res)+0)
    lda(at(n1)+1)
    adc(at(n2)+1)
    sta(at(res)+1)

# ------------------------------------------------------------------------
# add8_to_16(val, res)
# add a 8bits value to a 16bits value
# ------------------------------------------------------------------------
def add8_to_16(val, res):
    mlabel = get_anonymous_label("ok")

    clc()
    lda(at(res))
    adc(imm(val))
    sta(at(res))
    bcc(at(mlabel))
    inc(at(res)+1)
    label(mlabel)

# ------------------------------------------------------------------------
# sub8_to_16(val, res)
# substracts a 8bits value to a 16bits value
# ------------------------------------------------------------------------
def sub8_to_16(val, res):
    mlabel = get_anonymous_label("ok")

    sec()
    lda(at(res))
    sbc(imm(val))
    sta(at(res))
    bcs(at(mlabel))
    dec(at(res)+1)
    label(mlabel)

# ------------------------------------------------------------------------
# mov16imm(v, res)
# write in a 16bits memory address
# ------------------------------------------------------------------------
def mov16imm(v, res):

    lda(imm('>' + v))
    sta(at(res)+0)
    lda(imm('<' + v))
    sta(at(res)+1)

# ------------------------------------------------------------------------
# inc16(mem)
# Add a 1 to a 16bits value
# ------------------------------------------------------------------------
def inc16(mem):

    l_ok = get_anonymous_label("skip")

    inc(at(mem)+0)
    bne(at(l_ok))
    inc(at(mem)+1)
    label(l_ok)

# ------------------------------------------------------------------------
# dec16(val)
# Decrement 1 to a 16bits value
# ------------------------------------------------------------------------
def dec16(mem):

    l_skip = get_anonymous_label("skip")

    lda(at(mem) + 0)       # Test if the LSB is zero
    bne(at(l_skip))        # If it isn't we can skip the next instruction
    dec(at(mem) + 1)       # Decrement the MSB when the LSB will underflow
    label(l_skip)
    dec(at(mem) + 0)       # Decrement the LSB


# ------------------------------------------------------------------------
# sub16(n1, n2, res)
# subtracts number 2 from number 1 and writes result out
# ------------------------------------------------------------------------
def sub16(n1, n2, res):

    sec()                   # set carry for borrow purpose
    lda(at(n1))
    sbc(at(n2))             # perform subtraction on the LSB
    sta(at(res) + 0)
    lda(at(n1) + 1)         # do the same for the MSBs, with carry
    sbc(at(n2) + 1)	        # set according to the previous result
    sta(at(res) + 1)
