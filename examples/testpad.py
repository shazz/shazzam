# if shazzam not installed
import sys
sys.path.append(".")

from reloading import reloading
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a
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

        nop()
        sta(at(0x12))
        sta(at(0x12),x)
        sta(at(0x1212))
        sta(at(0x1212),x)
        sta(at(0x1212),y)
        sta(ind_at(0x12),x)
        sta(ind_at(0x12),y)
        nop()
        sta(at("test"))
        sta(at("test"),x)
        sta(at("test"),y)

    with segment(0x0801, assembler.get_data_segment()) as s:
        label("test")
        for i in range(10):
            byte(i)
        nop()
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
