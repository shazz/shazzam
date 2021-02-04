# if shazzam not installed
import sys
sys.path.append(".")

from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a

import logging
logger = logging.getLogger("shazzam")
logger.setLevel(logging.DEBUG)

# run with pytest -s to capture inputs
def test_input():

    with segment(0x0, "test_input") as s:

        label("loop")
        ldx(at(0x01))
        adc(at(0x00))
        sta(at(0x01))
        stx(at(0x00))
        dey()
        bne(rel_at("loop"))

        brk()

        cpu, mmu, cycles_used = s.emulate(debug_mode=True)

