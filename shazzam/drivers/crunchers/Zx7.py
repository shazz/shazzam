from shazzam.Cruncher import Cruncher
from shazzam.py64gen import RegisterACC as a
from shazzam.py64gen import RegisterX as x
from shazzam.py64gen import RegisterY as y
from shazzam.py64gen import *

import os
import pyzx7
import logging


class Zx7(Cruncher):

    def __init__(self, exe_path: str = None):
        self.logger = logging.getLogger("shazzam")
        self.packer_name = "Zx7"

        cmd_prg_template = None
        cmd_bin_template = [exe_path, "FILENAME_TO_SET", "OUTPUT_TO_SET"]
        super().__init__("Zx7", exe_path, cmd_prg_template, cmd_bin_template)

    def crunch_incbin(self, filename: str = None, data: bytearray = None, extra_params: List = None) -> bytearray:
        """crunch_incbin

        Args:
            filename (str): [description]
            extra_params (List, optional): [description]. Defaults to None.

        Raises:
            RuntimeError: [description]
        """
        try:

            if filename is None:
                filename = "resources/tmp.bin"
                with open(filename, "wb") as f:
                    f.write(data)

            output_filename = f"{filename}.zx7"
            if os.path.isfile(output_filename):
                 os.remove(output_filename)

            self.logger.info(f"Crunching {filename} with {self.packer_name}")
            new_filename = pyzx7.compress(filename)

            # check packing ratio
            unpacked_size = os.path.getsize(filename)
            packed_size = os.path.getsize(output_filename)
            if packed_size >= unpacked_size:
                raise RuntimeError(f"Packing doesn't shrink the incbin. Size increased from {unpacked_size} to {packed_size} bytes")

            self.logger.info(f"{filename} was {unpacked_size} bytes, packed to {packed_size} bytes")
            with open(output_filename, "rb") as f:
                barr = f.read()

            return bytearray(barr)

        except Exception as e:
            self.logger.error(f"Cannot crunch incbin using {self.packer_name} due to {e}")
            raise

    def generate_depacker_routine(self, address: int) -> None:

        #*****************************************************************
        # ZX7 decompressor based on
        # ZX7 data decompressor for Apple II
        # by Peter Ferrie (peter.ferrie@gmail.com)
        # with modifications by Juan J. Martinez (@reidrac)
        # optimized by Petri Häkkinen
        # This code is in the Public Domain
        #*****************************************************************

        zx7_src_lo	= 0x20	# should always contain 0
        zx7_src_hi	= 0x21	# write source page address here

        # internal
        zx7_dst_lo	= 0x22
        zx7_dst_hi	= 0x23
        zx7_ecx_lo	= 0x24
        zx7_ecx_hi	= 0x25
        zx7_last	= 0x26
        temp1       = 0x27
        temp2       = 0x28
        temp3       = 0x29

        # in:
        # A = dest address lo
        # X = dest address hi
        # Y = src address lo
        label("zx7_unpack", is_global=True)
        sta(at(zx7_dst_lo))		# sta(at(& stx(at(can be skipped if the address is set by caller
        stx(at(zx7_dst_hi))
        # y = src offset
        lda(imm(0))
        sta(at(zx7_last))
        sta(at(zx7_ecx_lo))
        sta(at(zx7_ecx_hi))

        label("copy_byte_loop")
        jsr(at("getput"))
        label("main_loop")
        jsr(at("next_bit"))
        bcc(rel_at("copy_byte_loop"))
        ldx(imm(0))			# x = counter

        label("len_size_loop")
        inx()
        jsr(at("next_bit"))
        bcc(rel_at("len_size_loop"))
        bcs(rel_at("len_value_skip"))	# always branch

        label("len_value_loop")
        jsr(at("next_bit"))

        label("len_value_skip")
        rol(at(zx7_ecx_lo))
        rol(at(zx7_ecx_hi))
        bcs(rel_at("next_bit_ret"))
        dex()
        bne(rel_at("len_value_loop"))
        inc(at(zx7_ecx_lo))
        bne(rel_at("skip1"))
        inc(at(zx7_ecx_hi))

        label("skip1")
        jsr(at("getsrc"))
        rol(a)
        sta(at(temp1))
        txa()
        bcc(rel_at("offset_end"))
        lda(imm(0x10))

        label("rld_next_bit")
        pha()
        jsr(at("next_bit"))
        pla()
        rol(a)
        bcc(rel_at("rld_next_bit"))
        #clc
        #adc #1
        adc(imm(0))			# carry is always set
        lsr(a)

        label("offset_end")
        sta(at(temp2))
        ror(at(temp1))
        ldx(at(zx7_src_hi))		# store src hi
        tya()			# store Y
        pha()
        # compute new offset y
        lda(at(zx7_dst_lo))
        sbc(at(temp1))
        tay()			# y = dst_lo - offset
        # src_hi = dst_hi - temp2
        lda(at(zx7_dst_hi))
        sbc(at(temp2))
        sta(at(zx7_src_hi))

        label("loop1")
        jsr(at("getput"))
        # dec ecx
        lda(at(zx7_ecx_lo))
        bne(rel_at("skip2"))
        dec(at(zx7_ecx_hi))

        label("skip2")	#sec			# carry seems to be always set, but why?
        sbc(imm(1))
        sta(at(zx7_ecx_lo))
        ora(at(zx7_ecx_hi))
        bne(rel_at("loop1"))
        # restore src
        pla()			# restore Y
        tay()
        stx(at(zx7_src_hi))		# restore src hi
        #jmp @main_loop
        bcs(rel_at("main_loop"))		# carry seems to be always set, but why?

        label("getput")
        jsr(at("getsrc"))
        sty(at(temp2))		    # store Y
        ldy(imm(0))
        sta(ind_at(0x22), y)
        ldy(at(temp2))		    # restore Y
        inc(at(zx7_dst_lo))
        bne(rel_at("skip3"))
        inc(at(zx7_dst_hi))
        label("skip3")
        rts()

        # read one byte from source
        label("getsrc")
        lda(ind_at(0x20), y)
        iny()
        bne(rel_at("skip4"))
        inc(at(zx7_src_hi))
        label("skip4")
        rts()

        label("next_bit")
        asl(at(zx7_last))
        bne(rel_at("next_bit_ret"))
        jsr(at("getsrc"))
        sec()
        rol(a)
        sta(at(zx7_last))

        label("next_bit_ret")
        rts()

    def generate_depacker_fast_routine(self, address: int) -> None:

        apd_bitbuffer   = 0xf5
        apd_src         = 0xf6
        apd_length      = 0xf8
        apd_offset      = 0xfa
        apd_source      = 0xfc
        apd_dest        = 0xfe

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
