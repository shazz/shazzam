# if shazzam not installed
import sys
sys.path.append(".")

from reloading import reloading
from shazzam.Segment import SegmentType
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a
from shazzam.macros.aliases import color, vic
import shazzam.macros.sys as sys
from shazzam.macros.vasyl import *
import shazzam.macros.vlib as vlib

# define your cross assembler
# from shazzam.drivers.assemblers.CC65 import CC65
# assembler = CC65("cc65", "third_party/cc65/bin/cl65")
from shazzam.drivers.assemblers.C64jasm import C64jasm
assembler = C64jasm("c64jasm", "/home/shazz/projects/c64/bin/c64jasm")

program_name = os.path.splitext(os.path.basename(__file__))[0]

@reloading
def code():

    # define here or anywhere, doesn't matter, your variables

    import examples.vasyl.logo_dlist

    # CC65 generates basic header, no macro needed just to define the CODE segment
    with segment(0x0801, assembler.get_code_segment()) as s:

        if not assembler.support_basic():
            sys.basic_start()

        label("init")
        jsr(at("knock_knock"))

        lda(at(0xd011))
        sta(at("preserve_ctrl1"))
        lda(at(0xd020))
        sta(at("preserve_ec"))
        lda(imm(0))                   # turn off VIC-II display fetches
        sta(at(0xd011))                # so that badlines do not interfere

        jsr(at("copy_and_activate_dlist"))
        label("loop")
        jsr(at(0xffe4))                # check if key pressed
        beq(rel_at("loop"))

        lda(imm(0))                   # turn off the display list
        sta(at(VREG_CONTROL))

        lda(at("preserve_ctrl1"))
        sta(at(0xd011))
        lda(at("preserve_ec"))
        sta(at(0xd020))

        rts()

    with segment(0x02000, "DATA") as s:
        label("preserve_ctrl1", is_global=True)
        byte(0)

        label("preserve_ec", is_global=True)
        byte(0)

    with segment(0x1E00, "VLIB") as s:

        # include vlib routines
        vasyl_segment_size = get_segment_addresses("VASYL").size
        print(f"Copying Dlist at of size {vasyl_segment_size}")
        vlib.init(vasyl_segment_size)
        vlib.copy_and_activate_dlist(vasyl_segment_size)

    # generate listing
    gen_code(assembler, gen_listing=True)

    # finally assemble segments to PRG using cross assembler then crunch it!
    assemble_prg(assembler, start_address=0x0801)

if __name__ == "__main__":
    generate(code, program_name)
