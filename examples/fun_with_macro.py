# if shazzam not installed
import sys
sys.path.append(".")

from reloading import reloading
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a
import shazzam.macros.math as m
from shazzam.macros.aliases import color, vic
from shazzam.drivers.assemblers.CC65 import CC65

# define your cross assembler
assembler = CC65("cc65", "/home/shazz/projects/c64/bin/cl65")
prefs = assembler.get_code_format()
set_prefs(default_code_segment=assembler.get_code_segment(),
          code_format=prefs.code,
          comments_format=prefs.comments,
          directive_prefix=prefs.directive)

@reloading
def code():

    # define here or anywhere, doesn't matter, your variables


    # CC65 generates basic header, no macro needed just to define the CODE segment
    with segment(0x0801, assembler.get_code_segment(), fixed_address=True) as s:
        m.add16("var1", "var2", "result")
        brk()

        label("var1")
        byte(0)
        byte(1)
        nop()
        label("var2")
        byte(10)
        byte(0)
        nop()
        label("result")
        byte(0)
        byte(0)

        cpu, mmu = s.emulate()
        print(f"Address: {get_current_address():04X}")
        print(f"Result: {mmu.read(get_current_address()-1)*256 + mmu.read(get_current_address()-2)}")


    # generate listing
    gen_code(format_code=prefs, gen_listing=True)

    # finally assemble segments to PRG using cross assembler then crunch it!
    assemble_prg(assembler, start_address=0x0801)

    # optimize segments
    optimize_segments()

if __name__ == "__main__":
    generate(code, "fun_with_macro")
