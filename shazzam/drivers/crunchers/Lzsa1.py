from shazzam.Cruncher import Cruncher
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a


class Lzsa1(Cruncher):

    def __init__(self, exe_path: str):

        cmd_prg_template = None
        cmd_bin_template = [exe_path, "-r", "FILENAME_TO_SET", "OUTPUT_TO_SET"]
        super().__init__("lzsa", exe_path, cmd_prg_template, cmd_bin_template)

    def generate_depacker_routine(self, address: int, mode: int = 2) -> None:
        """[summary]

        Args:
            address (int): [description]
            mode (int, optional): [description]. Defaults to 2.
        """
        label("DECOMPRESS_LZSA1", is_global=True)

        if mode == 0:
            ldy(imm(0x00))

            label("DECODE_TOKEN")
            jsr(at("GETSRC"))
            pha()
            andr(imm(0x70))
            beq(rel_at("NO_LITERALS"))
            cmp(imm(0x70))
            bne(rel_at("PREPARE_COPY_LITERALS"))

            jsr(at("GETSRC"))

            sbc(imm(0xF9))
            bcc(rel_at("PREPARE_COPY_LITERALS_DIRECT"))
            beq(rel_at("LARGE_VARLEN_LITERALS"))

            jsr(at("GETSRC"))
            iny()
            bcs(rel_at("PREPARE_COPY_LITERALS_DIRECT"))

            label("LARGE_VARLEN_LITERALS")
            jsr(at("GETLARGESRC"))
            tay()
            txa()
            bcs(rel_at("PREPARE_COPY_LARGE_LITERALS"))

            label("PREPARE_COPY_LITERALS")
            tax()
            lda(at("SHIFT_TABLE")-1,x)

            label("PREPARE_COPY_LITERALS_DIRECT")
            tax()

            label("PREPARE_COPY_LARGE_LITERALS")
            beq(rel_at("COPY_LITERALS"))
            iny()

            label("COPY_LITERALS")
            jsr(at("GETPUT"))
            dex()
            bne(rel_at("COPY_LITERALS"))
            dey()
            bne(rel_at("COPY_LITERALS"))

            label("NO_LITERALS")
            pla()
            pha()
            bmi(rel_at("GET_LONG_OFFSET"))

            jsr(at("GETSRC"))
            tax()
            lda(imm(0xFF))
            bne(rel_at("GOT_OFFSET"))

            label("SHORT_VARLEN_MATCHLEN")
            jsr(at("GETSRC"))
            iny()

            label("PREPARE_COPY_MATCH")
            tax()
            label("PREPARE_COPY_MATCH_Y")
            txa()
            beq(rel_at("COPY_MATCH_LOOP"))
            iny()

            label("COPY_MATCH_LOOP")
            lda(at(0xdead))
            jsr(at("PUTDST"))
            inc(at("COPY_MATCH_LOOP")+1)
            beq(rel_at("GETMATCH_ADJ_HI"))

            label("GETMATCH_DONE")
            dex()
            bne(rel_at("COPY_MATCH_LOOP"))
            dey()
            bne(rel_at("COPY_MATCH_LOOP"))
            beq(rel_at("DECODE_TOKEN"))

            label("GETMATCH_ADJ_HI")
            inc(at("COPY_MATCH_LOOP")+2)
            jmp(at("GETMATCH_DONE"))

            label("GET_LONG_OFFSET")
            jsr(at("GETLARGESRC"))

            label("GOT_OFFSET")
            # sta(at("OFFSHI")
            sta(at("OFFSHI")+1)
            txa()

            clc()
            adc(at("PUTDST")+1)
            sta(at("COPY_MATCH_LOOP")+1)
            # OFFSHI = *+1
            label("OFFSHI")
            lda(imm(0xAA))

            adc(at("PUTDST")+2)
            sta(at("COPY_MATCH_LOOP")+2)

            pla()
            andr(imm(0x0F))
            adc(imm(0x02))
            cmp(imm(0x12))
            bcc(rel_at("PREPARE_COPY_MATCH"))

            jsr(at("GETSRC"))

            sbc(imm(0xEE))
            bcc(rel_at("PREPARE_COPY_MATCH"))
            bne(rel_at("SHORT_VARLEN_MATCHLEN"))

            jsr(at("GETLARGESRC"))
            tay()

            bne(rel_at("PREPARE_COPY_MATCH_Y"))

            label("DECOMPRESSION_DONE")
            rts()

            label("SHIFT_TABLE")
            byte([     0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00])
            byte([ 0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01])
            byte([ 0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02,0x02])
            byte([ 0x03,0x03,0x03,0x03,0x03,0x03,0x03,0x03,0x03,0x03,0x03,0x03,0x03,0x03,0x03,0x03])
            byte([ 0x04,0x04,0x04,0x04,0x04,0x04,0x04,0x04,0x04,0x04,0x04,0x04,0x04,0x04,0x04,0x04])
            byte([ 0x05,0x05,0x05,0x05,0x05,0x05,0x05,0x05,0x05,0x05,0x05,0x05,0x05,0x05,0x05,0x05])
            byte([ 0x06,0x06,0x06,0x06,0x06,0x06,0x06,0x06,0x06,0x06,0x06,0x06,0x06,0x06,0x06,0x06])
            byte([ 0x07,0x07,0x07,0x07,0x07,0x07,0x07,0x07,0x07,0x07,0x07,0x07,0x07,0x07,0x07,0x07])

            label("GETPUT")
            jsr(at("GETSRC"))

            label("PUTDST")
            # LZSA_DST_LO = *+1
            # LZSA_DST_HI = *+2
            label("LZSA_DST", is_global=True)
            sta(at(0xAAAA))
            inc(at("PUTDST")+1)
            beq(rel_at("PUTDST_ADJ_HI"))
            rts()

            label("PUTDST_ADJ_HI")
            inc(at("PUTDST")+2)
            rts()

            label("GETLARGESRC")
            jsr(at("GETSRC"))
            tax()

            label("GETSRC")
            # LZSA_SRC_LO = *+1
            # LZSA_SRC_HI = *+2
            label("LZSA_SRC", is_global=True)
            lda(at(0xAAAA))
            inc(at("GETSRC")+1)
            beq(rel_at("GETSRC_ADJ_HI"))
            rts()

            label("GETSRC_ADJ_HI")
            inc(at("GETSRC")+2)
            rts()

        elif mode == 1:
            ldy(imm(0x00))

            label("DECODE_TOKEN")
            jsr(at("GETSRC"))
            pha()
            andr(imm(0x70))
            beq(rel_at("NO_LITERALS"))
            lsr(a)
            lsr(a)
            lsr(a)
            lsr(a)
            cmp(imm(0x07))
            bcc(rel_at("PREPARE_COPY_LITERALS"))
            jsr(at("GETSRC"))
            sbc(imm(0xF9))
            bcc(rel_at("PREPARE_COPY_LITERALS"))
            beq(rel_at("LARGE_VARLEN_LITERALS"))
            jsr(at("GETSRC"))
            iny()
            bcs(rel_at("PREPARE_COPY_LITERALS"))

            label("LARGE_VARLEN_LITERALS")
            jsr(at("GETLARGESRC"))
            tay()
            txa()
            label("PREPARE_COPY_LITERALS")
            tax()
            beq(rel_at("COPY_LITERALS"))
            iny()

            label("COPY_LITERALS")
            jsr(at("GETPUT"))
            dex()
            bne(rel_at("COPY_LITERALS"))
            dey()
            bne(rel_at("COPY_LITERALS"))

            label("NO_LITERALS")
            pla()
            pha()
            bmi(rel_at("GET_LONG_OFFSET"))
            jsr(at("GETSRC"))
            tax()
            lda(imm(0xFF))
            bne(rel_at("GOT_OFFSET"))

            label("SHORT_VARLEN_MATCHLEN")
            jsr(at("GETSRC"))
            iny()
            label("PREPARE_COPY_MATCH")
            tax()

            label("PREPARE_COPY_MATCH_Y")
            txa()
            beq(rel_at("COPY_MATCH_LOOP"))
            iny()

            label("COPY_MATCH_LOOP")
            lda(at(0xAAAA))
            jsr(at("PUTDST"))
            inc(at("COPY_MATCH_LOOP")+1)
            bne(rel_at("GETMATCH_DONE"))
            inc(at("COPY_MATCH_LOOP")+2)

            label("GETMATCH_DONE")
            dex()
            bne(rel_at("COPY_MATCH_LOOP"))
            dey()
            bne(rel_at("COPY_MATCH_LOOP"))
            beq(rel_at("DECODE_TOKEN"))
            label("GET_LONG_OFFSET")
            jsr(at("GETLARGESRC"))
            label("GOT_OFFSET")
            sta(at("OFFSHI")+1)
            txa()
            clc()
            adc(at("PUTDST")+1)
            sta(at("COPY_MATCH_LOOP")+1)
            # OFFSHI = *+1
            label("OFFSHI")
            lda(imm(0xAA))
            adc(at("PUTDST")+2)
            sta(at("COPY_MATCH_LOOP")+2)
            pla()
            andr(imm(0x0F))
            adc(imm(0x02))
            cmp(imm(0x12))
            bcc(rel_at("PREPARE_COPY_MATCH"))
            jsr(at("GETSRC"))
            sbc(imm(0xEE))
            bcc(rel_at("PREPARE_COPY_MATCH"))
            bne(rel_at("SHORT_VARLEN_MATCHLEN"))
            jsr(at("GETLARGESRC"))
            tay()
            bne(rel_at("PREPARE_COPY_MATCH_Y"))

            label("DECOMPRESSION_DONE")
            rts()

            label("GETPUT")
            jsr(at("GETSRC"))
            label("PUTDST")
            # LZSA_DST_LO = *+1
            # LZSA_DST_HI = *+2
            label("LZSA_DST", is_global=True)
            sta(at(0xAAAA))
            inc(at("PUTDST")+1)
            bne(rel_at("PUTDST_DONE"))
            inc(at("PUTDST")+2)

            label("PUTDST_DONE")
            rts()

            label("GETLARGESRC")
            jsr(at("GETSRC"))
            tax()
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

        elif mode == 2:

            lzsa_cmdbuf = 0xF9
            lzsa_winptr = 0xFA
            lzsa_srcptr = 0xFC
            lzsa_dstptr = 0xFE

            LZSA_SRC_LO = 0xFC
            LZSA_SRC_HI = 0xFD
            LZSA_DST_LO = 0xFE
            LZSA_DST_HI = 0xFF

            def LZSA_INC_PAGE():
                inc(at(lzsa_srcptr)+1)


            def LZSA_GET_SRC():
                skip = get_anonymous_label("skip")
                lda(ind_at(lzsa_srcptr),y)
                inc(at(lzsa_srcptr)+0)
                bne(rel_at(skip))
                LZSA_INC_PAGE()
                label(skip)

            label("lzsa1_unpack")
            ldy(imm(0))
            ldx(imm(0))
            label(".cp_length")
            LZSA_GET_SRC()
            sta(at(lzsa_cmdbuf))
            andr(imm(0x70))
            beq(rel_at(".lz_offset"))
            lsr(a)
            lsr(a)
            lsr(a)
            lsr(a)
            cmp(imm(0x07))
            bne(rel_at(".got_cp_len"))
            jsr(at(".get_length"))

            label(".got_cp_len")
            tay()
            beq(rel_at(".cp_page"))
            inx()

            label(".get_cp_src")
            clc()
            adc(at(lzsa_srcptr)+0)
            sta(at(lzsa_srcptr)+0)
            bcs(rel_at(".get_cp_dst"))
            dec(at(lzsa_srcptr)+1)

            label(".get_cp_dst")
            tya()
            clc()
            adc(at(lzsa_dstptr)+0)
            sta(at(lzsa_dstptr)+0)
            bcs(rel_at(".get_cp_idx"))
            dec(at(lzsa_dstptr)+1)

            label(".get_cp_idx")
            tya()
            eor(imm(0xFF))
            tay()
            iny()

            label(".cp_page")
            lda(ind_at(lzsa_srcptr),y)
            sta(ind_at(lzsa_dstptr),y)
            iny()
            bne(rel_at(".cp_page"))
            inc(at(lzsa_srcptr)+1)
            inc(at(lzsa_dstptr)+1)
            dex()
            bne(rel_at(".cp_page"))
            label(".lz_offset")
            LZSA_GET_SRC()
            clc()
            adc(at(lzsa_dstptr)+0)
            sta(at(lzsa_winptr)+0)
            lda(imm(0xFF))
            bit(at(lzsa_cmdbuf))
            bpl(rel_at(".hi_offset"))
            LZSA_GET_SRC()

            label(".hi_offset")
            adc(at(lzsa_dstptr)+1)
            sta(at(lzsa_winptr)+1)
            label(".lz_length")
            lda(at(lzsa_cmdbuf))
            andr(imm(0x0F))
            adc(imm(0x03-1))
            cmp(imm(0x12))
            bne(rel_at(".got_lz_len"))
            jsr(at(".get_length"))

            label(".got_lz_len")
            tay()
            beq(rel_at(".lz_page"))
            inx()

            label(".get_lz_win")
            clc()
            adc(at(lzsa_winptr)+0)
            sta(at(lzsa_winptr)+0)
            bcs(rel_at(".get_lz_dst"))
            dec(at(lzsa_winptr)+1)

            label(".get_lz_dst")
            tya()
            clc()
            adc(at(lzsa_dstptr)+0)
            sta(at(lzsa_dstptr)+0)
            bcs(rel_at(".get_lz_idx"))
            dec(at(lzsa_dstptr)+1)

            label(".get_lz_idx")
            tya()
            eor(imm(0xFF))
            tay()
            iny()

            label(".lz_page")
            lda(ind_at(lzsa_winptr),y)
            sta(ind_at(lzsa_dstptr),y)
            iny()
            bne(rel_at(".lz_page"))
            inc(at(lzsa_winptr)+1)
            inc(at(lzsa_dstptr)+1)
            dex()
            bne(rel_at(".lz_page"))
            jmp(at(".cp_length"))
            label(".get_length")
            clc()
            adc(ind_at(lzsa_srcptr),y)
            inc(at(lzsa_srcptr)+0)
            bne(rel_at(".skip_inc"))
            LZSA_INC_PAGE()

            label(".skip_inc")
            bcc(rel_at(".got_length"))
            cmp(imm(0x00))
            beq(rel_at(".extra_word"))

            label(".extra_byte")
            inx()
            jmp(at("lzsa1_get_byte"))

            label(".extra_word")
            jsr(at("lzsa1_get_byte"))
            pha()
            jsr(at("lzsa1_get_byte"))
            tax()
            beq(rel_at(".finished"))
            pla()
            rts()

            label("lzsa1_get_byte")
            lda(ind_at(lzsa_srcptr),y)
            inc(at(lzsa_srcptr)+0)
            beq(rel_at("lzsa1_next_page"))

            label(".got_length")
            rts()

            label("lzsa1_next_page")
            inc(at(lzsa_srcptr)+1)
            rts()

            label(".finished")
            pla()
            pla()
            pla()
            rts()

        else:
            raise ValueError(f"Unknown mode: {mode}")

