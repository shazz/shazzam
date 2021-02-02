# if shazzam not installed
import sys
sys.path.append(".")

from reloading import reloading
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a

from shazzam.macros.aliases import color, vic
import shazzam.plugins.plugins as p
from shazzam.drivers.assemblers.CC65 import CC65
from shazzam.drivers.irqloaders.Sparkle import Sparkle

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

    # CC65 generates basic header, no macro needed just to define the CODE segment
    with segment(0x0801, assembler.get_code_segment()) as s:

        print(f"{s.get_stats()}")

    # generate listing
    gen_code(assembler, format_code=prefs, gen_listing=True)

    # finally assemble segments to PRG using cross assembler then crunch it!
    assemble_prg(assembler, start_address=0x0801)

if __name__ == "__main__":
    generate(code, program_name)



