# 6502 Test #13
# Heather Justice 4/10/08
# Tests SEI & CLI & SED & CLD.
# Assumes prior tests pass...
#
# EXPECTED RESULT: $21 = 0x0C
#
test: SEI()
78
test: SED()
f8
test: PHP()
08
test: PLA()
68
test: STA(abs_adr=0x20)
85
20
test: CLI()
58
test: CLD()
d8
test: PHP()
08
test: PLA()
68
test: ADC(abs_adr=0x20)
65
20
test: STA(abs_adr=0x21)
85
21