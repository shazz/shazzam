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
from shazzam.drivers.assemblers.CC65 import CC65

# define your cross assembler
assembler = CC65("cc65", "third_party/cc65/bin/cl65")
program_name = os.path.splitext(os.path.basename(__file__))[0]

@reloading
def code():

    # define here or anywhere, doesn't matter, your variables

    import examples.vasyl.logo_dlist

    # CC65 generates basic header, no macro needed just to define the CODE segment
    with segment(0x0801, assembler.get_code_segment()) as s:

        # sys.basic_start()
        label("init")

        jsr(at("knock_knock"))

        lda(at(53265))
        sta(at("preserve_ctrl1"))
        lda(at(0xd020))
        sta(at("preserve_ec"))
        lda(imm(0))                   # turn off VIC-II display fetches
        sta(at(53265))                # so that badlines do not interfere

        jsr(at("copy_and_activate_dlist"))
        label("loop")
        jsr(at(0xffe4))                # check if key pressed
        beq(rel_at("loop"))

        lda(imm(0))                   # turn off the display list
        sta(at(VREG_CONTROL))
        lda(at("preserve_ctrl1"))
        sta(at(53265))
        lda(at("preserve_ec"))
        sta(at(0xd020))

        rts()

        vasyl_segment_load = "end_main"
        vasyl_segment_size = get_segment_addresses(assembler.get_vasyl_segment()).end_address

        # include vlib routines
        vlib.init(vasyl_segment_load, vasyl_segment_size)
        vlib.copy_and_activate_dlist(vasyl_segment_load, vasyl_segment_size)

        label("end_main")

    # generate listing
    gen_code(assembler, gen_listing=True)

    # finally assemble segments to PRG using cross assembler then crunch it!
    assemble_prg(assembler, start_address=0x0801)

if __name__ == "__main__":
    generate(code, program_name)
