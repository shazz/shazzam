from enum import Enum

from shazzam.Cruncher import Cruncher
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a


class PackingMode(Enum):
    FORWARD = 0
    BACKWARD = 1


class Apultra(Cruncher):

    def __init__(self, exe_path: str, mode: PackingMode = PackingMode.FORWARD):

        self.mode = mode

        cmd_prg_template = None

        if mode is PackingMode.FORWARD:
            cmd_bin_template = [exe_path, "FILENAME_TO_SET", "OUTPUT_TO_SET"]
        else:
            cmd_bin_template = [exe_path, "-b", "FILENAME_TO_SET", "OUTPUT_TO_SET"]

        super().__init__("apultra", exe_path, cmd_prg_template, cmd_bin_template)

    def generate_depacker_routine(self, address: int) -> None:

        if self.mode is PackingMode.FORWARD:
            self._forward_depacker(address)
        else:
            self._backward_depacker(address)

    def _forward_depacker(self, address: int):

        # apl_decompress - Decompress data stored in Jorgen Ibsen's aPLib format.
        #
        # Args: apl_srcptr = ptr to compessed data
        # Args: apl_dstptr = ptr to output buffer
        # Uses: lots!
        #
        # As an optimization, the code to handle window offsets > 64768 bytes has
        # been removed, since these don't occur with a 16-bit address range.
        #
        # As an optimization, the code to handle window offsets > 32000 bytes can
        # be commented-out, since these don't occur in typical 8-bit computer usage.

        # Zero page locations, Data usage is last 12 bytes of zero-page.
        apl_bitbuf = 0xF7
        apl_offset = 0xF8
        apl_winptr = 0xFA
        apl_srcptr = 0xFC
        apl_dstptr = 0xFE
        apl_length = apl_winptr

        # Macro to increment the source pointer to the next page.
        def APL_INC_PAGE():
            inc(at(apl_srcptr)+1)

        # Macro to read a byte from the compressed source data.
        def APL_GET_SRC():
            skip = get_anonymous_label("skip")
            lda(ind_at(apl_srcptr), y)
            inc(at(apl_srcptr)+0)
            bne(rel_at(skip))
            APL_INC_PAGE()
            label(skip)
            # nop()

        label("apl_decompress", is_global=True)

        ldy(imm(0))
        lda(imm(0x80))
        sta(at(apl_bitbuf))

        label("apl_literal")
        APL_GET_SRC()

        label("apl_write_byte")
        ldx(imm(0))
        sta(ind_at(apl_dstptr), y)
        inc(at(apl_dstptr)+0)
        bne(rel_at("apl_next_tag"))
        inc(at(apl_dstptr)+1)

        label("apl_next_tag")
        asl(at(apl_bitbuf))
        bne(rel_at("apl_skip0"))
        jsr(at("apl_load_bit"))
        label("apl_skip0")
        bcc(rel_at("apl_literal"))

        label("apl_skip1")
        asl(at(apl_bitbuf))
        bne(rel_at("apl_skip2"))
        jsr(at("apl_load_bit"))

        label("apl_skip2")
        bcc(rel_at("apl_copy_large"))
        asl(at(apl_bitbuf))
        bne(rel_at("apl_skip3"))
        jsr(at("apl_load_bit"))

        label("apl_skip3")
        bcc(rel_at("apl_copy_normal"))

        label("apl_copy_short")
        lda(imm(0x10))

        label("apl_nibble_loop")
        asl(at(apl_bitbuf))
        bne(rel_at("apl_skip4"))
        pha()
        jsr(at("apl_load_bit"))
        pla()

        label("apl_skip4")
        rol(a)
        bcc(rel_at("apl_nibble_loop"))
        beq(rel_at("apl_write_byte"))
        eor(imm(0xFF))
        tay()
        iny()
        dec(at(apl_dstptr)+1)
        lda(ind_at(apl_dstptr), y)
        inc(at(apl_dstptr)+1)
        ldy(imm(0))
        beq(rel_at("apl_write_byte"))

        label("apl_copy_normal")
        APL_GET_SRC()
        lsr(a)
        beq(rel_at("apl_finished"))
        sta(at(apl_offset)+0)
        sty(at(apl_offset)+1)
        tya()
        tax()
        adc(imm(2))
        bne(rel_at("apl_do_match"))
        label("apl_get_gamma")
        lda(imm(1))

        label("apl_gamma_loop")
        asl(at(apl_bitbuf))
        bne(rel_at("apl_skip5"))
        pha()
        jsr(at("apl_load_bit"))
        pla()

        label("apl_skip5")
        rol(a)
        rol(at(apl_length)+1)
        asl(at(apl_bitbuf))
        bne(rel_at("apl_skip6"))
        pha()
        jsr(at("apl_load_bit"))
        pla()
        label("apl_skip6")
        bcs(rel_at("apl_gamma_loop"))

        label("apl_finished")
        rts()

        label("apl_copy_large")
        jsr(at("apl_get_gamma"))
        sty(at(apl_length)+1)
        cpx(imm(1))
        sbc(imm(2))
        bcs(rel_at("apl_normal_pair"))
        jsr(at("apl_get_gamma"))
        ldx(at(apl_length)+1)
        bcc(rel_at("apl_do_match"))

        label("apl_normal_pair")
        sta(at(apl_offset)+1)
        APL_GET_SRC()
        sta(at(apl_offset)+0)
        jsr(at("apl_get_gamma"))
        ldx(at(apl_length)+1)
        ldy(at(apl_offset)+1)
        beq(rel_at("apl_lt256"))
        cpy(imm(0x7D))
        bcs(rel_at("apl_match_plus2"))
        cpy(imm(0x05))
        bcs(rel_at("apl_match_plus1"))
        bcc(rel_at("apl_do_match"))
        label("apl_lt256")
        ldy(at(apl_offset)+0)
        bmi(rel_at("apl_do_match"))
        sec()

        label("apl_match_plus2")
        adc(imm(1))
        bcs(rel_at("apl_match_plus256"))
        label("apl_match_plus1")
        adc(imm(0))
        bcc(rel_at("apl_do_match"))
        label("apl_match_plus256")
        inx()

        label("apl_do_match")
        eor(imm(0xFF))
        tay()
        iny()
        beq(rel_at("apl_calc_addr"))
        eor(imm(0xFF))
        inx()
        clc()
        adc(at(apl_dstptr)+0)
        sta(at(apl_dstptr)+0)
        bcs(rel_at("apl_calc_addr"))
        dec(at(apl_dstptr)+1)

        label("apl_calc_addr")
        sec()
        lda(at(apl_dstptr)+0)
        sbc(at(apl_offset)+0)
        sta(at(apl_winptr)+0)
        lda(at(apl_dstptr)+1)
        sbc(at(apl_offset)+1)
        sta(at(apl_winptr)+1)

        label("apl_copy_page")
        lda(ind_at(apl_winptr), y)
        sta(ind_at(apl_dstptr), y)
        iny()
        bne(rel_at("apl_copy_page"))
        inc(at(apl_winptr)+1)
        inc(at(apl_dstptr)+1)
        dex()
        bne(rel_at("apl_copy_page"))
        inx()
        jmp(at("apl_next_tag"))

        label("apl_load_bit")
        APL_GET_SRC()
        rol(a)
        sta(at(apl_bitbuf))

        rts()

    def _backward_depacker(self, address: int) -> None:

        # Zero page locations
        apl_gamma2_hi = 0xF6
        apl_bitbuf = 0xF7
        apl_offset = 0xF8
        apl_winptr = 0xFA
        apl_srcptr = 0xFC
        apl_dstptr = 0xFE

        # Read a byte from the source into A. Trashes X
        def APL_GET_SRC():
            src_page_done = get_anonymous_label("src_page_done")
            lda(ind_at(apl_srcptr), y)
            ldx(at(apl_srcptr)+0)
            bne(rel_at(src_page_done))
            dec(at(apl_srcptr)+1)
            label(src_page_done)
            dec(at(apl_srcptr+0))

        # Write a byte to the destinatipn
        def APL_PUT_DST():
            dst_page_done = get_anonymous_label("dst_page_done")
            sta(ind_at(apl_dstptr), y)
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
            jsr(at("apl_apl_load_bits"))
            label(has_bits)

        # Read one bit from the source into the carry, preserve A
        def APL_GET_BIT_SAVEA():
            has_bits = get_anonymous_label("has_bits")
            asl(at(apl_bitbuf))
            bne(rel_at(has_bits))
            pha()
            jsr(at("apl_apl_load_bits"))
            pla()
            label(has_bits)

        # Decompress aPLib data backwards
        label("apl_decompress", is_global=True)
        lda(imm(0x80))                      # initialize empty bit queue
        sta(at(apl_bitbuf))               # plus bit to roll into carry
        ldy(imm(0x00))                      # clear Y for indirect addr

        label("apl_copy_literal")
        APL_GET_SRC()                  # read literal from source
        label("apl_write_literal")
        APL_PUT_DST()                  # write literal to destination

        ldx(imm(0x00))                      # clear 'follows match' flag

        label("apl_next_token")
        APL_GET_BIT()                  # read 'literal or match' bit
        bcc(rel_at("apl_copy_literal"))             # if 0") literal

        APL_GET_BIT()                  # read '8+n bits or other' bit
        # if 10x") long 8+n bits match
        bcc(rel_at("apl_long_match"))

        # 11x") other type of match

        APL_GET_BIT()                  # read '7)+1) match or short literal' bit
        # if 111") 4 bit offset for 1-byte copy
        bcs(rel_at("apl_short_match"))

        APL_GET_SRC()                  # read low byte of offset + length bit
        # shift offset into place, len bit into carry
        lsr(a)
        beq(rel_at("apl_done"))                     # check for EOD
        sta(at(apl_offset)+0)             # store low byte of offset
        sty(at(apl_offset)+1)             # set high byte of offset to 0

        tya()                           # set A to 0
        sty(at(apl_gamma2_hi))            # set high byte of len to 0
        # add 2 or 3 depending on len bit in carry
        adc(imm(0x02))
        # now, low part of len is in A
        # high part of len in apl_gamma2_hi is 0
        # offset is written to apl_offset
        bne(rel_at("apl_got_len"))                  # go copy matched bytes

        label("apl_long_match")
        # 10") read gamma2 high offset bits in A
        jsr(at("apl_get_gamma2"))
        sty(at(apl_gamma2_hi))            # zero out high byte of gamma2

        cpx(imm(0x01))                      # set carry if following literal
        # substract 3 if following literal, 2 otherwise
        sbc(imm(0x02))
        bcs(rel_at("apl_no_repmatch"))

        # read repmatch length") low part in A
        jsr(at("apl_get_gamma2"))
        bcc(rel_at("apl_got_len"))                  # go copy large match
        # (carry is always clear after label("apl_get_gamma2)

        label("apl_short_match")
        # clear offset, load end bit into place
        lda(imm(0x10))
        label("apl_read_short_offs")
        APL_GET_BIT_SAVEA            # read one bit of offset into carry
        rol(a)                           # shift into A, shift end bit as well
        # loop until end bit is shifted out into carry
        bcc(rel_at("apl_read_short_offs"))

        # zero offset means write a 0
        beq(rel_at("apl_write_literal"))
        tay()
        lda(ind_at(apl_dstptr), y)            # load backreferenced byte
        ldy(imm(0x00))                      # clear Y again
        # go write byte to destination
        beq(rel_at("apl_write_literal"))

        label("apl_get_gamma2")
        lda(imm(0x01))                      # 1 so it gets shifted to 2
        label("apl_gamma2_loop")
        APL_GET_BIT_SAVEA()            # read data bit
        rol(a)                           # shift into low byte
        rol(at(apl_gamma2_hi))            # shift into high byte
        APL_GET_BIT_SAVEA()            # read continuation bit
        # loop until a zero continuation bit is read
        bcs(rel_at("apl_gamma2_loop"))
        label("apl_done")
        rts()

        label("apl_no_repmatch")
        sta(at(apl_offset)+1)             # write high byte of offset
        APL_GET_SRC()                  # read low byte of offset from source
        sta(at(apl_offset)+0)             # store low byte of offset

        # read match length") low part in A
        jsr(at("apl_get_gamma2"))

        ldx(at(apl_offset)+1)             # high offset byte is zero?
        # if so, offset(at("apl_ 256
        beq(rel_at("apl_offset_1byte"))

        # offset is >= 256label("apl_

        cpx(imm(0x7d))                      # offset >= 32000 (7d00) ?
        # if so, increase match len by 2
        bcs(rel_at("apl_offset_incby2"))
        cpx(imm(0x05))                      # offset >= 1280 (0500) ?
        # if so, increase match len by 1
        bcs(rel_at("apl_offset_incby1"))
        bcc(rel_at("apl_got_len"))                  # length is fine, go copy

        label("apl_offset_1byte")
        ldx(at(apl_offset)+0)             # offset(at("apl_ 128 ?
        # if so, increase match len by 2
        bmi(rel_at("apl_got_len"))
        sec()                           # carry must be set below

        label("apl_offset_incby2")
        # add 1 + set carry (from bcs or sec)
        adc(imm(0x01))
        # go add 256 to len if overflow
        bcs(rel_at("apl_len_inchi"))

        # carry clear") fall through for no-op

        label("apl_offset_incby1")
        adc(imm(0x00))                      # add 1 + carry
        bcc(rel_at("apl_got_len"))
        label("apl_len_inchi")
        # add 256 to len if low byte overflows
        inc(at(apl_gamma2_hi))

        label("apl_got_len")
        tax()                           # transfer low byte of len into X
        beq(rel_at("apl_add_offset"))
        inc(at(apl_gamma2_hi))

        label("apl_add_offset")
        clc()                           # add dest + match offset
        lda(at(apl_dstptr)+0)             # low 8 bits
        adc(at(apl_offset)+0)
        sta(at(apl_winptr)+0)             # store back reference address
        lda(at(apl_dstptr)+1)             # high 8 bits
        adc(at(apl_offset)+1)
        sta(at(apl_winptr)+1)             # store high 8 bits of address

        label("apl_copy_match_loop")
        lda(ind_at(apl_winptr), y)            # read one byte of backreference
        APL_PUT_DST()                  # write byte to destination

        lda(at(apl_winptr)+0)             # decrement backreference address
        bne(rel_at("apl_backref_page_done"))
        dec(at(apl_winptr)+1)
        label("apl_backref_page_done")
        dec(at(apl_winptr)+0)

        dex                           # loop to copy all matched bytes
        bne(rel_at("apl_copy_match_loop"))
        dec(at(apl_gamma2_hi))
        bne(rel_at("apl_copy_match_loop"))

        # X is 0 when exiting the loop above
        inx()                           # set 'follows match' flag
        jmp(at("apl_next_token"))             # go decode next token

        label("apl_apl_load_bits")
        lda(ind_at(apl_srcptr), y)            # read 8 bits from source
        rol(a)                           # shift bit queue, and high bit into carry
        sta(at(apl_bitbuf))               # save bit queue

        lda(at(apl_srcptr)+0)
        bne(rel_at("apl_bits_page_done"))
        dec(at(apl_srcptr)+1)
        label("apl_bits_page_done")
        dec(at(apl_srcptr)+0)
        rts()
