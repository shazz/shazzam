import sys
sys.path.append(".")

from shazzam.py64gen import *
import shazzam.macros.macros as m

def test_add16():

        for n1 in range(512):
            for n2 in range(250, 260):

                with segment(0x0, "add16", check_address_dups=False) as s:
                    m.add16("n1", "n2", "res")
                    brk()

                    label(name="n1")
                    byte(n1 & 0xff)
                    byte(n1 >> 8)

                    label(name="n2")
                    byte(n2 & 0xff)
                    byte(n2 >> 8)

                    label(name="res")
                    byte(0)
                    byte(0)
                    cpu, mmu = s.emulate()
                    assert ((mmu.read(get_current_address()-1)*256) + mmu.read(get_current_address()-2)) == n1+n2, f"Sum should be {n1+n2}"

