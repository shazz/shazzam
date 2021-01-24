# if shazzam not installed
import sys
sys.path.append(".")

from reloading import reloading
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a
import shazzam.macros.macros as m
from shazzam.macros.aliases import color, vic
from shazzam.drivers.assemblers.CC65 import CC65

# define your cross assembler
assembler = CC65("cc65", "/home/shazz/projects/c64/bin/cl65")
prefs = assembler.get_code_format()
set_prefs(code_format=prefs.code, comments_format=prefs.comments, directive_prefix=prefs.directive)

@reloading
def code():

    # define here or anywhere, doesn't matter, your variables


    # CC65 generates basic header, no macro needed just to define the CODE segment
    with segment(0x0801, assembler.get_code_segment()) as s:
        m.add16(get_label("res"), get_label("n1"), get_label("n2"))
        cpu, mmu = s.emulate()
        print(f"Address: {get_current_address():04X}")
        print(mmu.read(get_current_address()+4), mmu.read(get_current_address()+5) )
        # assert mmu.read(get_current_address()-1) + 255*mmu.read(get_current_address()-2) == 20

        ldata = label("n1")
        byte(0)
        byte(10)
        ldata = label("n2")
        byte(0)
        byte(10)
        ldata = label("res")
        byte(0)
        byte(0)




    # generate listing
    gen_code("helloworld")

    # finally assemble segments to PRG using cross assembler then crunch it!
    assemble_prg(assembler, start_address=0x0801)

if __name__ == "__main__":
    generate(code)