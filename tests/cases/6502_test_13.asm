# 6502 Test #13
# Heather Justice 4/10/08
# Tests SEI & CLI & SED & CLD.
# Assumes prior tests pass...
#
test: SEI()
78
test: SED()
f8
test: PHP()
08
test: PLA()
68
test: STA(at(0x20))
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
test: ADC(at(0x20))
65
20
test: STA(at(0x21))
85
21