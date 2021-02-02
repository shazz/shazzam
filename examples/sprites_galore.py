# if shazzam not installed
import sys
sys.path.append(".")

from shazzam.drivers.assemblers.CC65 import CC65
import shazzam.plugins.plugins as p
from shazzam.macros.aliases import color, vic
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a
from shazzam.py64gen import *
import shazzam.macros.sys as m
from reloading import reloading

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

    # define here or anywhere, doesn't matter, your variables
    spd = p.read_spd("resources/ball.spd")
    nb_sprites = 8
    top_irq = 38

    # CC65 generates basic header, no macro needed just to define the CODE segment
    with segment(0x0801, assembler.get_code_segment()) as s:

        sei()

        lda(imm(0x35))                                      # Bank out kernal and basic 00110 101
        sta(at(0x01))                                       # $e000-$ffff

        label("start")
        lda(imm(0))
        for i in range(nb_sprites):
            sta(at(vic.sprite0_x+(2*i)))
            sta(at(vic.sprite0_y+(2*i)))

        # set up irq to replace the kernal IRQ
        m.setup_irq('top_irq', top_irq)
        cli()

    # irq segment
    with segment(0x3000, "IRQ") as s:

        label("top_irq", is_global=True)
        m.double_irq('end', 'irq_stable')

        label("irq_stable")
        y_scroll = top_irq + 2                          # stable raster takes 2 rasterlines

        txs()                                           # we're now at cycle 25 (+/- jitter) after txs
        m.waste_cycles(58)                              # we're now at cycle 8 of the first picture rasterline

        for y in range(y_scroll, y_scroll+10):
            with rasterline(nb_sprites=8, y_pos=y, y_scroll=y_scroll):
                if (y & 7) == y_scroll:
                    nop()
                    nop()
                    nop()
                else:
                    nop()

        m.irq_end('top_irq', top_irq, True, False)
        label('end')


    # generate listing
    gen_code(assembler, format_code=prefs, gen_listing=True)

    # finally assemble segments to PRG using cross assembler then crunch it!
    assemble_prg(assembler, start_address=0x0801)

if __name__ == "__main__":
    generate(code, program_name)

