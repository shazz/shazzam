from shazzam.Cruncher import Cruncher
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a


class Lzsa(Cruncher):

    def __init__(self, exe_path: str):

        cmd_prg_template = None
        cmd_bin_template = [exe_path, "-r", "-f2", "FILENAME_TO_SET", "OUTPUT_TO_SET"]
        super().__init__("lzsa", exe_path, cmd_prg_template, cmd_bin_template)

    def generate_depacker_routine(self, address: int, use_fast: bool = True) -> None:
        """[summary]

        Args:
            address (int): [description]
            use_fast (bool, optional): [description]. Defaults to True.
        """
        # -----------------------------------------------------------------------------
        # Decompress raw LZSA2 block, forward only.
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
        #
        #  Copyright (C) 2019 Emmanuel Marty, Peter Ferrie
        #
        #  This software is provided "as-is", without any express or implied
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
        #  2. Altered source versions must be plainly marked as such, and must not be
        #     misrepresented as being the original software.
        #  3. This notice may not be removed or altered from any source distribution.
        # -----------------------------------------------------------------------------

        NIBCOUNT = 0xfc                          # zero-page location for temp offset

        label("DECOMPRESS_LZSA2_FAST", is_global=True)
        if use_fast:
            self.logger.info("Using Fast lzsa depacker")

            ldy(imm(0x00))
            sty(at(NIBCOUNT))

            # --------------------------------------------- #
            label("DECODE_TOKEN")
            jsr(at("GETSRC"))                               # read token byte: XYZ|LL|MMM
            pha()                                           # preserve token on stack

            andr(imm(0x18))                                 # isolate literals count (LL)
            beq(rel_at("NO_LITERALS"))                      # skip if no literals to copy
            cmp(imm(0x18))                                  # LITERALS_RUN_LEN_V2?
            bcc(rel_at("PREPARE_COPY_LITERALS"))            # if less, count is directly embedded in token

            jsr(at("GETNIBBLE"))                            # get extra literals length nibble
                                                            # add nibble to len from token
            adc(imm(0x02))                                  # (LITERALS_RUN_LEN_V2) minus carry
            cmp(imm(0x12))                                  # LITERALS_RUN_LEN_V2 + 15 ?
            bcc(rel_at("PREPARE_COPY_LITERALS_DIRECT"))     # if less, literals count is complete

            jsr(at("GETSRC"))                               # get extra byte of variable literals count
                                                            # the carry is always set by the cmp above
                                                            # GETSRC doesn"t change it
            sbc(imm(0xEE))                                  # overflow?
            jmp(at("PREPARE_COPY_LITERALS_DIRECT"))

            # --------------------------------------------- #
            label("PREPARE_COPY_LITERALS_LARGE")
                                                            # handle 16 bits literals count
                                                            # literals count = directly these 16 bits
            jsr(at("GETLARGESRC"))                          # grab low 8 bits in X, high 8 bits in A
            tay()                                           # put high 8 bits in Y
            bcs(rel_at("PREPARE_COPY_LITERALS_HIGH"))       # (*same as JMP PREPARE_COPY_LITERALS_HIGH but shorter)

            # --------------------------------------------- #
            label("PREPARE_COPY_LITERALS")
            lsr(a)                                          # shift literals count into place
            lsr(a)
            lsr(a)

            # --------------------------------------------- #
            label("PREPARE_COPY_LITERALS_DIRECT")
            tax()
            bcs(rel_at("PREPARE_COPY_LITERALS_LARGE"))      # if so, literals count is large

            # --------------------------------------------- #
            label("PREPARE_COPY_LITERALS_HIGH")
            txa()
            beq(rel_at("COPY_LITERALS"))
            iny()

            # --------------------------------------------- #
            label("COPY_LITERALS")
            jsr(at("GETPUT"))                               # copy one byte of literals
            dex()
            bne(rel_at("COPY_LITERALS"))
            dey()
            bne(rel_at("COPY_LITERALS"))

            # --------------------------------------------- #
            label("NO_LITERALS")
            pla()                                           # retrieve token from stack
            pha()                                           # preserve token again
            asl(a)
            bcs(rel_at("REPMATCH_OR_LARGE_OFFSET"))         # 1YZ: rep-match or 13/16 bit offset

            asl(a)                                          # 0YZ: 5 or 9 bit offset
            bcs(rel_at("OFFSET_9_BIT"))

                                                            # 00Z: 5 bit offset

            ldx(imm(0xFF))                                  # set offset bits 15-8 to 1

            jsr(at("GETCOMBINEDBITS"))                      # rotate Z bit into bit 0, read nibble for bits 4-1
            ora(imm(0xE0))                                  # set bits 7-5 to 1
            bne(rel_at("GOT_OFFSET_LO"))                    # go store low byte of match offset and prepare match

            # --------------------------------------------- #
            label("OFFSET_9_BIT")                           # 01Z: 9 bit offset
            rol(a)                                          # carry: Z bit# A: xxxxxxx1 (carry known set from bcs(rel_at("OFFSET_9_BIT)
            adc(imm(0x00))                                  # if Z bit is set, add 1 to A (bit 0 of A is now 0), otherwise bit 0 is 1
            ora(imm(0xFE))                                  # set offset bits 15-9 to 1. reversed Z is already in bit 0
            bne(rel_at("GOT_OFFSET_HI"))                    # go store high byte, read low byte of match offset and prepare match
                                                            # (*same as JMP GOT_OFFSET_HI but shorter)
            # --------------------------------------------- #
            label("REPMATCH_OR_LARGE_OFFSET")
            asl(a)                                          # 13 bit offset?
            bcs(rel_at("REPMATCH_OR_16_BIT"))               # handle rep-match or 16-bit offset if not

                                                            # 10Z: 13 bit offset

            jsr(at("GETCOMBINEDBITS"))                      # rotate Z bit into bit 8, read nibble for bits 12-9
            adc(imm(0xDE))                                  # set bits 15-13 to 1 and substract 2 (to substract 512)
            bne(rel_at("GOT_OFFSET_HI"))                    # go store high byte, read low byte of match offset and prepare match
                                                            # (*same as JMP GOT_OFFSET_HI but shorter)

            # --------------------------------------------- #
            label("REPMATCH_OR_16_BIT")                     # rep-match or 16 bit offset
            bmi(rel_at("REP_MATCH"))                        # reuse previous offset if so (rep-match)

                                                            # 110: handle 16 bit offset
            jsr(at("GETSRC"))                               # grab high 8 bits
            label("GOT_OFFSET_HI")
            tax()
            jsr(at("GETSRC"))                               # grab low 8 bits
            label("GOT_OFFSET_LO")

            # shazzam: var replaced by labels +1
            sta(at("OFFSLO")+1)                             # store low byte of match offset
            stx(at("OFFSHI")+1)                             # store high byte of match offset

            # --------------------------------------------- #
            label("REP_MATCH")

            # Forward decompression - add match offset
            clc()                                           # add dest + match offset
            lda(at("PUTDST")+1)                             # low 8 bits

            # --------------------------------------------- #
            # shazzam: var replaced by labels +1
            #OFFSLO = *+1
            label("OFFSLO")
            adc(imm(0xDE))
            sta(at("COPY_MATCH_LOOP")+1)                    # store back reference address
            # OFFSHI = *+1
            label("OFFSHI")
            lda(imm(0xAD))                                  # high 8 bits

            adc(at("PUTDST")+2)
            sta(at("COPY_MATCH_LOOP")+2)                    # store high 8 bits of address

            pla()                                           # retrieve token from stack again
            andr(imm(0x07))                                 # isolate match len (MMM)
            adc(imm(0x01))                                  # add MIN_MATCH_SIZE_V2 and carry
            cmp(imm(0x09))                                  # MIN_MATCH_SIZE_V2 + MATCH_RUN_LEN_V2?
            bcc(rel_at("PREPARE_COPY_MATCH"))               # if less, length is directly embedded in token

            jsr(at("GETNIBBLE"))                            # get extra match length nibble
                                                            # add nibble to len from token
            adc(imm(0x08))                                  # (MIN_MATCH_SIZE_V2 + MATCH_RUN_LEN_V2) minus carry
            cmp(imm(0x18))                                  # MIN_MATCH_SIZE_V2 + MATCH_RUN_LEN_V2 + 15?
            bcc(rel_at("PREPARE_COPY_MATCH"))               # if less, match length is complete

            jsr(at("GETSRC"))                               # get extra byte of variable match length
                                                            # the carry is always set by the cmp above
                                                            # GETSRC doesn"t change it
            sbc(imm(0xE8))                                  # overflow?

            # --------------------------------------------- #
            label("PREPARE_COPY_MATCH")
            tax()
            bcc(rel_at("PREPARE_COPY_MATCH_Y"))             # if not, the match length is complete
            beq(rel_at("DECOMPRESSION_DONE"))               # if EOD code, bail

                                                            # Handle 16 bits match length
            jsr(at("GETLARGESRC"))                          # grab low 8 bits in X, high 8 bits in A
            tay()                                           # put high 8 bits in Y

            # --------------------------------------------- #
            label("PREPARE_COPY_MATCH_Y")
            txa()
            beq(rel_at("COPY_MATCH_LOOP"))
            iny()

            # --------------------------------------------- #
            label("COPY_MATCH_LOOP")
            lda(at(0xDEAD))                                 # get one byte of backreference
            jsr(at("PUTDST"))                               # copy to destination

            # Forward decompression -- put backreference bytes forward
            inc(at("COPY_MATCH_LOOP")+1)
            beq(rel_at("GETMATCH_ADJ_HI"))

            # --------------------------------------------- #
            label("GETMATCH_DONE")
            dex()
            bne(rel_at("COPY_MATCH_LOOP"))
            dey()
            bne(rel_at("COPY_MATCH_LOOP"))
            jmp(at("DECODE_TOKEN"))

            # --------------------------------------------- #
            label("GETMATCH_ADJ_HI")
            inc(at("COPY_MATCH_LOOP")+2)
            jmp(at("GETMATCH_DONE"))

            # --------------------------------------------- #
            label("GETCOMBINEDBITS")
            eor(imm(0x80))
            asl(a)
            php()

            jsr(at("GETNIBBLE"))                            # get nibble into bits 0-3 (for offset bits 1-4)
            plp()                                           # merge Z bit as the carry bit (for offset bit 0)
            rol(a)                                          # nibble -> bits 1-4# carry(!Z bit) -> bit 0 # carry cleared
            label("DECOMPRESSION_DONE")
            rts()

            # --------------------------------------------- #
            label("GETNIBBLE")
            # NIBBLES = *+1
            label("NIBBLES")
            lda(imm(0xAA))
            lsr(at(NIBCOUNT))
            bcc(rel_at("NEED_NIBBLES"))
            andr(imm(0x0F))                                 # isolate low 4 bits of nibble
            rts()

            # --------------------------------------------- #
            label("NEED_NIBBLES")
            inc(at(NIBCOUNT))
            jsr(at("GETSRC"))                               # get 2 nibbles

            # shazzam: replaced var by label+1
            sta(at("NIBBLES")+1)
            lsr(a)
            lsr(a)
            lsr(a)
            lsr(a)
            sec()
            rts()

            # --------------------------------------------- #
            #  Forward decompression -- get and put bytes forward
            label("GETPUT")
            jsr(at("GETSRC"))

            # --------------------------------------------- #
            label("PUTDST")

            # LZSA_DST_LO = *+1
            # LZSA_DST_HI = *+2
            label("LZSA_DST", is_global=True)
            sta(at(0xDEAD))
            inc(at("PUTDST")+1)
            beq(rel_at("PUTDST_ADJ_HI"))
            rts()

            # --------------------------------------------- #
            label("PUTDST_ADJ_HI")
            inc(at("PUTDST")+2)
            rts()

            # --------------------------------------------- #
            label("GETLARGESRC")
            jsr(at("GETSRC"))                               # grab low 8 bits
            tax()                                           # move to X
                                                            # fall through grab high 8 bits

            # --------------------------------------------- #
            label("GETSRC")
            # LZSA_SRC_LO = *+1
            # LZSA_SRC_HI = *+2
            label("LZSA_SRC", is_global=True)
            lda(at(0xDEAD))
            inc(at("GETSRC")+1)
            beq(rel_at("GETSRC_ADJ_HI"))
            rts()

            # --------------------------------------------- #
            label("GETSRC_ADJ_HI")
            inc(at("GETSRC")+2)
            rts()

        else:

            self.logger.info("Using Small lzsa depacker")

            ldy(imm(0x00))
            sty(at(NIBCOUNT))

            label("DECODE_TOKEN")
            jsr(at("GETSRC"))                        # read token byte: XYZ|LL|MMM
            pha()                                  # preserve token on stack

            andr(imm(0x18))                             # isolate literals count (LL)
            beq(rel_at("NO_LITERALS"))                      # skip if no literals to copy
            lsr(a)                                  # shift literals count into place
            lsr(a)
            lsr(a)
            cmp(imm(0x03))                             # LITERALS_RUN_LEN_V2?
            bcc(rel_at("PREPARE_COPY_LITERALS"))            # if less, count is directly embedded in token

            jsr(at("GETNIBBLE"))                        # get extra literals length nibble
                                                    # add nibble to len from token
            adc(imm(0x02))                             # (LITERALS_RUN_LEN_V2) minus carry
            cmp(imm(0x12))                             # LITERALS_RUN_LEN_V2 + 15 ?
            bcc(rel_at("PREPARE_COPY_LITERALS"))            # if less, literals count is complete

            jsr(at("GETSRC"))                           # get extra byte of variable literals count
                                                    # the carry is always set by the cmp above
                                                    # GETSRC doesn't change it
            SBC(imm(0xEE))                             # overflow?

            label("PREPARE_COPY_LITERALS")
            tax()
            bcc(rel_at("PREPARE_COPY_LITERALS_HIGH"))       # if not, literals count is complete

                                                    # handle 16 bits literals count
                                                    # literals count = directly these 16 bits
            jsr(at("GETLARGESRC"))                      # grab low 8 bits in X, high 8 bits in A
            tay()                                  # put high 8 bits in Y

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

            ldx(imm(0xFF))                             # set offset bits 15-8 to 1

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
            asl(a)                                  # 13 bit offset?
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
            sta(at("OFFSLO")+1)                           # store low byte of match offset
            stx(at("OFFSHI")+1)                           # store high byte of match offset

            label("REP_MATCH")
            # Forward decompression - add match offset

            clc()                                  # add dest + match offset
            lda(at("PUTDST")+1)                         # low 8 bits

            # OFFSLO = *+1
            label("OFFSLO")
            adc(imm(0xAA))
            sta(at("COPY_MATCH_LOOP")+1)                # store back reference address
            # OFFSHI = *+1
            label("OFFSHI")
            LDA(imm(0xAA))                             # high 8 bits
            adc(at("PUTDST")+2)
            sta(at("COPY_MATCH_LOOP")+2)                # store high 8 bits of address

            pla()                                  # retrieve token from stack again
            andr(imm(0x07))                             # isolate match len (MMM)
            adc(imm(0x01))                             # add MIN_MATCH_SIZE_V2 and carry
            cmp(imm(0x09))                             # MIN_MATCH_SIZE_V2 + MATCH_RUN_LEN_V2?
            bcc(rel_at("PREPARE_COPY_MATCH"))               # if less, length is directly embedded in token

            jsr(at("GETNIBBLE"))                        # get extra match length nibble
                                                    # add nibble to len from token
            adc(imm(0x08))                             # (MIN_MATCH_SIZE_V2 + MATCH_RUN_LEN_V2) minus carry
            cmp(imm(0x18))                             # MIN_MATCH_SIZE_V2 + MATCH_RUN_LEN_V2 + 15?
            bcc(rel_at("PREPARE_COPY_MATCH"))               # if less, match length is complete

            jsr(at("GETSRC"))                           # get extra byte of variable match length
                                                    # the carry is always set by the cmp above
                                                    # GETSRC doesn't change it
            sbc(imm(0xE8))                             # overflow?

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

            # Forward decompression -- put backreference bytes forward

            inc(at("COPY_MATCH_LOOP")+1)
            bne(rel_at("GETMATCH_DONE"))
            inc(at("COPY_MATCH_LOOP")+2)
            label("GETMATCH_DONE")

            dex()
            bne(rel_at("COPY_MATCH_LOOP"))
            dey()
            bne(rel_at("COPY_MATCH_LOOP"))
            jmp(at("DECODE_TOKEN"))

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
            # NIBBLES = *+1
            LDA(imm(0xAA))
            lsr(at(NIBCOUNT))
            bcs(rel_at("HAS_NIBBLES"))

            inc(at(NIBCOUNT))
            jsr(at("GETSRC"))                           # get 2 nibbles
            # sta(at("NIBBLES"))
            sta(at("GETNIBBLE")+1)

            lsr(a)
            lsr(a)
            lsr(a)
            lsr(a)
            sec()

            label("HAS_NIBBLES")
            andr(imm(0x0F))                             # isolate low 4 bits of nibble
            rts()

            # Forward decompression -- get and put bytes forward
            label("GETPUT")
            jsr(at("GETSRC"))
            label("PUTDST")
            label("LZSA_DST", is_global=True)
            # LZSA_DST_LO = *+1
            # LZSA_DST_HI = *+2
            sta(at(0xAAAA))
            inc(at("PUTDST")+1)
            bne(rel_at("PUTDST_DONE"))
            inc(at("PUTDST")+2)
            label("PUTDST_DONE")
            rts()

            label("GETLARGESRC")
            jsr(at("GETSRC"))                           # grab low 8 bits
            tax()                                  # move to X
                                                    # fall through grab high 8 bits

            label("GETSRC")
            # LZSA_SRC_LO = *+1
            # LZSA_SRC_HI = *+2
            label("LZSA_SRC", is_global=True)
            lda(at(0xAAAA))
            inc(at("GETSRC")+1)
            bne(rel_at("GETSRC_DONE"))
            inc(at("GETSRC")+2)
            label("GETSRC_DONE")
            rts()


