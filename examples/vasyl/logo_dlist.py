from shazzam.py64gen import *
from shazzam.macros.vasyl import *
from shazzam.Assembler import Assembler

# BeamRacer * https://beamracer.net
# Video and Display List coprocessor board for the Commodore 64
# Copyright (C)2019-2020 Mad Hackers Lab
#
# https://github.com/madhackerslab/beamracer-examples
#
# Logo display list

with segment(0x0900, "VASYL", relocated_offset=0x0000) as s:

    label("dl_start", is_global=True)
    WAIT(48 ,0)

    dl_line_0 = label("dl_line_0")
    MASKV(0)
    WAIT(0, 15)
    MOV(0x20, 0)
    DELAYV(1)
    SKIP()
    WAIT(55 , 59)
    BRA(dl_line_0)
    WAIT(56 ,0)

    dl_line_1 = label("dl_line_1")
    MASKV(0)
    WAIT(0, 15)
    MOV(0x20, 14)
    DELAYH(5)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(6)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYH(1)
    MOV(0x20, 14)
    DELAYH(4)
    MOV(0x20, 6)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYV(1)
    SKIP()
    WAIT(63 , 59)
    BRA(dl_line_1)
#   WAIT(64 ,0)

    dl_line_2 = label("dl_line_2")
    MASKV(0)
    WAIT(0, 15)
    MOV(0x20, 0)
    DELAYH(4)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYH(8)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYH(3)
    MOV(0x20, 14)
    DELAYH(6)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYV(1)
    SKIP()
    WAIT(71 , 59)
    BRA(dl_line_2)
#   WAIT(72 ,0)

    dl_line_3 = label("dl_line_3")
    MASKV(0)
    WAIT(0, 15)
    MOV(0x20, 14)
    DELAYH(5)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(5)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 14)
    DELAYH(6)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYV(1)
    SKIP()
    WAIT(79 , 59)
    BRA(dl_line_3)
#   WAIT(80 ,0)

    dl_line_4 = label("dl_line_4")
    MASKV(0)
    WAIT(0, 15)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYH(3)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYV(1)
    SKIP()
    WAIT(87 , 59)
    BRA(dl_line_4)
#   WAIT(88 ,0)

    dl_line_5 = label("dl_line_5")
    MASKV(0)
    WAIT(0, 15)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYH(3)
    MOV(0x20, 14)
    DELAYH(6)
    MOV(0x20, 6)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYV(1)
    SKIP()
    WAIT(95 , 59)
    BRA(dl_line_5)
#   WAIT(96 ,0)

    dl_line_6 = label("dl_line_6")
    MASKV(0)
    WAIT(0, 15)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYH(3)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYV(1)
    SKIP()
    WAIT(103 , 59)
    BRA(dl_line_6)
    WAIT(104 ,0)

    dl_line_7 = label("dl_line_7")
    MASKV(0)
    WAIT(0, 15)
    MOV(0x20, 14)
    DELAYH(5)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(6)
    MOV(0x20, 6)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYV(1)
    SKIP()
    WAIT(111 , 59)
    BRA(dl_line_7)
    WAIT(112 ,0)

    dl_line_8 = label("dl_line_8")
    MASKV(0)
    WAIT(0, 15)
    MOV(0x20, 0)
    DELAYV(1)
    SKIP()
    WAIT(119 , 59)
    BRA(dl_line_8)
    WAIT(120 ,0)

    dl_line_9 = label("dl_line_9")
    MASKV(0)
    WAIT(0, 15)
    MOV(0x20, 0)
    DELAYH(37)
    MOV(0x20, 7)
    MOV(0x20, 0)
    DELAYV(1)
    SKIP()
    WAIT(127 , 59)
    BRA(dl_line_9)
    WAIT(128 ,0)

    dl_line_10 = label("dl_line_10")
    MASKV(0)
    WAIT(0, 15)
    MOV(0x20, 7)
    DELAYH(37)
    MOV(0x20, 1)
    MOV(0x20, 7)
    MOV(0x20, 0)
    DELAYV(1)
    SKIP()
    WAIT(135 , 59)
    BRA(dl_line_10)
    WAIT(136 ,0)

    dl_line_11 = label("dl_line_11")
    MASKV(0)
    WAIT(0, 15)
    MOV(0x20, 4)
    DELAYH(37)
    MOV(0x20, 1)
    MOV(0x20, 0)
    DELAYV(1)
    SKIP()
    WAIT(143 , 59)
    BRA(dl_line_11)
    WAIT(144 ,0)

    dl_line_12 = label("dl_line_12")
    MASKV(0)
    WAIT(0, 15)
    MOV(0x20, 0)
    DELAYH(37)
    MOV(0x20, 7)
    MOV(0x20, 0)
    DELAYV(1)
    SKIP()
    WAIT(151 , 59)
    BRA(dl_line_12)
#   WAIT(152 ,0)
#dl_line_13")
#   MASKV(0)
#   WAIT(0, 15)
#   MOV(0x20, 0)
#   DELAYV(1)
#   SKIP()
#   WAIT(159 , 59)
#   MOV VREG_DL2STROBE, 0)
    WAIT(160 ,0)

    dl_line_14 = label("dl_line_14")
    MASKV(0)
    WAIT(0, 15)
    MOV(0x20, 14)
    DELAYH(5)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYH(3)
    MOV(0x20, 14)
    DELAYH(4)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(4)
    MOV(0x20, 6)
    MOV(0x20, 14)
    DELAYH(6)
    MOV(0x20, 6)
    MOV(0x20, 14)
    DELAYH(5)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYV(1)
    SKIP()
    WAIT(167 , 59)
    BRA(dl_line_14)
    WAIT(168 ,0)

    dl_line_15 = label("dl_line_15")
    MASKV(0)
    WAIT(0, 15)
    MOV(0x20, 0)
    DELAYH(4)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYH(1)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYH(23)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYV(1)
    SKIP()
    WAIT(175 , 59)
    BRA(dl_line_15)
    WAIT(176 ,0)

    dl_line_16 = label("dl_line_16")
    MASKV(0)
    WAIT(0, 15)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYH(2)
    MOV(0x20, 14)
    DELAYH(5)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYV(1)
    SKIP()
    WAIT(183 , 59)
    BRA(dl_line_16)
    WAIT(184 ,0)

    dl_line_17 = label("dl_line_17")
    MASKV(0)
    WAIT(0, 15)
    MOV(0x20, 14)
    DELAYH(5)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYH(1)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYH(2)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYH(3)
    MOV(0x20, 14)
    DELAYH(5)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYV(1)
    SKIP()
    WAIT(191 , 59)
    BRA(dl_line_17)
    WAIT(192 ,0)

    dl_line_18 = label("dl_line_18")
    MASKV(0)
    WAIT(0, 15)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYH(1)
    MOV(0x20, 14)
    DELAYH(6)
    MOV(0x20, 6)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYH(2)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYH(3)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYV(1)
    SKIP()
    WAIT(199 , 59)
    BRA(dl_line_18)
    WAIT(200 ,0)

    dl_line_19 = label("dl_line_19")
    MASKV(0)
    WAIT(0, 15)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 14)
    DELAYH(5)
    MOV(0x20, 6)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYH(3)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 0)
    DELAYH(1)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYV(1)
    SKIP()
    WAIT(207 , 59)
    BRA(dl_line_19)
    WAIT(208 ,0)

    dl_line_20 = label("dl_line_20")
    MASKV(0)
    WAIT(0, 15)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYH(1)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(4)
    MOV(0x20, 6)
    MOV(0x20, 14)
    DELAYH(6)
    MOV(0x20, 0)
    MOV(0x20, 14)
    DELAYH(2)
    MOV(0x20, 0)
    DELAYH(2)
    MOV(0x20, 14)
    DELAYH(1)
    MOV(0x20, 6)
    MOV(0x20, 0)
    DELAYV(1)
    SKIP()
    WAIT(215 , 59)
    BRA(dl_line_20)

    dl_line_21 = label("dl_line_21")
    WAIT(224 ,0)

    dl_line_22 = label("dl_line_22")
    MASKV(0)
    WAIT(0, 15)
    MOV(0x20, 0)
    DELAYH(27)
    MOV(0x20, 2)
    DELAYH(1)
    MOV(0x20, 0)
    DELAYH(2)
    MOV(0x20, 2)
    DELAYH(2)
    MOV(0x20, 0)
    DELAYV(1)
    SKIP()
    WAIT(231 , 59)
    BRA(dl_line_22)
    WAIT(232 ,0)

    dl_line_23 = label("dl_line_23")
    MASKV(0)
    WAIT(0, 15)
    MOV(0x20, 0)
    DELAYH(28)
    MOV(0x20, 2)
    MOV(0x20, 0)
    DELAYH(2)
    MOV(0x20, 2)
    MOV(0x20, 0)
    MOV(0x20, 2)
    MOV(0x20, 0)
    DELAYV(1)
    SKIP()
    WAIT(239 , 59)
    BRA(dl_line_23)
    WAIT(240 ,0)

    dl_line_24 = label("dl_line_24")
    MASKV(0)
    WAIT(0, 15)
    MOV(0x20, 0)
    DELAYH(28)
    MOV(0x20, 2)
    MOV(0x20, 0)
    MOV(0x20, 2)
    MOV(0x20, 0)
    MOV(0x20, 2)
    DELAYH(2)
    MOV(0x20, 0)
    DELAYV(1)
    SKIP()
    WAIT(247 , 59)
    BRA(dl_line_24)
    END()

