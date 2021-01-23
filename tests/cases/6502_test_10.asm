# 6502 Test #10
# Heather Justice 3/26/08
# Tests flag instructions (CLC & SEC & CLV & CLD & SED) & NOP.
# Assumes that loads & stores (all addressing modes) and all branches work.
# Also assumes ADC works with all addressing modes.
#
# EXPECTED RESULTS:(abs_adr=0x30 = 0xCE
#
test: LDA(imm=0x99)
a9
99
test: ADC(imm=0x87)
69
87
test: CLC()
18
test: NOP()
ea
test: BCC(rel_adr=0x04)
90
04
test: ADC(imm=0x60)
69
60
test: ADC(imm=0x93)
69
93
test: SEC()
38
test: NOP()
ea
test: BCC(rel_adr=0x01)
90
01
test: CLV()
b8
test: BVC(rel_adr=0x02)
50
02
test: LDA(imm=0x00)
a9
00
test: ADC(imm=0xAD)
69
ad
test: NOP()
ea
test: STA(abs_adr=0x30)
85
30