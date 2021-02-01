from shazzam.Cruncher import Cruncher
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a


class Lzsa(Cruncher):

    def __init__(self, exe_path: str):

        cmd_prg_template = None
        cmd_bin_template = [exe_path, "FILENAME_TO_SET", "OUTPUT_TO_SET"]
        super().__init__("lzsa", exe_path, cmd_prg_template, cmd_bin_template)

    def generate_depacker_routine(self, address: int, use_fast: bool = True) -> None:
        """[summary]

        Args:
            address (int): [description]
            use_fast (bool, optional): [description]. Defaults to True.
        """
         # -----------------------------------------------------------------------------
        # Decompress raw LZSA2 block.
        # Create one with lzsa -r -f2 <original_file> <compressed_file>
        #
        # in:
        # * LZSA_SRC_LO and LZSA_SRC_HI contain the compressed raw block address
        # * LZSA_DST_LO and LZSA_DST_HI contain the destination buffer address
        #
        # out:
        # * LZSA_DST_LO and LZSA_DST_HI contain the last decompressed byte address, +1
        #
        # -----------------------------------------------------------------------------
        # Backward decompression is also supported, use lzsa -r -b -f2 <original_file> <compressed_file>
        # To use it, also define BACKWARD_DECOMPRESS=1 before including this code!
        #
        # in:
        # * LZSA_SRC_LO/LZSA_SRC_HI must contain the address of the last byte of compressed data
        # * LZSA_DST_LO/LZSA_DST_HI must contain the address of the last byte of the destination buffer
        #
        # out:
        # * LZSA_DST_LO/LZSA_DST_HI contain the last decompressed byte address, -1
        #
        # -----------------------------------------------------------------------------
        #
        #  Copyright (C) 2019 Emmanuel Marty, Peter Ferrie
        #
        #  This software is provided 'as-is', without any express or implied
        #  warranty.  In no event will the authors be held liable for any damages
        #  arising from the use of this software.
        #
        #  Permission is granted to anyone to use this software for any purpose,
        #  including commercial applications, and to alter it and redistribute it
        #  freely, subject to the following restrictions:
        #
        #  1. The origin of this software must not be misrepresented# you must not
        #     claim that you wrote the original software. If you use this software
        #     in a product, an acknowledgment in the product documentation would be
        #     appreciated but is not required.
        #  2. Altered source versions must be pla()inly marked as such, and must not be
        #     misrepresented as being the original software.
        #  3. This notice may not be removed or altered from any source distribution.
        # -----------------------------------------------------------------------------

        NIBCOUNT    = 0xFC                          # zero-page location for temp offset

        label("DECOMPRESS_LZSA2_FAST")
        LDY(imm(0x00))
        sty(at(NIBCOUNT))

        label("DECODE_TOKEN")
        jsr(at("GETSRC"))                           # read token byte: XYZ|LL|MMM
        pha()                                  # preserve token on stack

        AND(imm(0x18))                             # isolate literals count (LL)
        beq(rel_at("NO_LITERALS"))                      # skip if no literals to copy
        CMP(imm(0x18))                             # LITERALS_RUN_LEN_V2?
        bcc(rel_at("PREPARE_COPY_LITERALS"))            # if less, count is directly embedded in token

        jsr(at("GETNIBBLE"))                        # get extra literals length nibble
                                            # add nibble to len from token
        adc(imm(0x02))                             # (LITERALS_RUN_LEN_V2) minus carry
        CMP(imm(0x12))                             # LITERALS_RUN_LEN_V2 + 15 ?
        bcc(rel_at("PREPARE_COPY_LITERALS_DIRECT"))     # if less, literals count is complete

        jsr(at("GETSRC"))                           # get extra byte of variable literals count
                                            # the carry is always set by the CMP above
                                            # GETSRC doesn't change it
        SBC(imm(0xEE))                             # overflow?
        jmp(at("PREPARE_COPY_LITERALS_DIRECT"))

        label("PREPARE_COPY_LITERALS_LARGE")
                                            # handle 16 bits literals count
                                            # literals count = directly these 16 bits
        jsr(at("GETLARGESRC"))                      # grab low 8 bits in X, high 8 bits in A
        tay()                                  # put high 8 bits in Y
        bcs(rel_at("PREPARE_COPY_LITERALS_HIGH"))       # (*same as jmp(at("PREPARE_COPY_LITERALS_HIGH but shorter)

        label("PREPARE_COPY_LITERALS")
        lsr(a)                                  # shift literals count into pla()ce
        lsr(a)
        lsr(a)

        label("PREPARE_COPY_LITERALS_DIRECT")
        tax()
        bcs(rel_at("PREPARE_COPY_LITERALS_LARGE"))      # if so, literals count is large

        label("PREPARE_COPY_LITERALS_HIGH")
        txa()
        beq(rel_at("COPY_LITERALS"))
        iny()

        label("COPY_LITERALS")
        jsr(at("GETPUT"))                           # copy one byte of literals
        dex()
        bne(rel_at("COPY_LITERALS"))
        dey()
        bne(rel_at("COPY_LITERALS"))

        label("NO_LITERALS")
        pla()                                  # retrieve token from stack
        pha()                                  # preserve token again
        asl(a)
        bcs(rel_at("REPMATCH_OR_LARGE_OFFSET"))         # 1YZ: rep-match or 13/16 bit offset

        asl(a)                                  # 0YZ: 5 or 9 bit offset
        bcs(rel_at("OFFSET_9_BIT"))

                                            # 00Z: 5 bit offset

        LDX(imm(0xFF))                             # set offset bits 15-8 to 1

        jsr(at("GETCOMBINEDBITS"))                  # rotate Z bit into bit 0, read nibble for bits 4-1
        ora(imm(0xE0))                             # set bits 7-5 to 1
        bne(rel_at("GOT_OFFSET_LO"))                    # go store low byte of match offset and prepare match

        label("OFFSET_9_BIT")                            # 01Z: 9 bit offset
        rol(a)                                  # carry: Z bit# A: xxxxxxx1 (carry known set from bcs(rel_at("OFFSET_9_BIT)
        adc(imm(0x00))                             # if Z bit is set, add 1 to A (bit 0 of A is now 0), otherwise bit 0 is 1
        ora(imm(0xFE))                             # set offset bits 15-9 to 1. reversed Z is already in bit 0
        bne(rel_at("GOT_OFFSET_HI"))                    # go store high byte, read low byte of match offset and prepare match
                                            # (*same as jmp(at("GOT_OFFSET_HI but shorter)

        label("REPMATCH_OR_LARGE_OFFSET")
        asl(a)                                # 13 bit offset?
        bcs(rel_at("REPMATCH_OR_16_BIT"))               # handle rep-match or 16-bit offset if not

                                            # 10Z: 13 bit offset

        jsr(at("GETCOMBINEDBITS"))                  # rotate Z bit into bit 8, read nibble for bits 12-9
        adc(imm(0xDE))                             # set bits 15-13 to 1 and substract 2 (to substract 512)
        bne(rel_at("GOT_OFFSET_HI"))                    # go store high byte, read low byte of match offset and prepare match
                                            # (*same as jmp(at("GOT_OFFSET_HI but shorter)

        label("REPMATCH_OR_16_BIT")                      # rep-match or 16 bit offset
        bmi(rel_at("REP_MATCH"))                        # reuse previous offset if so (rep-match)

                                            # 110: handle 16 bit offset
        jsr(at("GETSRC"))                           # grab high 8 bits
        label("GOT_OFFSET_HI")
        tax()
        jsr(at("GETSRC"))                           # grab low 8 bits
        label("GOT_OFFSET_LO")
        sta(at(OFFSLO))                           # store low byte of match offset
        stx(at(OFFSHI))                           # store high byte of match offset

        label("REP_MATCH")

        if BACKWARD_DECOMPRESS:

            # Backward decompression - substract match offset

            sec()                                  # add dest + match offset
            lda(at(PUTDST)+1)                         # low 8 bits
            OFFSLO = get_current_address() + 1
            SBC(imm(0xAA))
            sta(at(COPY_MATCH_LOOP)+1)                # store back reference address
            lda(at(PUTDST)+2)
            OFFSHI = get_current_address()+1
            SBC(imm(0xAA))                             # high 8 bits
            sta(at(COPY_MATCH_LOOP)+2)                # store high 8 bits of address
            sec()

        else:

            # Forward decompression - add match offset

            clc()                                  # add dest + match offset
            lda(at(PUTDST)+1)                         # low 8 bits
            OFFSLO = get_current_address()+1
            adc(imm(0xAA))
            sta(at(COPY_MATCH_LOOP)+1)                # store back reference address
            OFFSHI = get_current_address()+1
            LDA(imm(0xAA))                             # high 8 bits
            adc(at(PUTDST)+2)
            sta(at(COPY_MATCH_LOOP)+2)                # store high 8 bits of address

        pla()                                  # retrieve token from stack again
        AND(imm(0x07))                             # isolate match len (MMM)
        adc(imm(0x01))                             # add MIN_MATCH_SIZE_V2 and carry
        CMP(imm(0x09))                             # MIN_MATCH_SIZE_V2 + MATCH_RUN_LEN_V2?
        bcc(rel_at("PREPARE_COPY_MATCH"))               # if less, length is directly embedded in token

        jsr(at("GETNIBBLE"))                        # get extra match length nibble
                                            # add nibble to len from token
        adc(imm(0x08))                             # (MIN_MATCH_SIZE_V2 + MATCH_RUN_LEN_V2) minus carry
        CMP(imm(0x18))                             # MIN_MATCH_SIZE_V2 + MATCH_RUN_LEN_V2 + 15?
        bcc(rel_at("PREPARE_COPY_MATCH"))               # if less, match length is complete

        jsr(at("GETSRC"))                           # get extra byte of variable match length
                                            # the carry is always set by the CMP above
                                            # GETSRC doesn't change it
        SBC(imm(0xE8))                             # overflow?

        label("PREPARE_COPY_MATCH")
        tax()
        bcc(rel_at("PREPARE_COPY_MATCH_Y"))             # if not, the match length is complete
        beq(rel_at("DECOMPRESSION_DONE"))               # if EOD code, bail

                                            # Handle 16 bits match length
        jsr(at("GETLARGESRC"))                      # grab low 8 bits in X, high 8 bits in A
        tay()                                  # put high 8 bits in Y

        label("PREPARE_COPY_MATCH_Y")
        txa()
        beq(rel_at("COPY_MATCH_LOOP"))
        iny()

        label("COPY_MATCH_LOOP")
        lda(at(0xAAAA))                            # get one byte of backreference
        jsr(at("PUTDST"))                           # copy to destination

        if BACKWARD_DECOMPRESS:

            # Backward decompression -- put backreference bytes backward

            lda(at(COPY_MATCH_LOOP)+1)
            beq(rel_at("GETMATCH_ADJ_HI"))
            label("GETMATCH_DONE")
            dec(at(COPY_MATCH_LOOP)+1)

        else:

            # Forward decompression -- put backreference bytes forward

            inc(at(COPY_MATCH_LOOP)+1)
            beq(rel_at("GETMATCH_ADJ_HI"))
            label("GETMATCH_DONE")

        dex()
        bne(rel_at("COPY_MATCH_LOOP"))
        dey()
        bne(rel_at("COPY_MATCH_LOOP"))
        jmp(at("DECODE_TOKEN"))

        if BACKWARD_DECOMPRESS:

            label("GETMATCH_ADJ_HI")
            dec(at(COPY_MATCH_LOOP)+2)
            jmp(at("GETMATCH_DONE"))

        else:

            label("GETMATCH_ADJ_HI")
            inc(at(COPY_MATCH_LOOP)+2)
            jmp(at("GETMATCH_DONE"))

        label("GETCOMBINEDBITS")
        eor(imm(0x80))
        asl(a)
        php()

        jsr(at("GETNIBBLE"))                        # get nibble into bits 0-3 (for offset bits 1-4)
        plp()                                  # merge Z bit as the carry bit (for offset bit 0)
        rol(a)                                  # nibble -> bits 1-4# carry(!Z bit) -> bit 0 # carry cleared
        label("DECOMPRESSION_DONE")
        rts()

        label("GETNIBBLE")
        NIBBLES = get_current_address()+1
        lda(imm(0xAA))
        lsr(at(NIBCOUNT))
        bcc(rel_at("NEED_NIBBLES"))
        andr(imm(0x0F))                             # isolate low 4 bits of nibble
        rts()

        label("NEED_NIBBLES")
        inc(at(NIBCOUNT))
        jsr(at("GETSRC"))                           # get 2 nibbles
        sta(at(NIBBLES))
        lsr(a)
        lsr(a)
        lsr(a)
        lsr(a)
        sec()
        rts()

        if BACKWARD_DECOMPRESS:

            # Backward decompression -- get and put bytes backward
            label("GETPUT")
            jsr(at("GETSRC"))
            label("PUTDST")
            LZSA_DST_LO = get_current_address()+1
            LZSA_DST_HI = get_current_address()+2
            sta(at(0xAAAA))
            lda(at(PUTDST)+1)
            beq(rel_at("PUTDST_ADJ_HI"))
            dec(at(PUTDST)+1)
            rts()

            label("PUTDST_ADJ_HI")
            dec(at(PUTDST)+2)
            dec(at(PUTDST)+1)
            rts()

            label("GETLARGESRC")
            jsr(at("GETSRC"))                           # grab low 8 bits
            tax()                                  # move to X
                                                    # fall through grab high 8 bits

            label("GETSRC")
            LZSA_SRC_LO = get_current_address()+1
            LZSA_SRC_HI = get_current_address()+2
            lda(at(0xAAAA))
            pha()
            lda(at(GETSRC)+1)
            beq(rel_at("GETSRC_ADJ_HI"))
            dec(at(GETSRC)+1)
            pla()
            rts()

            label("GETSRC_ADJ_HI")
            dec(at(GETSRC)+2)
            dec(at(GETSRC)+1)
            pla()
            rts()

        else:

            # Forward decompression -- get and put bytes forward

            label("GETPUT")
            jsr(at("GETSRC"))
            label("PUTDST")
            LZSA_DST_LO = get_current_address()+1
            LZSA_DST_HI = get_current_address()+2
            sta(at(0xAAAA))
            inc(at(PUTDST)+1)
            beq(rel_at("PUTDST_ADJ_HI"))
            rts()

            label("PUTDST_ADJ_HI")
            inc(at(PUTDST)+2)
            rts()

            label("GETLARGESRC")
            jsr(at("GETSRC"))                           # grab low 8 bits
            tax()                                  # move to X
                                                    # fall through grab high 8 bits

            label("GETSRC")
            LZSA_SRC_LO = get_current_address()+1
            LZSA_SRC_HI = get_current_address()+2
            lda(at(0xAAAA))
            inc(at(GETSRC)+1)
            beq(rel_at("GETSRC_ADJ_HI"))
            rts()

            label("GETSRC_ADJ_HI")
            inc(at(GETSRC)+2)
            rts



