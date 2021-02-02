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
prefs = assembler.get_code_format()
set_prefs(
    default_code_segment="start",
    code_format=prefs.code,
    comments_format=prefs.comments,
    directive_prefix=prefs.directive,
    directive_delimiter=prefs.delimiter
)

program_name = os.path.splitext(os.path.basename(__file__))[0]


@reloading
def code():

    # define here or anywhere your variables
    nb_sprites = 6

    spd = p.read_spd("resources/ball.spd")
    sid = p.read_sid("resources/Meetro.sid")

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
        nop()
        # y_scroll = 0
        # for y in range(40, 50):
        #     with rasterline(nb_sprites=8, y_pos=y, y_scroll=y_scroll):
        #         if (y & 7) == y_scroll:
        #             nop()
        #             nop()
        #             nop()
        #         else:
        #             jmp(abs_adr=0x100)
        #             jmp(abs_adr=0x1000, ind=True)


        print(f"{s.get_stats()}")

    # generate listing
    gen_code(assembler, format_code=prefs, gen_listing=True)

    # finally assemble segments to PRG using cross assembler then crunch it!
    assemble_prg(assembler, start_address=0x0801)

if __name__ == "__main__":
    generate(code, program_name)



