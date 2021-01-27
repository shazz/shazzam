import subprocess
import os
import logging

from shazzam.Cruncher import Cruncher
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a

class Apultra(Cruncher):

    def __init__(self, exe_path: str):

        cmd_prg_template = None
        cmd_bin_template = [exe_path, "FILENAME_TO_SET", "OUTPUT_TO_SET"]
        super().__init__("apultra", exe_path, cmd_prg_template, cmd_bin_template)

    def generate_depacker_routine(self, address: int) -> None:
        """generate_depacker_routine

        Args:
            address (int): [description]

        Raises:
            NotImplementedError: [description]
        """
        # Zero page locations
        apl_gamma2_hi     = 0xF6
        apl_bitbuf        = 0xF7
        apl_offset        = 0xF8
        apl_winptr        = 0xFA
        apl_srcptr        = 0xFC
        apl_dstptr        = 0xFE

        # Read a byte from the source into A. Trashes X
        def APL_GET_SRC():
            src_page_done = get_anonymous_label("src_page_done")
            lda(ind_at(apl_srcptr),y)
            ldx(at(apl_srcptr)+0)
            bne(rel_at(src_page_done))
            dec(at(apl_srcptr)+1)
            label(src_page_done)
            dec(at(apl_srcptr+0))

        # Write a byte to the destinatipn
        def APL_PUT_DST():
            dst_page_done = get_anonymous_label("dst_page_done")
            sta(ind_at(apl_dstptr),y)
            lda(at(apl_dstptr)+0)
            bne(rel_at(dst_page_done))
            dec(at(apl_dstptr)+1)
            label(dst_page_done)
            dec(at(apl_dstptr)+0)

        # Read one bit from the source into the carry, trash A

        def APL_GET_BIT():
            has_bits = get_anonymous_label("has_bits")
            asl(at(apl_bitbuf))
            bne(rel_at(has_bits))
            jsr(at("apl_load_bits"))
            label(has_bits)

        # Read one bit from the source into the carry, preserve A
        def APL_GET_BIT_SAVEA():
            has_bits = get_anonymous_label("has_bits")
            asl(at(apl_bitbuf))
            bne(rel_at(has_bits))
            pha()
            jsr(at("apl_load_bits"))
            pla()
            label(has_bits)

        # Decompress aPLib data backwards
        label("apl_decompress")
        lda(imm(0x80))                      # initialize empty bit queue
        sta(at(apl_bitbuf))               # plus bit to roll into carry
        ldy(imm(0x00))                      # clear Y for indirect addr

        label("copy_literal")
        APL_GET_SRC()                  # read literal from source
        label("write_literal")
        APL_PUT_DST()                  # write literal to destination

        ldx(imm(0x00))                      # clear 'follows match' flag

        label("next_token")
        APL_GET_BIT()                  # read 'literal or match' bit
        bcc(rel_at("copy_literal"))             # if 0") literal

        APL_GET_BIT()                  # read '8+n bits or other' bit
        bcc(rel_at("long_match"))               # if 10x") long 8+n bits match

                                        # 11x") other type of match

        APL_GET_BIT()                  # read '7)+1) match or short literal' bit
        bcs(rel_at("short_match"))              # if 111") 4 bit offset for 1-byte copy

        APL_GET_SRC()                  # read low byte of offset + length bit
        lsr(a)                           # shift offset into place, len bit into carry
        beq(rel_at("done"))                     # check for EOD
        sta(at(apl_offset)+0)             # store low byte of offset
        sty(at(apl_offset)+1)             # set high byte of offset to 0

        tya()                           # set A to 0
        sty(at(apl_gamma2_hi))            # set high byte of len to 0
        adc(imm(0x02))                      # add 2 or 3 depending on len bit in carry
                                                # now, low part of len is in A
                                                # high part of len in apl_gamma2_hi is 0
                                                # offset is written to apl_offset
        bne(rel_at("got_len"))                  # go copy matched bytes

        label("long_match")
        jsr(at("get_gamma2"))               # 10") read gamma2 high offset bits in A
        sty(at(apl_gamma2_hi))            # zero out high byte of gamma2

        cpx(imm(0x01))                      # set carry if following literal
        sbc(imm(0x02))                      # substract 3 if following literal, 2 otherwise
        bcs(rel_at("no_repmatch"))

        jsr(at("get_gamma2"))               # read repmatch length") low part in A
        bcc(rel_at("got_len"))                  # go copy large match
                                    # (carry is always clear after label("get_gamma2)

        label("short_match")
        lda(imm(0x10))                      # clear offset, load end bit into place
        label("read_short_offs")
        APL_GET_BIT_SAVEA            # read one bit of offset into carry
        rol(a)                           # shift into A, shift end bit as well
        bcc(rel_at("read_short_offs"))          # loop until end bit is shifted out into carry

        beq(rel_at("write_literal"))            # zero offset means write a 0
        tay()
        lda(ind_at(apl_dstptr),y)            # load backreferenced byte
        ldy(imm(0x00))                      # clear Y again
        beq(rel_at("write_literal"))            # go write byte to destination

        label("get_gamma2")
        lda(imm(0x01))                      # 1 so it gets shifted to 2
        label("gamma2_loop")
        APL_GET_BIT_SAVEA()            # read data bit
        rol(a)                           # shift into low byte
        rol(at(apl_gamma2_hi))            # shift into high byte
        APL_GET_BIT_SAVEA()            # read continuation bit
        bcs(rel_at("gamma2_loop"))              # loop until a zero continuation bit is read
        label("done")
        rts()

        label("no_repmatch")
        sta(at(apl_offset)+1)             # write high byte of offset
        APL_GET_SRC()                  # read low byte of offset from source
        sta(at(apl_offset)+0)             # store low byte of offset

        jsr(at("get_gamma2"))               # read match length") low part in A

        ldx(at(apl_offset)+1)             # high offset byte is zero?
        beq(rel_at("offset_1byte"))             # if so, offset(at(" 256

                                    # offset is >= 256label("

        cpx(imm(0x7d))                      # offset >= 32000 (7d00) ?
        bcs(rel_at("offset_incby2"))            # if so, increase match len by 2
        cpx(imm(0x05))                      # offset >= 1280 (0500) ?
        bcs(rel_at("offset_incby1"))            # if so, increase match len by 1
        bcc(rel_at("got_len"))                  # length is fine, go copy

        label("offset_1byte")
        ldx(at(apl_offset)+0)             # offset(at(" 128 ?
        bmi(rel_at("got_len"))                  # if so, increase match len by 2
        sec()                           # carry must be set below

        label("offset_incby2")
        adc(imm(0x01))                      # add 1 + set carry (from bcs or sec)
        bcs(rel_at("len_inchi"))                # go add 256 to len if overflow

                                                # carry clear") fall through for no-op

        label("offset_incby1")
        adc(imm(0x00))                      # add 1 + carry
        bcc(rel_at("got_len"))
        label("len_inchi")
        inc(at(apl_gamma2_hi))            # add 256 to len if low byte overflows

        label("got_len")
        tax()                           # transfer low byte of len into X
        beq(rel_at("add_offset"))
        inc(at(apl_gamma2_hi))

        label("add_offset")
        clc()                           # add dest + match offset
        lda(at(apl_dstptr)+0)             # low 8 bits
        adc(at(apl_offset)+0)
        sta(at(apl_winptr)+0)             # store back reference address
        lda(at(apl_dstptr)+1)             # high 8 bits
        adc(at(apl_offset)+1)
        sta(at(apl_winptr)+1)             # store high 8 bits of address

        label("copy_match_loop")
        lda(ind_at(apl_winptr),y)            # read one byte of backreference
        APL_PUT_DST()                  # write byte to destination

        lda(at(apl_winptr)+0)             # decrement backreference address
        bne(rel_at("backref_page_done"))
        dec(at(apl_winptr)+1)
        label("backref_page_done")
        dec(at(apl_winptr)+0)

        dex                           # loop to copy all matched bytes
        bne(rel_at("copy_match_loop"))
        dec(at(apl_gamma2_hi))
        bne(rel_at("copy_match_loop"))

                                    # X is 0 when exiting the loop above
        inx()                           # set 'follows match' flag
        jmp(at("next_token"))             # go decode next token

        label("apl_load_bits")
        lda(ind_at(apl_srcptr),y)            # read 8 bits from source
        rol(a)                           # shift bit queue, and high bit into carry
        sta(at(apl_bitbuf))               # save bit queue

        lda(at(apl_srcptr)+0)
        bne(rel_at("bits_page_done"))
        dec(at(apl_srcptr)+1)
        label("bits_page_done")
        dec(at(apl_srcptr)+0)
        rts()



