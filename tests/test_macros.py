import sys
sys.path.append(".")

from shazzam.py64gen import *
import shazzam.macros.macros as m

def test_add16():

    with segment(0x0, "add16") as s:

        m.add16("res", "n1", "n2")

        label(name="n1")
        byte(value=0)
        byte(value=10)

        label(name="n2")
        byte(value=0)
        byte(value=10)

        label(name="res")
        byte(value=0)
        byte(value=0)

        cpu, mem = s.emulate()
        current = s.get_stats()['current_address']
        assert mem.read(current-2) == 0, f"res[hi] should be 0"
        assert mem.read(current-1) == 20, f"res[hi] should be 0"
