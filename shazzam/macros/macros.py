import math
import logging
from shazzam.py64gen import *
from shazzam.py64gen import Register as r

logger = logging.getLogger("shazzam")

# ------------------------------------------------------------------------
# add16(res, n1, n2)
# 16 bits addition
# ------------------------------------------------------------------------
def add16(res, n1, n2):
    clc()
    lda(abs_adr=n1)
    adc(abs_adr=n2)
    sta(abs_adr=res+0)
    lda(abs_adr=n1+1)
    adc(abs_adr=n2+1)
    sta(abs_adr=res+1)

# ------------------------------------------------------------------------
# add8_to_16(n, val)
# add a 8bits value to a 16bits value
# ------------------------------------------------------------------------
def add8_to_16(n, val):
    mlabel = get_anonymous_label("ok")

    clc()
    lda(abs_adr=n)
    adc(value=val)
    sta(abs_adr=n)
    bcc(label=mlabel)
    inc(abs_adr=n+1)
    label(name=mlabel)

# ------------------------------------------------------------------------
# sub8_to_16(n, val)
# substracts a 8bits value to a 16bits value
# ------------------------------------------------------------------------
def sub8_to_16(n, val):
    mlabel = get_anonymous_label("ok")

    sec()
    lda(abs_adr=n)
    sbc(value=val)
    sta(abs_adr=n)
    bcs(label=mlabel)
    dec(abs_adr=n+1)
    label(name=mlabel)

# ------------------------------------------------------------------------
# waste_cycles(n)
# setup stable raster irq note: cannot be set on a badline or the second
# interrupt happens before we store the stack pointer (among other things)
# ------------------------------------------------------------------------
def waste_cycles(n):
    nops = math.floor(n/2)
    rem = n & 1
    c = n
    if rem == 0:
        for i in range(nops):
            nop()
            c = c - 2
    else:
        for i in range(nops-1):
            nop()
            c = c - 2
        bit(abs_adr=0xfe)
        c = c - 3
    if c != 0:
        logger.error(f"error {c} cycles remaining on {n}")
        raise RuntimeError("should not be here")

# ------------------------------------------------------------------------------------------
# clear_screen(clear_byte, screen, use_ptr)
# clear the ram (all 1024 bytes) from a given address with a given character
# ------------------------------------------------------------------------------------------
def clear_screen(clear_byte: int, screen: int, use_ptr: bool):
    mlabel = get_anonymous_label("loop")

    if use_ptr:
        lda(abs_adr=clear_byte)
    else:
        lda(imm=clear_byte)
    ldx(imm=0)
    label(mlabel)
    sta(abs_adr=screen, index=r.X)
    sta(abs_adr=screen + 0x100, index=r.X)
    sta(abs_adr=screen + 0x200, index=r.X)
    sta(abs_adr=screen + 0x300, index=r.X)
    inx()
    bne(label=mlabel)

# ------------------------------------------------------------------------------------------
# basic start
# generate a compatible basic header
# ------------------------------------------------------------------------------------------
def basic_start(addr):
    with segment(0x0801, "entry") as s:
        byte(0x0c)
        byte(0x08)
        byte(0x00)
        byte(0x00)
        byte(0x9e)

        if (addr >= 10000):
            byte(0x30 + (addr//10000)%10)

        if (addr >= 1000):
            byte(0x30 + (addr//1000)%10)

        if (addr >= 100):
            byte(0x30 + (addr//100)%10)

        if (addr >= 10):
            byte(0x30 + (addr//10)%10)

        byte(0x30 + addr % 10)
        byte(0x0, 0x0, 0x0)

        logger.info(f"after basic header, program start at {s.get_stats()['current_address']}")

# ------------------------------------------------------------------------------------------
# Setup VIC bacnk
# Usind dd00 or dd02
# ------------------------------------------------------------------------------------------
def setup_vic_bank(bank_start, use_dd02):

    def generate_dd00(bank_start):
        if bank_start == 0:
            reg = 0b11
        elif bank_start == 0x4000:
            reg = 0b10
        elif bank_start == 0x8000:
            reg = 0b01
        elif bank_start == 0xC000:
            reg = 0b00
        else:
            logger.error(f"Unknown bank {bank_start}")

        return reg

    def generate_dd02(bank_start):
        if bank_start == 0:
            reg = 0b00
        elif bank_start == 0x4000:
            reg = 0b01          # reverse from d000
        elif bank_start == 0x8000:
            reg = 0b10          # reverse from d000
        elif bank_start == 0xC000:
            reg = 0b11
        else:
            logger.error(f"Unknown bank {bank_start}")

        return reg

    def generate_full_dd02(bank_start):
        if bank_start == 0:
            reg = 0x3c
        elif bank_start == 0x4000:
            reg = 0x3d          # reverse from d000
        elif bank_start == 0x8000:
            reg = 0x3e          # reverse from d000
        elif bank_start == 0xC000:
            reg = 0x3f
        else:
            logger.error(f"Unknown bank {bank_start}")

        return reg

    if use_dd02:
        dd02 = utils.generate_full_dd02(bank_start)

        logger.info("bank", bank_start, BITMAP_ADDR, SCREEN_MEM_ADDR, "dd02", dd02, "d018", utils.generate_d018(CHAR_MEM_ADDR, BITMAP_ADDR, SCREEN_MEM_ADDR), d018, "mixed", (dd02 | d018))
        lda(imm=dd02)
        sta(abs_adr=dd02)
    else:
        dd00 = utils.generate_dd00(bank_start)
        lda(imm=dd00)
        sta(abs_adr=dd00)

# ------------------------------------------------------------------------------------------
# Generate d018 register
# ------------------------------------------------------------------------------------------
def generate_d018(charmem, bitmap, screenmem):
    mapping_charmem = {
        0x0000: 0b000,
        0x0800: 0b001,
        0x1000: 0b010,
        0x1800: 0b011,
        0x2000: 0b100,
        0x2800: 0b101,
        0x3000: 0b110,
        0x3800: 0b111
    }
    mapping_bitmap = {
        0x0000: 0b000,
        0x2000: 0b100
    }
    mapping_screenmem = {
        0x0000: 0b0000,
        0x0400: 0b0001,
        0x0800: 0b0010,
        0x0C00: 0b0011,
        0x1000: 0b0100,
        0x1400: 0b0101,
        0x1800: 0b0110,
        0x1C00: 0b0111,
        0x2000: 0b1000,
        0x2400: 0b1001,
        0x2800: 0b1010,
        0x2C00: 0b1011,
        0x3000: 0b1100,
        0x3400: 0b1101,
        0x3800: 0b1110,
        0x3C00: 0b1111
    }

    logger.debug(charmem, mapping_charmem[parseInt(charmem)])
    logger.debug(bitmap, mapping_bitmap[bitmap])
    logger.debug(screenmem, mapping_screenmem[screenmem])

    reg = ((mapping_charmem[charmem] << 1) | (mapping_bitmap[bitmap] << 1) | (mapping_screenmem[screenmem] << 4))
    return reg