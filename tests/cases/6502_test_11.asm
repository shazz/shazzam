# 6502 Test #11
# Heather Justice 3/26/08
# Tests stack instructions (PHA & PLA & PHP & PLP).
# Assumes that loads & stores (all addressing modes).
# Also assumes ADC (all addressing modes) and all flag instructions work.
#
test: LDA(imm(0x27))
a9
27
test: ADC(imm(0x01))
69
01
test: SEC()
38
test: PHP()
08
test: CLC()
18
test: PLP()
28
test: ADC(imm(0x00))
69
00
test: PHA()
48
test: LDA(imm(0x00))
a9
00
test: PLA()
68
test: STA(at(0x30))
85
30