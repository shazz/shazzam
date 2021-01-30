# if shazzam not installed
import sys
sys.path.append(".")

from reloading import reloading
from shazzam.Segment import SegmentType
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a
from shazzam.macros.aliases import color, vic
from shazzam.drivers.assemblers.CC65 import CC65
import shazzam.plugins.plugins as p
import shazzam.macros.vic as v


# define your cross assembler
assembler = CC65("cc65", "third_party/cc65/bin/cl65")
prefs = assembler.get_code_format()
set_prefs(default_code_segment=assembler.get_code_segment(),
          code_format=prefs.code,
          comments_format=prefs.comments,
          directive_prefix=prefs.directive)

@reloading
def code():

    # define here or anywhere, doesn't matter, your variables
    kla = p.read_kla('resources/panda.kla')
    vic_bank    = 0x4000
    screen_mem  = 0x2000
    bitmap_mem  = 0x0000
    char_mem    = 0x0000            # not used, 0 is fine

    # CC65 generates basic header, no macro needed just to define the CODE segment
    with segment(0x0801, assembler.get_code_segment()) as s:

        v.setup_vic_bank(vic_bank)  # set vic bank

        d018 = v.generate_d018(char_mem, bitmap_mem, screen_mem)
        lda(imm(d018))
        sta(at(vic.mem_setup))      # set vic memory setup

        lda(imm(0b00111000))        # set bitmap mode
        sta(at(vic.scr_ctrl))

        lda(imm(0b11011000))        # set multicolor mode on
        sta(at(vic.scr_ctrl2))

        lda(imm(kla.bg_color))      # set border and window color to picture background color
        sta(at(vic.border_col))
        sta(at(vic.bck_col))

        label("loop")
        jmp(at("loop"))

    # set bitmap data at vic_bank + bimap
    with segment(vic_bank, "bitmap", segment_type=SegmentType.BITMAP) as s:
        incbin(kla.bitmap)

    with segment(vic_bank+screen_mem, "screen_ram", segment_type=SegmentType.SCREEN_MEM) as s:
        incbin(kla.scrmem)

    with segment(0xd800, "color_ram", segment_type=SegmentType.REGISTERS) as s:
        incbin(kla.colorram)

    # generate listing
    gen_code(format_code=prefs, gen_listing=True)

    # finally assemble segments to PRG using cross assembler then crunch it!
    assemble_prg(assembler, start_address=0x0801)

if __name__ == "__main__":
    generate(code, "i_love_koalas")
