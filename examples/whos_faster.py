from reloading import reloading
import os

# if shazzam not installed
import sys
sys.path.append(".")

from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a

from shazzam.macros.aliases import color, vic
import shazzam.plugins.plugins as p
from shazzam.drivers.assemblers.CC65 import CC65
from shazzam.drivers.crunchers.C64f import C64f
import shazzam.plugins.plugins as p

# define your cross assembler
assembler = CC65("cc65", "third_party/cc65/bin/cl65")
data_cruncher = C64f("third_party/c64f/c64f")
program_name = os.path.splitext(os.path.basename(__file__))[0]

@reloading
def code():

    # define here or anywhere, doesn't matter, your variables
    sid = p.read_sid("resources/Meetro.sid")
    segments = {
        assembler.get_code_segment(): assembler.get_code_segment_address(),
        "packedata": 0x3000,
        "depacker": 0xA000,
    }

    # CC65 generates basic header, no macro needed just to define the CODE segment
    with segment(segments[assembler.get_code_segment()], assembler.get_code_segment()) as s:

        sei()

        lda(imm(0x36))      # TURN OFF BASIC ROM to access addres behind the BASIC ROM ($A000-$BFFF)
        sta(at(0x01))

        label("start_perf")
        jsr(at("depack"))
        brk()               # to stop the emulation

        lda(imm(0x37))      # TURN BASIC ROM BACK ON
        sta(at(0x001))

        cli()               # enable interrupts

        label("loop")       # infinite loop
        jmp(at("loop"))

        # -------------------------------------------------
        # Depacking caller routine, need access to zp
        # -------------------------------------------------
        # zp locations where to store src and dst addresses
        apd_src         = 0xf6
        apd_dest        = 0xfe

        label("depack")
        # set packed data src / dst
        lda(imm("<packed_data"))
        sta(at(apd_src))

        lda(imm(">packed_data"))
        sta(at(apd_src)+1)

        lda(imm(0x00))
        sta(at(apd_dest))

        lda(imm(0x40))
        sta(at(apd_dest)+1)

        jsr(at("dc64f"))
        label("end_depack")
        rts()

        # -------------------------------------------------
        # Depacking routine
        # -------------------------------------------------
        # CHANGE use_fast to True or False to benchmark c64f FAST and SMALL depacking routines
        data_cruncher.generate_depacker_routine(s.get_stats().start_address, use_fast=True)

        # -------------------------------------------------
        # Packed data
        # -------------------------------------------------
        label("packed_data")
        incbin(data_cruncher.crunch_incbin(data=sid.data))

        cpu, mmu, cycles_used = s.emulate(start_address="start_perf", cycles_count_start="dc64f", cycles_count_end="end_depack")
        routine_size = get_label_address("packed_data") - get_label_address("dc64f")
        print(f"Depacker used {routine_size} bytes and {cycles_used} cycles (around [{round(cycles_used/19656, 2)}/{round(cycles_used/18656, 2)}] vbls [IDLE/ACTIVE]) since ${get_label_address('dc64f'):04X} (dc64f)")

        expected_results = {
            0x4000: [0x4C, 0x40, 0x10, 0x4C, 0xC1, 0x10, 0x01, 0x02, 0x04, 0x0F, 0x10, 0x00, 0x51, 0x27, 0x3A, 0x07],
            0x4C10: [0xA3, 0x18, 0xA0, 0x1F, 0xA2, 0x37, 0x1F, 0xA3, 0x37, 0x7F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        }

        # checking start / end packed data are well depacked
        print("--------------------------------------------------------------")
        for adr in expected_results.keys():
            print(f"Address ${adr:04X}:", end =' ')
            for i in range(16):
                print(f"{mmu.read(adr + i):02X}", end=' ')
                assert expected_results[adr][i] == mmu.read(adr + i)
            print("")
        print("--------------------------------------------------------------")

    # generate listing
    gen_code(assembler, gen_listing=True)

    # finally assemble segments to PRG using cross assembler then crunch it!
    assemble_prg(assembler, start_address=0x0801)

if __name__ == "__main__":
    generate(code, program_name)



