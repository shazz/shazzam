import math
import logging
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a
from shazzam.macros.aliases import color, vic

logger = logging.getLogger("shazzam")

# ------------------------------------------------------------------------
# waste_cycles(n)
# setup stable raster irq note: cannot be set on a badline or the second
# interrupt happens before we store the stack pointer (among other things)
# ------------------------------------------------------------------------
def waste_cycles(n):
    nops = math.floor(n/2)
    rem = n & 1
    c = n
    if rem == 0:
        for i in range(nops):
            nop()
            c = c - 2
    else:
        for i in range(nops-1):
            nop()
            c = c - 2
        bit(at(0xfe))
        c = c - 3
    if c != 0:
        logger.error(f"error {c} cycles remaining on {n}")
        raise RuntimeError("should not be here")


# ------------------------------------------------------------------------------------------
# basic start
# generate a compatible basic header
# ------------------------------------------------------------------------------------------
def basic_start(addr):
    with segment(0x0801, "entry") as s:
        byte(0x0c)
        byte(0x08)
        byte(0x00)
        byte(0x00)
        byte(0x9e)

        if (addr >= 10000):
            byte(0x30 + (addr//10000)%10)

        if (addr >= 1000):
            byte(0x30 + (addr//1000)%10)

        if (addr >= 100):
            byte(0x30 + (addr//100)%10)

        if (addr >= 10):
            byte(0x30 + (addr//10)%10)

        byte(0x30 + addr % 10)
        byte(0x0, 0x0, 0x0)

        logger.info(f"after basic header, program start at {s.get_stats()['current_address']}")

