# 6502 Test #12
# Heather Justice 4/10/08
# Tests RTI instruction.
# Assumes lots of other instructions work already...
#
# EXPECTED RESULTS: $33 = 0x42
#
test: CLC()
18
test: LDA(imm=0x42)
a9
42
test: STA(abs_adr=0x33)
85
33
test: LDA(imm=0xF0)
a9
f0
test: PHA()
48
test: LDA(imm=0x01)
a9
01
test: PHA()
48
test: SEC()
38
test: PHP()
08
test: CLC()
18
test: RTI()
40