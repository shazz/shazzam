# if shazzam not installed
import sys
sys.path.append(".")

from reloading import reloading
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a
from shazzam.macros.aliases import color, vic
from shazzam.drivers.assemblers.CC65 import CC65
import shazzam.macros.macros as m

# define your cross assembler
assembler = CC65("cc65", "/home/shazz/projects/c64/bin/cl65")
prefs = assembler.get_code_format()
set_prefs(code_format=prefs.code, comments_format=prefs.comments, directive_prefix=prefs.directive)

@reloading
def code():

    # define here or anywhere, doesn't matter, your variables


    # CC65 generates basic header, no macro needed just to define the CODE segment
    with segment(0x0801, assembler.get_code_segment()) as s:
        lda(at("test"))

        m.add8_to_16(5, 320)

        brk()
        label("res")
        byte(0)
        byte(0)


        # cpu, mmu = s.emulate()
        # print(f"Address: {get_current_address():04X}")
        # assert ((mmu.read(get_current_address()-1)*256) + mmu.read(get_current_address()-2)) == 325
        # print(s.get_stats())

        # nop()
        # sta(at(0x12))
        # sta(at(0x12),x)
        # sta(at(0x1212))
        # sta(at(0x1212),x)
        # sta(at(0x1212),y)
        # sta(ind_at(0x12),x)
        # sta(ind_at(0x12),y)

        # nop()
        # sta(at("test"))
        # sta(at("test"),x)
        # sta(at("test"),y)

    with segment(0x0900, assembler.get_data_segment()) as s:
        label("test", is_global=True)
        for i in range(10):
            byte(i)
        nop()   # else label won't be seen... to fixed
        label("test2")
        for i in range(3):
            byte(i)


    # generate listing
    gen_code("testpad", prefs=prefs)
    gen_listing("testpad")

    # finally assemble segments to PRG using cross assembler then crunch it!
    assemble_prg(assembler, start_address=0x0801)

if __name__ == "__main__":
    generate(code)
