from reloading import reloading

# if shazzam not installed
import sys
sys.path.append(".")

from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a

from shazzam.macros.aliases import color, vic
import shazzam.plugins.plugins as p
from shazzam.drivers.assemblers.CC65 import CC65
from shazzam.drivers.crunchers.Lzsa1 import Lzsa1
import shazzam.plugins.plugins as p


# define your cross assembler
assembler = CC65("cc65", "third_party/cc65/bin/cl65")
data_cruncher = Lzsa1("third_party/lzsa/lzsa")

program_name = os.path.splitext(os.path.basename(__file__))[0]

@reloading
def code():

    # define here or anywhere, doesn't matter, your variables
    sid = p.read_sid("resources/Meetro.sid")
    segments = {
        assembler.get_code_segment(): 0x0801,
        "packedata": 0x3000,
        "depacker": 0xA000,
    }

    with segment(segments["packedata"], "packedata") as s:
        incbin(data_cruncher.crunch_incbin(data=sid.data))
        print(s.get_stats())

    # CC65 generates basic header, no macro needed just to define the CODE segment
    with segment(segments[assembler.get_code_segment()], assembler.get_code_segment()) as s:

        # zp locations where to store src and dst addresses
        apl_srcptr = 0xFC
        apl_dstptr = 0xFE

        sei()

        lda(imm(0x7f))      # a = 0x07f = %0111 1111
        sta(at(0xdc0d))     # Set Interrupt control to enable all timers interrupts
        sta(at(0xdd0d))     # Set Interrupt control to enable all timers interrupts

        lda(imm(0x01))      # a = 1
        sta(at(0xd01a))     # set Interrupt control register to enable raster interrupts only

        # set screen
        lda(imm(0x1b))      # a = 0x01b = 0001 1011
        ldx(imm(0x08))      # x = 0x08  = 0000 1000
        ldy(imm(0x14))      # y = 0x014 = 0001 010 0, 0x024 = 0010 010 0

        sta(at(0xd011))     # Screen control register #1 = a => in text mode
        stx(at(0xd016))     # Screen control register #2 = x => 40 columns mode
        sty(at(0xd018))     # Set memory setup register to charmem at 1000-$17FF and screen ram to 0x0400-$07FF => bad as driver is in(at(0x00400?

        lda(imm("<irq"))    # Set IRQ address low byte in a
        ldx(imm(">irq"))    # Set IRQ address high byte in x

        ldy(imm(0x7e))      # y = 0x07e
        sta(at(0x0314))     # set Execution address of interrupt service routine to low byte irq address
        stx(at(0x0315))     # set Execution address+1 of interrupt service routine to high byte irq address
        sty(at(0xd012))     # set Raster line to generate interrupt at raster line 0x07e = 126

        # read interrupt registers clear them
        lda(at(0xdc0d))     # read interrupt control register 1 in a
        lda(at(0xdd0d))     # read interrupt control register 2 in a
        asl(at(0xd019))     # Ack raster interrupt

        lda(imm(0x36))      # TURN OFF BASIC ROM to access addres behind the BASIC ROM ($A000-$BFFF)
        sta(at(0x01))

        jsr(at("depack"))

        # init player
        lda(imm(0))
        tax()
        tay()
        jsr(at(0x1000))     # jump to SID player init, song 0,...

        lda(imm(0x37))      # TURN BASIC ROM BACK ON
        sta(at(0x001))

        cli()               # enable interrupts

        label("loop")       # infinite loop
        jmp(at("loop"))

        # -------------------------------------------------
        # IRQ routine
        # -------------------------------------------------
        label("irq")
        lda(imm(0x01))
        sta(at(0xd019))

        lda(imm(0x36))      # TURN OFF BASIC ROM
        sta(at(0x01))

        inc(at(vic.border_col))
        jsr(at(0x1003))     # call SID player
        dec(at(vic.border_col))

        lda(imm(0x37))      # TURN BASIC ROM ON
        sta(at(0x01))

        jmp(at(0x0ea81))    # Others can be ended with JMP 0xEA81, which simply goes to the end of the kernel handler.

        # -------------------------------------------------
        # Depacking caller routine, need access to zp
        # -------------------------------------------------
        # in:
        # * LZSA_SRC (LO+1, HI+2) contains the compressed raw block address
        # * LZSA_DST (LO+1, HI+2) contains the destination buffer address
        #
        # out:
        # * LZSA_DST_LO (LO+1, HI+2) contains the last decompressed byte address, +1
        mode = 2

        label("depack")
        packed_data = get_segment_addresses("packedata").start_address
        print(f"Packed data ends at {packed_data:04X}")

        if mode != 2:
            # set packed data src / dst
            lda(imm(packed_data & 0xff))
            sta(at("LZSA_SRC")+1)

            lda(imm(packed_data >> 8))
            sta(at("LZSA_SRC")+2)

            lda(imm(0x1000 & 0xff))
            sta(at("LZSA_DST")+1)

            lda(imm(0x1000 >> 8))
            sta(at("LZSA_DST")+2)
        else:

            LZSA_SRC_LO = 0xFC
            LZSA_SRC_HI = 0xFD
            LZSA_DST_LO = 0xFE
            LZSA_DST_HI = 0xFF

            # set packed data src / dst
            lda(imm(packed_data & 0xff))
            sta(at(LZSA_SRC_LO))

            lda(imm(packed_data >> 8))
            sta(at(LZSA_SRC_HI))

            # depacked data are located at apl_dstptr+126 bytes
            lda(imm(0x1000 & 0xff))
            sta(at(LZSA_DST_LO))

            lda(imm(0x1000 >> 8))
            sta(at(LZSA_DST_HI))

        # unpack data forward.
        depack_start = get_current_address()
        jsr(at("DECOMPRESS_LZSA1"))
        depack_end = get_current_address()

        rts()

    with segment(segments["depacker"], "depacker") as s:
        data_cruncher.generate_depacker_routine(s.get_stats().start_address, mode=mode)

    # generate listing
    gen_code(assembler, gen_listing=True)

    # finally assemble segments to PRG using cross assembler then crunch it!
    assemble_prg(assembler, start_address=0x0801)

    print(f"Counting cycles from {depack_start:04X} to {depack_end:04X}")
    _, _, cycles_used = emulate_program(entry_point_address=0x0801, stop_address=depack_end, cycles_count_start=depack_start, cycles_count_end=depack_end, debug_mode=False)

    routine_size = get_segment_addresses("depacker").end_address - get_segment_addresses("depacker").start_address
    print(f"Depacker used {routine_size} bytes and {cycles_used} cycles (around [{round(cycles_used/19656, 2)}/{round(cycles_used/18656, 2)}] vbls [IDLE/ACTIVE]) or [{round(cycles_used/19656/50*1000, 2)}/{round(cycles_used/18656/50*1000, 2)}] ms")
    print(f"Packed data size: {get_segment_addresses('packedata').end_address - get_segment_addresses('packedata').start_address} bytes")


if __name__ == "__main__":
    generate(code, program_name)

