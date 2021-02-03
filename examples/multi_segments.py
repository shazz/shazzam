# if shazzam not installed
import sys
sys.path.append(".")

from reloading import reloading
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a
from shazzam.macros.aliases import color, vic
import shazzam.plugins.plugins as p
from shazzam.drivers.assemblers.CC65 import CC65

# define your cross assembler
assembler = CC65("cc65", "third_party/cc65/bin/cl65")
program_name = os.path.splitext(os.path.basename(__file__))[0]

@reloading
def code():

    # define here or anywhere your variables
    vic_bank    = 0x4000
    screen_mem  = 0x2000
    bitmap_mem  = 0x0000
    char_mem    = 0x0000            # not used, 0 is fine

    nb_sprites = 6

    spd = p.read_spd("resources/ball.spd")
    sid = p.read_sid("resources/Meetro.sid")
    kla = p.read_kla('resources/panda.kla')

    # CC65 generates basic header, no macro needed just to define the CODE segment
    with segment(0x0801, assembler.get_code_segment()) as s:
        jmp(abs_adr=0x2000)

    # init segment
    with segment(0x2000, "INIT", use_relative_addressing=True) as s:

        label("start")
        lda(imm=0)
        for i in range(nb_sprites):
            sta(abs_adr=vic.sprite0_x+(2*i))
            sta(abs_adr=vic.sprite0_y+(2*i))

        cpu = s.emulate()
        assert cpu.r.a == 0, f"A should be 1 but it's {cpu.r}"

        lda(imm=1)
        beq(label="is_zero")

        print(s.get_stats())

        jmp(label="top_irq")
        print(f"last instruction '{s.get_last_instruction()}'' took {s.get_last_instruction().get_size()} bytes and {s.get_last_instruction().get_cycle_count()} cycles")
        label(name="is_zero")
        lda(imm=3)

    # irq segment
    with segment(0x3000, "IRQ") as s:

        label("top_irq", is_global=True)
        nop()
        print(f"{s.get_stats()}")

    # set bitmap data at vic_bank + bitmap
    with segment(vic_bank+bitmap_mem, "bitmap", segment_type=SegmentType.BITMAP) as s:
        incbin(kla.bitmap)

    with segment(vic_bank+screen_mem, "screen_ram", segment_type=SegmentType.SCREEN_MEM) as s:
        incbin(kla.scrmem)

    with segment(0xd800, "color_ram", segment_type=SegmentType.REGISTERS) as s:
        incbin(kla.colorram)

    # generate listing
    gen_code(assembler, gen_listing=True)

    # finally assemble segments to PRG using cross assembler then crunch it!
    assemble_prg(assembler, start_address=0x0801)

    # Asking the segment optimizer if we can do better
    optimize_segments()

if __name__ == "__main__":
    generate(code, program_name)



