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
assembler = CC65("cc65", "third_party/cc65/bin/cl65")
program_name = os.path.splitext(os.path.basename(__file__))[0]

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

        cpu, mmu, cc = s.emulate()
        print(f"Address: {get_current_address():04X}")
        print(f"Result: {mmu.read(get_current_address()-1)*256 + mmu.read(get_current_address()-2)}")
        print(f"Cycles used: {cc}")

    # generate listing
    gen_code(assembler, gen_listing=True)

    # finally assemble segments to PRG using cross assembler then crunch it!
    assemble_prg(assembler, start_address=0x0801)

if __name__ == "__main__":
    generate(code, program_name)