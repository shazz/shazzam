import math
import logging
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a
from shazzam.macros.aliases import color, vic
from shazzam.macros.vasyl import *

logger = logging.getLogger("shazzam")

# BeamRacer * https://beamracer.net
# Video and Display List coprocessor board for the Commodore 64
# Copyright (C)2019-2020 Mad Hackers Lab
#
# https://github.com/madhackerslab/
#
# Header file for BeamRacer VASYL chip
# See https://docs.beamracer.net/ for more information.
#
# Ported by Shazz / TRSi
# Copyright (C)2021 TRSi

tmp_ptr     = 251
tmp_ptr2    = 253

def init(vasyl_segment_load, vasyl_segment_size, autostart : bool = False):

    import shazzam.macros.vasyl

    # this only gets assembled if there is no knocking ahead of it
    # .ifnref knock_knock
    if autostart:
        copy_and_activate_dlist()

        label("autostart")
        jsr(at("knock_knock"))

        ldx(imm(0x2e))
        label("vlib_preserve_loop")
        lda(at(0xd000), x)
        sta(at("vlib_preserve_vic"), x)
        dex()
        bpl(rel_at("vlib_preserve_loop"))

        jsr(at("copy_and_activate_dlist"))
        label("vlib_keyloop")
        jsr(at(0xffe4))                     # check if key pressed
        beq(rel_at("vlib_keyloop"))

        cmp(imm(3))
        beq(rel_at("vlib_no_restore"))

        lda(imm(0))                         # turn off display list
        sta(at(VREG_CONTROL))

        ldx(imm(0x2e))
        label("vlib_preserve_loop2")
        lda(at("vlib_preserve_vic"), x)
        sta(at(0xd000), x)
        dex()
        bpl(rel_at("vlib_preserve_loop2"))
        label("vlib_no_restore")
        rts()
        label("vlib_preserve_vic")
        byte([0] * 47)                      # .res 47
    # .endif


# .ifref knock_knock
    # Attempt activation of the BeamRacer, on failure (BeamRacer missing) exits the program
    label("knock_knock", is_global=True)
    ldx(imm(255))
    cpx(at(VREG_CONTROL))
    bne(rel_at("vlib_active"))

    lda(imm(0x42))
    sta(at(VREG_CONTROL))

    lda(imm(0x52))
    sta(at(VREG_CONTROL))
    cpx(at(VREG_CONTROL))
    bne(rel_at("vlib_active"))

    # exit the program
    pla()
    pla()
    label("vlib_active")
    # jsr(at("print_info"))
    rts()
# .endif

def copy_and_activate_dlist(vasyl_segment_load, vasyl_segment_size):
    copy_dlist(vasyl_segment_load, vasyl_segment_size)

# .ifref copy_and_activate_dlist
    # Copy a dlist to local RAM and activate it:
    # the contents of segment "VASYL" is copied to address 0 in local RAM and then the display list is activated.
    label("copy_and_activate_dlist")
    jsr(at("copy_dlist"))

    # start using the new Display List
    lda(imm("<dl_start"))
    sta(at(VREG_DLIST))
    lda(imm(">dl_start"))
    sta(at(VREG_DLIST + 1))
    lda(imm(1 << CONTROL_DLIST_ON_BIT))
    sta(at(VREG_CONTROL))
    rts()
# .endif

def copy_dlist(vasyl_segment_load, vasyl_segment_size):
    copy_to_lmem()

# .ifref copy_dlist
    # Copy a dlist to local RAM:
    # the contents of segment "VASYL" is copied to address 0 in local RAM.
    label("copy_dlist")
    lda(imm(vasyl_segment_load & 0xff))
    sta(at(tmp_ptr))
    lda(imm(vasyl_segment_load >> 8))
    sta(at(tmp_ptr + 1))
    lda(imm(0))
    sta(at(tmp_ptr2))
    sta(at(tmp_ptr2) + 1)

    lda(imm(vasyl_segment_size % 0xff))
    ldx(imm(vasyl_segment_size >> 8))
    jmp(at("copy_to_lmem"))
# .endif

def copy_to_lmem():
# .ifref copy_to_lmem
    # Copy data to lram:
    # 0xFA/0xFB - source
    # 0xFC/0xFD - destination (in VASYL's local RAM)
    # AX - lo/hi byte count
    label("copy_to_lmem")
    ldy(at(tmp_ptr2))
    sty(at(VREG_ADR0))
    ldy(at(tmp_ptr2) + 1)
    sty(at(VREG_ADR0) + 1)
    ldy(imm(1))
    sty(at(VREG_STEP0))

    clc()
    adc(at(tmp_ptr))
    sta(at(tmp_ptr2))
    txa()
    adc(at(tmp_ptr) + 1)
    sta(at(tmp_ptr2) + 1)

    ldy(imm(0))
    label("vlib_loop")
    lda(ind_at(tmp_ptr), y)
    sta(at(VREG_PORT0))
    inc(at(tmp_ptr))
    bne(rel_at("vlib_no_carry"))
    inc(at(tmp_ptr) + 1)
    label("vlib_no_carry")
    lda(at(tmp_ptr2))
    cmp(at(tmp_ptr))
    bne(rel_at("vlib_loop"))
    lda(at(tmp_ptr2) + 1)
    cmp(at(tmp_ptr) + 1)
    bne(rel_at("vlib_loop"))
    rts()
# .endif

def set_pages():
# .ifref set_pages
    # Set VASYL memory pages to a value.
    # A - value
    # Y - starting page
    # X - page count
    UNROLL_FACTOR = 8
    label("set_pages")
    sty(at(VREG_ADR0) + 1)
    ldy(imm(1))
    sty(at(VREG_STEP0))
    dey()                           # 0
    sty(at(VREG_ADR0))
    dey()                           # 255
    sta(at(VREG_PORT0))             # Store one byte.
    label("vlib_next_page")
    sty(at(VREG_REP0))              # Repeat 255 times on first iteration, 256 on subsequent ones.
    label("vlib_waitrep")
    ldy(at(VREG_REP0))              # Wait for REP transfer to end.
    bne(rel_at("vlib_waitrep"))
    dex()
    bne(rel_at("vlib_next_page"))
    rts()
# .endif

def print_info():
# .ifref print_info
    # Print information about VASYL and VIC-II versions.
    label("print_info")
    lda(imm("<version_text"))
    ldy(imm(">version_text"))
    jsr(at(0xab1e))                 # print null terminated string
    lda(at(VREG_DLSTROBE))
    lsr(a)
    lsr(a)
    lsr(a)
    tax()

    lda(imm(0))
    jsr(at(0xbdcd))                 # print XA as unsigned integer
    lda(imm("<type_text"))
    ldy(imm(">type_text"))
    jsr(at(0xab1e))                 # print null terminated string

    lda(at(VREG_DLSTROBE))
    andr(imm(0x07))
    tax()
    lda(at("type_table_lo"), x)
    ldy(at("type_table_hi"), x)
    jmp(at(0xab1e))                 # print null terminated string

    label("version_text")
    byte(["vasyl ID: ", 0])

    label("type_text")
    byte([ 0xd,"vic-ii type  : ", 0])

    l_ntsc = label("type_ntsc")
    byte(["ntsc (6567r8 or 8562)", 0])

    l_pal = label("type_pal")
    byte(["pal (6569 or 8565)", 0])

    l_paln = label("type_paln")
    byte(["pal-n (6572)", 0])

    l_ntsc_old = label("type_ntsc_old")
    byte(["ntsc (6567r56a)", 0])

    l_unknown = label("type_unknown")
    byte(["unknown", 0])

    label("type_table_lo")
    byte([l_ntsc.value & 0xff, l_unknown.value & 0xff, l_unknown.value & 0xff, l_ntsc_old.value & 0xff])
    byte([l_paln.value & 0xff, l_unknown.value & 0xff, l_pal.value & 0xff, l_unknown.value & 0xff])

    label("type_table_hi")
    byte([l_ntsc.value >> 8, l_unknown.value >> 8, l_unknown.value >> 8, l_ntsc_old.value >> 8])
    byte([l_paln.value >> 8, l_unknown.value >> 8, l_pal.value >> 8, l_unknown.value >> 8])

# .endif
