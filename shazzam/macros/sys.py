import math
import logging
from typing import Any
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


# ------------------------------------------------------------------------
# setup_irq(irq_addr, irq_line, ack_raster_int)
# Set raster IRQ
# -----------------------------------------------------------------------
def setup_irq(irq_addr: Any, irq_line: int, ack_raster_int: bool = True):
    lda(imm(0x7f))                  # 0x7f = 0111 1111
    sta(at(0xdc0d))                # enable all interrupts
    sta(at(0xdd0d))                # enable all NMI

    if isinstance(irq_addr, str):
        lda(imm('<' + irq_addr))            # set HW interrupt vector
        ldx(imm('>' + irq_addr))
    else:
        lda(imm(irq_addr & 0xff))            # set HW interrupt vector
        ldx(imm(irq_addr >> 8))

    sta(at(0xfffe))
    stx(at(0xffff))

    lda(imm(0x01))
    sta(at(0xd01a))                # Enable Raster interrupt
    lda(imm(irq_line))
    sta(at(0xd012))                # Set raster interrupt to rasterline `irq_line`
    if irq_line > 255:
        raise ValueError("this macro doesn't support setting the 9th bit of irq line")

    if ack_raster_int:
        lda(at(0xd011))            # load screen control register
        andr(imm(0x7f))              # ack raster interrupt (bit #8)
        sta(at(0xd011))

    asl(at(0xd019))                # Ack all interrupts
    bit(at(0xdc0d))                # Enable all interrupts
    bit(at(0xdd0d))                # Enable all NMI

#------------------------------------------------------------------------
# end_irq(next_irq_addr, next_irq_line, irq_line_hi)
# Ack, end current raster IRQ and set new raster IRQ
#------------------------------------------------------------------------
def end_irq(next_irq_addr, next_irq_line, ack_raster_irq, irq_line_hi, fixed_line):

    clear = get_anonymous_label("clear")
    end = get_anonymous_label("end")

    asl(at(0xd019))                                # Ack all interrupts

    if isinstance(next_irq_addr, str):
        lda(imm('<' + next_irq_addr))            # set HW interrupt vector
        ldx(imm('>' + next_irq_addr))
    else:
        lda(at(next_irq_addr & 0xf))                   # Set next IRQ in hardware vector (no kernal)
        ldx(at(next_irq_addr >> 8))

    sta(at(0xfffe))
    stx(at(0xffff))

    # if constant raster line
    if fixed_line:
        lda(imm(next_irq_line & 255))               # Set next raster line interrupt
        sta(at(0xd012))
        if next_irq_line > 255:                     # if irq_line_hi, then
            lda(at(0xd011))
            ora(imm(0x80))                          # 1000 0000
            sta(at(0xd011))                        # force raster line interrupt
        else:
            lda(at(0xd011))
            andr(imm(0x7f))                         # clear raster line interrupt
            sta(at(0xd011))
    # else read memory
    else:
        lda(at(next_irq_line))                     # Set next raster line interrupt
        sta(at(0xd012))
        if irq_line_hi:
            lda(at(next_irq_line+1))
            beq(rel_at(clear))

            lda(at(0xd011))
            ora(imm(0x80))                          # 1000 0000
            sta(at(0xd011))
            jmp(at(end))

            label(clear)
            lda(at(0xd011))
            andr(imm(0x7f))
            sta(at(0xd011))
            label(end)

# ------------------------------------------------------------------------
# irq_start(end_lbl)
# set a,x,y registers
# ------------------------------------------------------------------------
def irq_start(end_lbl):

    sta(at(end_lbl)-6)
    stx(at(end_lbl)-4)
    sty(at(end_lbl)-2)

# ------------------------------------------------------------------------
# irq_end(next, line)
# restore a,x,y registers then RTI (Kernal interrupt vector replacement)
# ------------------------------------------------------------------------
def irq_end(next, line, fixed_line, irq_line_hi):

    end_irq(next, line, False, irq_line_hi, fixed_line)
    # label('skip_next')
    lda(imm(0x00))
    ldx(imm(0x00))
    ldy(imm(0x00))
    rti()

# ------------------------------------------------------------------------
# double_irq(end, stableIRQ)
# setup stable raster
# IRQ NOTE: cannot be set on a badline or the second
# interrupt happens before we store the stack pointer (among other things)
# ------------------------------------------------------------------------
def double_irq(end: Any, stableIRQ: Any):

    # The CPU cycles spent to get in here                                   [7] 7
    irq_start(end)                 # 4+4+4 cycles                          [12] 19

    if isinstance(stableIRQ, str):
        lda(imm('<' + stableIRQ))            # set HW interrupt vector
        ldx(imm('>' + stableIRQ))
    else:
        lda(imm(stableIRQ & 0xff))      # Set IRQ Vector                        [4] 23
        ldx(imm(stableIRQ >> 8))        # to point to the                       [4] 27
                                    # next part of the
    sta(at(0xfffe))                # Stable IRQ                            [4] 31
    stx(at(0xffff))                #                                       [4] 35
    inc(at(0xd012))                # set raster interrupt to the next line [6] 41
    asl(at(0xd019))                # Ack raster interrupt                  [6] 47
    tsx()                           # Store the stack pointer!              [2] 49
    cli()                           #                                       [2] 51
                                    # Total spent cycles up to this point   [51]
    nop()                           #                                       [53]
    nop()                           #                                       [55]
    nop()                           #                                       [57]
    nop()                           #                                       [59]
    nop()                           # Execute nop()'s                       [61]
    nop()                           # until next RASTER                     [63]
    nop()                           # IRQ Triggers

