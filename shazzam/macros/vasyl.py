import math
import logging
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a
from shazzam.macros.aliases import color, vic

logger = logging.getLogger("shazzam")

# Beam Racer * https://beamracer.net
# Video and Display List coprocessor board for the Commodore 64
# Copyright (C)2019-2020 Mad Hackers Lab
#
# https://github.com/madhackerslab/
#
# Header file for BeamRacer VASYL chip
# See https://docs.beamracer.net/ for more information.
#
# Compatible with ca65 assembler (part of https://github.com/cc65).

# Macros for assembling VASYL opcodes.

# Registers (0xd031-0xd03f, read-write)
VIC_BASE            = 0xd000

VREG_BASE            = 0xd030
VREG_INT             = 0x40
VREG_MAX             = 0x4f
VREG_CONTROL         = VREG_BASE + 0x01
VREG_DLIST           = VREG_BASE + 0x02
VREG_DLISTL          = VREG_BASE + 0x02
VREG_DLISTH          = VREG_BASE + 0x03
VREG_ADR0            = VREG_BASE + 0x04
VREG_STEP0           = VREG_BASE + 0x06
VREG_PORT0           = VREG_BASE + 0x07
VREG_ADR1            = VREG_BASE + 0x08
VREG_STEP1           = VREG_BASE + 0x0a
VREG_PORT1           = VREG_BASE + 0x0b
VREG_REP0            = VREG_BASE + 0x0c
VREG_REP1            = VREG_BASE + 0x0d
VREG_DLSTROBE        = VREG_BASE + 0x0e
VREG_RESERVED        = VREG_BASE + 0x0f

# Internal registers (0xd040-0xd04f, write-only, not system-bus accessible)
VREG_PBS_CONTROL     = VREG_BASE + 0x10
VREG_DLIST2          = VREG_BASE + 0x11
VREG_DLIST2L         = VREG_BASE + 0x11
VREG_DLIST2H         = VREG_BASE + 0x12
VREG_DL2STROBE       = VREG_BASE + 0x13
VREG_PBS_BASEL       = VREG_BASE + 0x14
VREG_PBS_BASEH       = VREG_BASE + 0x15
VREG_PBS_CYCLE_START = VREG_BASE + 0x16
VREG_PBS_CYCLE_STOP  = VREG_BASE + 0x17
VREG_PBS_STEPL       = VREG_BASE + 0x18
VREG_PBS_STEPH       = VREG_BASE + 0x19
VREG_PBS_PADDINGL    = VREG_BASE + 0x1a
VREG_PBS_PADDINGH    = VREG_BASE + 0x1b
VREG_PBS_XORBYTE     = VREG_BASE + 0x1c
VREG_PBS_RESERVED0   = VREG_BASE + 0x1d
VREG_PBS_RESERVED1   = VREG_BASE + 0x1e
VREG_PBS_RESERVED2   = VREG_BASE + 0x1f


# Opcode masks and values.
#
# *_MASK has "one" bits in locations which must be matching with
# corresponding *_VALUE bits to recognize given instruction. For instance:
#    lda #opcode
#    and #VASYL_BADLINE_MASK
#    cmp #VASYL_BADLINE_VALUE
#    beq opcode_is_badline_instruction

VASYL_BADLINE_MASK    = 0b11111000
VASYL_BADLINE_VALUE   = 0b10101000
VASYL_BRA_MASK        = 0b11111111
VASYL_BRA_VALUE       = 0b10100011
VASYL_DECAB_MASK      = 0b11111110
VASYL_DECAB_VALUE     = 0b10100000
VASYL_DELAYH_MASK     = 0b11111000 # also includes the mask for MASKH
VASYL_DELAYH_VALUE    = 0b10110000
VASYL_DELAYV_MASK     = 0b11111000 # also includes the mask for MASKV
VASYL_DELAYV_VALUE    = 0b10111000
VASYL_IRQ_MASK        = 0b11111111
VASYL_IRQ_VALUE       = 0b10100010
VASYL_MASKH_MASK      = 0b11111110
VASYL_MASKH_VALUE     = 0b10110100
VASYL_MASKPH_MASK     = 0b11111110
VASYL_MASKPH_VALUE    = 0b10110110
VASYL_MASKPV_MASK     = 0b11111110
VASYL_MASKPV_VALUE    = 0b10111110
VASYL_MASKV_MASK      = 0b11111110
VASYL_MASKV_VALUE     = 0b10111100
VASYL_MOVI_MASK       = 0b11100000
VASYL_MOVI_VALUE      = 0b10000000
VASYL_MOV_MASK        = 0b11000000
VASYL_MOV_VALUE       = 0b11000000
VASYL_VNOP_MASK       = 0b11111111
VASYL_VNOP_VALUE      = 0b10100111
VASYL_SETAB_MASK      = 0b11111110
VASYL_SETAB_VALUE     = 0b10110010
VASYL_SKIP_MASK       = 0b11111111
VASYL_SKIP_VALUE      = 0b10100110
VASYL_WAITBAD_MASK    = 0b11111111
VASYL_WAITBAD_VALUE   = 0b10100100
VASYL_WAITREP_MASK    = 0b11111110
VASYL_WAITREP_VALUE   = 0b10111010
VASYL_WAIT_MASK       = 0b10000000
VASYL_WAIT_VALUE      = 0b00000000
VASYL_XFER_MASK       = 0b11111111
VASYL_XFER_VALUE      = 0b10100101


# Constants
MEMBANK_COUNT = 8

CONTROL_RAMBANK_BIT             = 0 # bits 0-2
CONTROL_DLIST_ON_BIT            = 3
CONTROL_RAMBANK_MASK            = (0b111 << CONTROL_RAMBANK_BIT)
CONTROL_PORT_READ_ENABLE_BIT    = 4
CONTROL_GRAYDOT_KILL_BIT        = 5
CONTROL_PORT_MODE_BIT           = 6
CONTROL_PORT_MODE_COPY          = (0b01 << CONTROL_PORT_MODE_BIT)
CONTROL_PORT_MODE_MASK          = (0b11 << CONTROL_PORT_MODE_BIT)

PBS_CONTROL_ACTIVE_BIT          = 3
PBS_CONTROL_RAMBANK_BIT         = 0 # bits 0-2
PBS_CONTROL_RAMBANK_MASK        = (0b111 << PBS_CONTROL_RAMBANK_BIT)
PBS_CONTROL_UPDATE_BIT          = 4 # bits 4-5
PBS_CONTROL_UPDATE_MASK         = (0b11 << PBS_CONTROL_UPDATE_BIT)
PBS_CONTROL_UPDATE_NONE         = (0b00 << PBS_CONTROL_UPDATE_BIT)
PBS_CONTROL_UPDATE_EOL          = (0b01 << PBS_CONTROL_UPDATE_BIT)
PBS_CONTROL_UPDATE_ALWAYS       = (0b10 << PBS_CONTROL_UPDATE_BIT)
PBS_CONTROL_SWIZZLE_BIT         = 6 # bits 6-7
PBS_CONTROL_SWIZZLE_MASK        = (0b11 << PBS_CONTROL_SWIZZLE_BIT)
PBS_CONTROL_SWIZZLE_NONE        = (0b00 << PBS_CONTROL_SWIZZLE_BIT)
PBS_CONTROL_SWIZZLE_MIRROR      = (0b01 << PBS_CONTROL_SWIZZLE_BIT)
PBS_CONTROL_SWIZZLE_MULTIMIRROR = (0b10 << PBS_CONTROL_SWIZZLE_BIT)

def WAIT(v, h):
    word(((v) & 0x01ff) | (((h) & 0x3f) << 9))

def DELAYH(v, h=None):
    if h is None:  # this means only one arg was given so "v" actually the horizontal delay
        byte([0b10110000, ((v) & 0x3f)])
    else:
        byte([0b10110000, (((v) & 0x03) << 6) | ((h) & 0x3f)])

def DELAYV(v):
    word((0b10111000 << 8) | ((v) & 0x01ff))

def MASKH(h):
    byte(0b10110100, ((h) & 0x3f))

def MASKV(v):
    word((0b10111100 << 8) |  ((v) & 0x01ff))

def MASKPH(h):
    byte(0b10110110, ((h) & 0x3f))

def MASKPV(v):
    word((0b10111110 << 8)|  ((v) & 0x01ff))

def SETA(v):
    byte(0b10110010, ((v) & 0xff))

def SETB(v):
    byte(0b10110011, ((v) & 0xff))

def DECA():
    byte(0b10100000)

def DECB():
    byte(0b10100001)

def MOV(reg, value):
    if ((reg) & 0xff) < VREG_MAX and (((reg & 0xff00) == VIC_BASE) or ((reg & 0xff00) == 0x0) ):
        if ((reg) & 0xff) < VREG_INT:
            byte([0xc0 | ((reg) & 0x3f), ((value) & 0xff)])
        else:
            byte([0x80 | (((reg) - VREG_INT) & 0x0f), ((value) & 0xff)])
    else:
        raise ValueError(f"MOV: register out of range: {reg:02X}")

def SKIP():
    byte(0b10100110)

def IRQ():
    byte(0b10100010)

def VNOP():
    byte(0b10100111)

def WAITBAD():
    byte(0b10100100)

def BADLINE(l):
    byte(0b10101000 | ((l) & 0x07))

def XFER(reg, c):
    if ((reg) & 0xff) <= VREG_MAX and ((((reg) & 0xff00) == VIC_BASE) or (((reg) & 0xff00) == 0x0)):
        byte(0b10100101, (((c) & 1) << 7) | ((reg) & 0xff))
    else:
        raise ValueError(f"XFER: register out of range: {reg:04X}")

def BRA(target):
    if target.value is not None:
        if get_current_address() > target.value:
            rel_adr = -(get_current_address() + 2 - target.value)
        else:
            rel_adr = target.value - (get_current_address() + 2)

        if rel_adr >= -128 & rel_adr <= 127:
            byte([0b10100011, (rel_adr & 0xff)])
        else:
            raise ValueError(f"BRA: target out of range: {rel_adr} bytes away")
    else:
        raise NotImplementedError()

        #TODO: Fix this part
    #     ifndef target
    #         byte(0b10100011, ((target) - (* + 1)) & 0xff)
    #         logger.warning("Forward BRA assembled without bounds checking.")
    #     else:
    #         if ((target) -(* + 1)) >= -128 & ((target) -(* + 1)) <= 127:
    #             byte(0b10100011, ((target) - (* + 1)) & 0xff)
    #         else:
    #             raise ValueError(f"BRA: target out of range: {target} is {(target) -(* + 1)} bytes away")

def END():
    WAIT(0x1ff, 0x3f)


