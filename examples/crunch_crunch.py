# if shazzam not installed
import sys
sys.path.append(".")

from reloading import reloading
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a

from shazzam.macros.aliases import color, vic
import shazzam.plugins.plugins as p
from shazzam.drivers.assemblers.CC65 import CC65
from shazzam.drivers.crunchers.Exomizer import Exomizer
from shazzam.drivers.crunchers.Nucrunch import Nucrunch
from shazzam.drivers.crunchers.Pucrunch import Pucrunch
from shazzam.drivers.crunchers.Apultra import Apultra
from shazzam.drivers.crunchers.Doynamite import Doynamite
from shazzam.drivers.crunchers.Lzsa import Lzsa

# define your cross assembler
assembler = CC65("cc65", "/home/shazz/projects/c64/bin/cl65")
prefs = assembler.get_code_format()
set_prefs(default_code_segment=assembler.get_code_segment(),
          code_format=prefs.code,
          comments_format=prefs.comments,
          directive_prefix=prefs.directive)

prg_cruncher  = Exomizer("/home/shazz/projects/c64/bin/exomizer")
prg_cruncher  = Nucrunch("/home/shazz/projects/c64/bin/nucrunch")
prg_cruncher  = Pucrunch("/home/shazz/projects/c64/bin/pucrunch")
data_cruncher = Apultra("/home/shazz/projects/c64/bin/apultra")

@reloading
def code():

    # define here or anywhere, doesn't matter, your variables
    sidfile = "resources/Meetro.sid"

    # CC65 generates basic header, no macro needed just to define the CODE segment
    with segment(0x0801, assembler.get_code_segment()) as s:
        nop()
        nop()
        print(f"{s.get_stats()}")

    with segment(0x1000, "packedata") as s:
        incbin(data_cruncher.crunch_incbin(sidfile))
        print(s.get_stats())

    with segment(0x1900, "depacker") as s:
        data_cruncher.generate_depacker_routine(s.get_stats().start_address)

    # generate listing and code
    gen_code(prefs=prefs)
    gen_listing()

    # finally assemble segments to PRG using cross assembler then crunch it!
    assemble_prg(assembler, start_address=0x0801, cruncher=prg_cruncher)

if __name__ == "__main__":
    generate(code, "crunchcrunch")



