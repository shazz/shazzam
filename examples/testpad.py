# if shazzam not installed
import sys
sys.path.append(".")

from reloading import reloading
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a
from shazzam.macros.aliases import color, vic
from shazzam.drivers.assemblers.CC65 import CC65
import shazzam.macros.math as m
import shazzam.plugins.plugins as p

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

    import binascii
    kla = p.read_kla('resources/panda.kla')
    print(kla.keys())
    # print(f"address: {binascii.hexlify(kla.address)}")
    print(f"address: {kla.address:04X}")
    print(f"bitmap[0]: {kla.bitmap[0]:02X}")
    print(f"bitmap[0]: {kla.bitmap[1]:02X}")
    print(f"color: {kla.bg_color}")
    exit()

    # CC65 generates basic header, no macro needed just to define the CODE segment
    with segment(0x0801, assembler.get_code_segment()) as s:

        label("test1")
        nop()
        nop()
        nop()
        label("data1")
        for i in range(9):
            byte(i)
        label("data2")
        for i in range(7):
            byte(i)
        label("code")
        nop()
        byte(0)
        label("end_of_data")

        # bcc(rel_at(0x0810))

        # val = 5
        # res = 320
        # m.add8_to_16(val, "res")

        # brk()
        # label("res")
        # byte(res & 0xff)
        # byte(res >> 8)

        # cpu, mmu = s.emulate()
        # print(f"Address: {get_current_address():04X}")

        # result = ((mmu.read(get_current_address()-1)*256) + mmu.read(get_current_address()-2))
        # assert result  == 325, f"{result} vs {val+res}"
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

    # with segment(0x0812, assembler.get_data_segment()) as s:
    #     label("test", is_global=True)
    #     for i in range(10):
    #         byte(i)
    #     nop()   # else label won't be seen... to fixed
    #     label("test2")
    #     for i in range(3):
    #         byte(i)


    # generate listing
    gen_code(assembler, format_code=prefs, gen_listing=True)

    # finally assemble segments to PRG using cross assembler then crunch it!
    assemble_prg(assembler, start_address=0x0801)

if __name__ == "__main__":
    generate(code, program_name)
