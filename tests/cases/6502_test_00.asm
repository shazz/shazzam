# 6502 Test #00
# Heather Justice 3/11/08
# Tests instructions LDA/LDX/LDY & STA/STX/STY with all addressing modes.
#
# EXPECTED RESULTS:
#  0x022A = 0x55 (decimal 85)
#  A = 0x55, X = 0x2A, Y = 0x73
#
test: LDA(imm=85)
a9
55
test: LDX(imm=42)
a2
2a
test: LDY(imm=115)
a0
73
test: STA(abs_adr=0x81)
85
81
test: LDA(imm=0x01)
a9
01
test: STA(abs_adr=0x61)
85
61
test: LDA(abs_adr=0x81)
a5
81
test: STA(abs_adr=0x0910)
8d
10
09
test: LDA(abs_adr=0x0910)
ad
10
09
test: STA(abs_adr= 0x56, index=r.X)
95
56
test: LDA(abs_adr= 0x56, index=r.X)
b5
56
test: STY(abs_adr=0x60)
84
60
test: STA(ind_adr=0x60, index=r.Y)
91
60
test: LDA(ind_adr=0x60, index=r.Y)
B1
60
test: STA(abs_adr=0x07ff, index=r.X)
9d
ff
07
test: LDA(abs_adr=0x07ff, index=r.X)
bd
ff
07
test: STA(abs_adr=0x07ff, index=r.Y)
99
ff
07
test: LDA(abs_adr=0x07ff, index=r.Y)
b9
ff
07
test: STA(ind_adr=0x36, index=r.X)
81
36
test: LDA(ind_adr=0x36, index=r.X)
a1
36
test: STX(abs_adr=0x50)
86
50
test: LDX(abs_adr=0x60)
a6
60
test: LDY(abs_adr=0x50)
a4
50
test: STX(abs_adr=0x0913)
8e
13
09
test: LDX(abs_adr=0x0913)
ae
13
09
test: STY(abs_adr=0x0914)
8c
14
09
test: LDY(abs_adr=0x0914)
ac
14
09
test: STY(abs_adr=0x2D, index=r.X)
94
2D
test: STX(abs_adr=0x77, index=r.Y)
96
77
test: LDY(abs_adr=0x2D, index=r.X)
b4
2d
test: LDX(abs_adr=0x77, index=r.Y)
b6
77
test: LDY(abs_adr=0x08A0, index=r.X)
bc
a0
08
test: LDX(abs_adr=0x08A1, index=r.Y)
be
a1
08
test: STA(abs_adr=0x0200, index=r.X)
9d
00
02