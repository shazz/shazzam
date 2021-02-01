from shazzam.Cruncher import Cruncher
from shazzam.py64gen import RegisterACC as a
from shazzam.py64gen import RegisterX as x
from shazzam.py64gen import RegisterY as y
from shazzam.py64gen import *

import os
import logging

class C64f(Cruncher):

    def __init__(self, exe_path: str = None):
        self.logger = logging.getLogger("shazzam")
        cmd_prg_template = None
        cmd_bin_template = [exe_path, "FILENAME_TO_SET", "OUTPUT_TO_SET"]

        super().__init__("C64f", exe_path, cmd_prg_template, cmd_bin_template)

    def generate_depacker_routine(self, address: int, use_fast: bool = True) -> None:

        apd_bitbuffer   = 0xf5
        apd_src         = 0xf6
        apd_length      = 0xf8
        apd_offset      = 0xfa
        apd_source      = 0xfc
        apd_dest        = 0xfe

        if use_fast:

            def incsrc():
                incsr1 = get_anonymous_label("incsr1")
                inc(at(apd_src))
                bne(rel_at(incsr1))
                inc(at(apd_src)+1)
                label(incsr1)

            def getbyte():
                lda(ind_at(apd_src), y)
                incsrc()

            def putbyte():
                putbyt = get_anonymous_label("putbyt")
                sta(ind_at(apd_dest), y)
                inc(at(apd_dest))
                bne(rel_at(putbyt))
                inc(at(apd_dest)+1)
                label(putbyt)

            def getbit():
                getbi1 = get_anonymous_label("getbi1")
                asl(at(apd_bitbuffer))
                bne(rel_at(getbi1))
                tax()
                getbyte()
                rol(a)
                sta(at(apd_bitbuffer))
                txa()
                label(getbi1)

            def getbitd():
                getbi2 = get_anonymous_label("getbi2")
                asl(at(apd_bitbuffer))
                bne(rel_at(getbi2))
                getbyte()
                rol(a)
                sta(at(apd_bitbuffer))
                label(getbi2)

            label("exitdz")
            rts()

            label("dc64f", is_global=True)

            lda(imm(0x80))
            sta(at(apd_bitbuffer))
            ldy(imm(0))
            sty(at(apd_length+1))

            label("copyby")

            getbyte()
            putbyte()
            label("mainlo")

            getbitd()
            bcc(rel_at("copyby"))
            sty(at(apd_offset)+1)
            getbitd()
            lda(imm(1))
            bcs(rel_at("contie"))
            label("lenval")

            getbit()
            rol(a)
            rol(at(apd_length)+1)
            getbit()
            bcc(rel_at("lenval"))
            label("contie")

            adc(imm(0))
            sta(at(apd_length))
            beq(rel_at("exitdz"))
            lda(ind_at(apd_src), y)
            bpl(rel_at("toffen"))
            incsrc()
            getbit()
            rol(at(apd_offset)+1)
            getbit()
            rol(at(apd_offset)+1)
            getbit()
            rol(at(apd_offset)+1)
            getbit()
            bcc(rel_at("offend"))
            inc(at(apd_offset)+1)
            sbc(imm(0x80))
            jmp(at("offend"))

            label("toffen")
            incsrc()

            label("offend")
            sec()
            sbc(at(apd_dest))
            eor(imm(0b11111111))
            sta(at(apd_source))
            lda(at(apd_offset)+1)
            sbc(at(apd_dest)+1)
            eor(imm(0b11111111))
            sta(at(apd_source)+1)
            lda(at(apd_length)+1)
            beq(rel_at("skip"))

            label("loop1")
            lda(ind_at(apd_source), y)
            sta(ind_at(apd_dest), y)
            iny()
            bne(rel_at("loop1"))
            inc(at(apd_source)+1)
            inc(at(apd_dest)+1)
            dec(at(apd_length)+1)
            bne(rel_at("loop1"))

            label("skip")
            ldx(at(apd_length))
            beq(rel_at("lopend"))

            label("loop2")
            lda(ind_at(apd_source), y)
            sta(ind_at(apd_dest), y)
            iny()
            dex()
            bne(rel_at("loop2"))
            tya()
            ldy(imm(0))
            adc(at(apd_dest))
            sta(at(apd_dest))
            bcc(rel_at("lopend"))
            inc(at(apd_dest+1))

            label("lopend")
            jmp(at("mainlo"))

        else:

            def incsrc():
                incsr1 = get_anonymous_label("incsr1")
                inc(at(apd_src))
                bne(rel_at(incsr1))
                inc(at(apd_src)+1)
                label(incsr1)


            label("dc64f", is_global=True)
            lda(imm(0x80))
            sta(at(apd_bitbuffer))
            ldy(imm(0))

            label("copyby")
            lda(ind_at(apd_src), y)
            incsrc()
            sta(ind_at(apd_dest), y)
            inc(at(apd_dest))
            bne(rel_at("mainlo"))
            inc(at(apd_dest)+1)

            label("mainlo")
            jsr(at("getbit"))
            bcc(rel_at("copyby"))
            sty(at(apd_length)+1)
            sty(at(apd_offset)+1)
            lda(imm(1))
            jmp(at("here"))

            label("lenval")
            jsr(at("getbit"))
            rol(a)
            rol(at(apd_length)+1)

            label("here")
            jsr(at("getbit"))
            bcc(rel_at("lenval"))
            adc(imm(0))
            sta(at(apd_length))
            beq(rel_at("getbi1"))
            lda(ind_at(apd_src), y)
            incsrc()
            asl(a)
            bcc(rel_at("offend"))
            pha()
            lda(imm(0b00010000))

            label("nextbi")
            jsr(at("getbit"))
            rol(a)
            bcc(rel_at("nextbi"))
            adc(imm(0))
            lsr(a)
            sta(at(apd_offset)+1)
            pla()

            label("offend")
            ror(a)
            sec()
            sbc(at(apd_dest))
            eor(imm(0b11111111))
            sta(at(apd_source))
            lda(at(apd_offset)+1)
            sbc(at(apd_dest)+1)
            eor(imm(0b11111111))
            sta(at(apd_source)+1)
            ldx(at(apd_length))
            beq(rel_at("loop2"))

            label("loop1")
            lda(ind_at(apd_source), y)
            sta(ind_at(apd_dest), y)
            iny()
            dex()
            bne(rel_at("loop1"))
            inc(at(apd_source)+1)
            inc(at(apd_dest)+1)

            label("loop2")
            dec(at(apd_length)+1)
            bpl(rel_at("loop1"))
            tya()
            ldy(imm(0))
            adc(at(apd_dest))
            sta(at(apd_dest))
            bcs(rel_at("mainlo"))
            dec(at(apd_dest)+1)
            jmp(at("mainlo"))

            label("getbit")
            asl(at(apd_bitbuffer))
            bne(rel_at("getbi1"))
            tax()
            lda(ind_at(apd_src), y)
            incsrc()
            rol(a)
            sta(at(apd_bitbuffer))
            txa()

            label("getbi1")
            rts()