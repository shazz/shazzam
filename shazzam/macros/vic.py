import math
import logging
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a
from shazzam.macros.aliases import color, vic

logger = logging.getLogger("shazzam")

# ------------------------------------------------------------------------------------------
# clear_screen(clear_byte, screen, use_ptr)
# clear the ram (all 1024 bytes) from a given address with a given character
# ------------------------------------------------------------------------------------------
def clear_screen(clear_byte: int, screen: int, use_ptr: bool):
    mlabel = get_anonymous_label("loop")

    if use_ptr:
        lda(at(clear_byte))
    else:
        lda(imm(clear_byte))
    ldx(imm(0))
    label(mlabel)
    sta(at(screen), x)
    sta(at(screen) + 0x100, x)
    sta(at(screen) + 0x200, x)
    sta(at(screen) + 0x300, x)
    inx()
    bne(at(mlabel))

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
        lda(imm(dd02))
        sta(at(dd02))
    else:
        dd00 = utils.generate_dd00(bank_start)
        lda(imm(dd00))
        sta(at(dd00))

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

# ------------------------------------------------------------------------
# vsync
# ------------------------------------------------------------------------
def vsync():
    l_wait1 = get_anonymous_label("l_wait1")
    l_wait2 = get_anonymous_label("l_wait2")

    label(l_wait1)
    lda(at(vic.scr_ctrl))
    bpl(at(l_wait1))

    label(l_wait2)
    lda(at(vic.scr_ctrl))
    bmi(at(l_wait2))

# ------------------------------------------------------------------------
# Init sprites
# ------------------------------------------------------------------------
def init_sprites(nb, data, spd, bank, scr_mem):

    # set sprites specific color
    for i in range(nb):
        lda(imm(spd.colors[i]))
        sta(at(vic.sprite0_color+i))            # set main sprite color

    # set extra colors
    lda(imm(0x0e))                              # spd.multicol1
    sta(at(vic.sprite_extra_col1))

    lda(imm(spd.multicol2))
    sta(at(vic.sprite_extra_col2))

    # set sprites pointers
    sprite_balls_adr = (data-bank)/64
    lda(imm(sprite_balls_adr))
    for i in range(nb):
        sta(at(bank + scr_mem + 0x3f8 + i))

