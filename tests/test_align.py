# if shazzam not installed
import sys
sys.path.append(".")

from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a

import logging
logger = logging.getLogger("shazzam")
logger.setLevel(logging.DEBUG)

def test_align():

    with segment(0x0, "test_align") as s:

        ldy(imm(100))
        label("loop")
        ldx(at(0x01))
        adc(at(0x00))
        sta(at(0x01))
        stx(at(0x00))
        dey()
        bne(rel_at("loop"))

        align(0x40)
        assert s.get_stats().current_address == 0x40

        for i in range(0xC0):
            nop()

        assert s.get_stats().current_address == 0x100
        align(0x100)
        assert s.get_stats().current_address == 0x100





