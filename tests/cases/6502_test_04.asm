# 6502 Test #04
# Heather Justice 3/12/08
# Tests instructions JMP (both addressing modes) & JSR & RTS.
# Assumes that loads & stores & ORA work with all addressing modes.
# NOTE: Depends on addresses of instructions... Specifically, the "final"
#   address is actually hard-coded at address(abs_adr=0020 (first 4 lines of code).
#   Additionally, a JMP and JSR specify specific addresses.
#
# EXPECTED RESULTS:(abs_adr=40=0x42
#
test: LDA(imm=0x24)
a9
24
test: STA(abs_adr=0x20)
85
20
test: LDA(imm=0xf0)
a9
f0
test: STA(abs_adr=0x21)
85
21
test: LDA(imm=0x00)
a9
00
test: ORA(imm=0x03)
09
03
test: JMP(abs_adr=0xf011)
4c
11
f0
test: ORA(imm=0xFF)
09
ff
test: ORA(imm=0x30)
09
30
test: JSR(abs_adr=0xf01d)
20
1d
f0
test: ORA(imm=0x42)
09
42
test: JMP(ind_adr=0x0020)
6c
20
00
test: ORA(imm=0xFF)
09
ff
test: STA(abs_adr=0x30)
85
30
test: LDX(abs_adr=0x30)
a6
30
test: LDA(imm=0x00)
a9
00
test: RTS()
60
test: STA(abs_adr=0x0d, index=r.X)
95
0d