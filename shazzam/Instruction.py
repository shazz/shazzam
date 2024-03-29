import hashlib
import logging
from shazzam.Address import Address
from shazzam.Immediate import Immediate


class Instruction():
    """6502 Instruction class"""
    cycle_counts = [
    #   0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F
        7, 6, 2, 8, 3, 3, 5, 5, 3, 2, 2, 2, 4, 4, 6, 6,  # 0
        2, 5, 2, 8, 4, 4, 6, 6, 2, 4, 2, 7, 4, 4, 7, 7,  # 1
        6, 6, 2, 8, 3, 3, 5, 5, 4, 2, 2, 2, 4, 4, 6, 6,  # 2
        2, 5, 2, 8, 4, 4, 6, 6, 2, 4, 2, 7, 4, 4, 7, 7,  # 3
        6, 6, 2, 8, 3, 3, 5, 5, 3, 2, 2, 2, 3, 4, 6, 6,  # 4
        2, 5, 2, 8, 4, 4, 6, 6, 2, 4, 2, 7, 4, 4, 7, 7,  # 5
        6, 6, 2, 8, 3, 3, 5, 5, 4, 2, 2, 2, 5, 4, 6, 6,  # 6
        2, 5, 2, 8, 4, 4, 6, 6, 2, 4, 2, 7, 4, 4, 7, 7,  # 7
        2, 6, 2, 6, 3, 3, 3, 3, 2, 2, 2, 2, 4, 4, 4, 4,  # 8
        2, 6, 2, 6, 4, 4, 4, 4, 2, 5, 2, 5, 5, 5, 5, 5,  # 9
        2, 6, 2, 6, 3, 3, 3, 3, 2, 2, 2, 2, 4, 4, 4, 4,  # A
        2, 5, 2, 5, 4, 4, 4, 4, 2, 4, 2, 4, 4, 4, 4, 4,  # B
        2, 6, 2, 8, 3, 3, 5, 5, 2, 2, 2, 2, 4, 4, 6, 6,  # C
        2, 5, 2, 8, 4, 4, 6, 6, 2, 4, 2, 7, 4, 4, 7, 7,  # D
        2, 6, 2, 8, 3, 3, 5, 5, 2, 2, 2, 2, 4, 4, 6, 6,  # E
        2, 5, 2, 8, 4, 4, 6, 6, 2, 4, 2, 7, 4, 4, 7, 7   # F
    ]

    opcodes = [
        #     0,8           1,9           2,A           3,B           4,C           5,D           6,E           7,F  */
        ["brk","imp"],["ora","iix"],["___","___"],["slo","iix"],["___","___"],["ora","zpg"],["asl","zpg"],["slo","zpg"],  # 00
        ["php","imp"],["ora","imm"],["asl","acc"],["anc","imm"],["___","___"],["ora","abs"],["asl","abs"],["slo","abs"],  # 08
        ["bpl","rel"],["ora","iiy"],["___","___"],["slo","iiy"],["___","___"],["ora","zpx"],["asl","zpx"],["slo","zpx"],  # 10
        ["clc","imp"],["ora","aby"],["___","___"],["slo","aby"],["___","___"],["ora","abx"],["asl","abx"],["slo","abx"],  # 18
        ["jsr","abs"],["and","iix"],["___","___"],["rla","iix"],["bit","zpg"],["and","zpg"],["rol","zpg"],["rla","zpg"],  # 20
        ["plp","imp"],["and","imm"],["rol","acc"],["anc","imm"],["bit","abs"],["and","abs"],["rol","abs"],["rla","abs"],  # 28
        ["bmi","rel"],["and","iiy"],["___","___"],["rla","iiy"],["___","___"],["and","zpx"],["rol","zpx"],["rla","zpx"],  # 30
        ["sec","imp"],["and","aby"],["___","___"],["rla","aby"],["___","___"],["and","abx"],["rol","abx"],["rla","abx"],  # 38
        ["rti","imp"],["eor","iix"],["___","___"],["sre","iix"],["___","___"],["eor","zpg"],["lsr","zpg"],["sre","zpg"],  # 40
        ["pha","imp"],["eor","imm"],["lsr","acc"],["alr","imm"],["jmp","abs"],["eor","abs"],["lsr","abs"],["sre","abs"],  # 48
        ["bvc","rel"],["eor","iiy"],["___","___"],["sre","iiy"],["___","___"],["eor","zpx"],["lsr","zpx"],["sre","zpx"],  # 50
        ["cli","imp"],["eor","aby"],["___","___"],["sre","aby"],["___","___"],["eor","abx"],["lsr","abx"],["sre","abx"],  # 58
        ["rts","imp"],["adc","iix"],["___","___"],["rra","iix"],["___","___"],["adc","zpg"],["ror","zpg"],["rra","zpg"],  # 60
        ["pla","imp"],["adc","imm"],["ror","acc"],["arr","imm"],["jmp","ind"],["adc","abs"],["ror","abs"],["rra","abs"],  # 68
        ["bvs","rel"],["adc","iiy"],["___","___"],["rra","iiy"],["___","___"],["adc","zpx"],["ror","zpx"],["rra","zpx"],  # 70
        ["sei","imp"],["adc","aby"],["___","___"],["rra","aby"],["___","___"],["adc","abx"],["ror","abx"],["rra","abx"],  # 78
        ["___","___"],["sta","iix"],["___","___"],["sax","iiy"],["sty","zpg"],["sta","zpg"],["stx","zpg"],["sax","zpg"],  # 80
        ["dey","imp"],["___","___"],["txa","imp"],["xaa","imm"],["sty","abs"],["sta","abs"],["stx","abs"],["sax","abs"],  # 88
        ["bcc","rel"],["sta","iiy"],["___","___"],["ahx","iiy"],["sty","zpx"],["sta","zpx"],["stx","zpy"],["sax","zpy"],  # 90
        ["tya","imp"],["sta","aby"],["txs","imp"],["tas","aby"],["___","___"],["sta","abx"],["shx","aby"],["ahx","aby"],  # 98
        ["ldy","imm"],["lda","iix"],["ldx","imm"],["lax","iix"],["ldy","zpg"],["lda","zpg"],["ldx","zpg"],["lax","zpg"],  # A0
        ["tay","imp"],["lda","imm"],["tax","imp"],["lax","imm"],["ldy","abs"],["lda","abs"],["ldx","abs"],["lax","abs"],  # A8
        ["bcs","rel"],["lda","iiy"],["___","___"],["lax","iiy"],["ldy","zpx"],["lda","zpx"],["ldx","zpy"],["lax","zpy"],  # B0
        ["clv","imp"],["lda","aby"],["tsx","imp"],["las","aby"],["ldy","abx"],["lda","abx"],["ldx","aby"],["lax","aby"],  # B8
        ["cpy","imm"],["cmp","iix"],["___","___"],["dcp","iix"],["cpy","zpg"],["cmp","zpg"],["dec","zpg"],["dcp","zpg"],  # C0
        ["iny","imp"],["cmp","imm"],["dex","imp"],["sbx","imm"],["cpy","abs"],["cmp","abs"],["dec","abs"],["dcp","abs"],  # C8
        ["bne","rel"],["cmp","iiy"],["___","___"],["dcp","iiy"],["___","___"],["cmp","zpx"],["dec","zpx"],["dcp","zpx"],  # D0
        ["cld","imp"],["cmp","aby"],["___","___"],["dcp","aby"],["___","___"],["cmp","abx"],["dec","abx"],["dcp","abx"],  # D8
        ["cpx","imm"],["sbc","iix"],["___","___"],["isc","iix"],["cpx","zpg"],["sbc","zpg"],["inc","zpg"],["isc","zpg"],  # E0
        ["inx","imp"],["sbc","imm"],["nop","imp"],["___","___"],["cpx","abs"],["sbc","abs"],["inc","abs"],["isc","abs"],  # E8
        ["beq","rel"],["sbc","iiy"],["___","___"],["isc","iiy"],["___","___"],["sbc","zpx"],["inc","zpx"],["isc","zpx"],  # F0
        ["sed","imp"],["sbc","aby"],["___","___"],["isc","aby"],["___","___"],["sbc","abx"],["inc","abx"],["isc","abx"]   # F8
    ]

    operand_sizes = {
        'imp': 0,
        'imm': 1,
        'zpg': 1,
        'zpx': 1,
        'zpy': 1,
        'iix': 1,
        'iiy': 1,
        'abs': 2,
        'abx': 2,
        'aby': 2,
        'ind': 2,
        'rel': 1,
        'acc': 0,
    }

    addressing_modes = sorted(list(set([opcode[1] for opcode in opcodes])))
    instructions = list(set([opcode[0] for opcode in opcodes]))

    def __init__(self, instruction_name, mode, immediate: Immediate = None, address: Address = None, use_upper: bool = False, use_hex: bool = False, show_labels: bool = True):

        self.logger = logging.getLogger("shazzam")
        self.instruction_name = instruction_name
        self.mode = mode
        self.opcode = None
        self.use_upper = use_upper
        self.use_hex = use_hex
        self.show_labels = show_labels

        try:
            Instruction.opcodes.index([instruction_name, mode])
        except ValueError:
            raise RuntimeError(f"Opcode {instruction_name} cannot be used with mode {mode}")

        for idx, opcode in enumerate(Instruction.opcodes):
            if opcode[0] == instruction_name and opcode[1] == mode:
                self.opcode = idx

        if self.mode not in Instruction.addressing_modes:
            raise ValueError(f"Unknown addressing {mode} for instruction {instruction_name}")

        if self.opcode is None:
            raise ValueError(f"Unknown instruction {instruction_name} with addressing mode {mode}")

        if immediate and not isinstance(immediate, Immediate):
            raise ValueError("Immediate has to be a Immediate object")

        if address and not isinstance(address, Address):
            raise ValueError("Address has to be a Address object")

        self.address = address
        self.immediate = immediate

        # set by segment
        self.end_address = None
        self.bytecode = None

        self.logger.debug(f"Instruction created: {self.instruction_name} / {self.opcode} / {self.mode}")

    def check_constraints(self) -> None:
        """[summary]

        Raises:
            ValueError: [description]
            ValueError: [description]
            ValueError: [description]
            ValueError: [description]
        """
        if self.mode in ['imm'] and self.immediate.value and self.immediate.value > 0xff:
            raise ValueError(f"Immediate value cannot be bigger then a byte! Got: {self.immediate.value}")

        elif self.mode in ['zpg', 'zpx', 'zpy'] and self.address.value and self.address.value > 0xff:
            raise ValueError(f"Absolute zp address cannot be bigger then a byte! Got: {self.value:04X}")

        elif self.mode in ['abs', 'abx', 'aby'] and self.address.value and self.address.value > 0xffff:
            raise ValueError(f"Absolute address cannot be bigger then a word! Got: {self.value:04X}")

        elif self.mode in ['rel'] and self.address.relative and self.address.relative > 0xff:
            raise ValueError(f"Relative address value cannot be bigger then a byte! Got: {self.address.relative:04X}")

    def get_instruction_name(self) -> str:
        """[summary]

        Returns:
            str: [description]
        """
        return self.instruction_name.upper() if self.use_upper else self.instruction_name

    def hash(self) -> str:
        """[summary]

        Returns:
            str: [description]
        """
        return hashlib.md5(str(self).encode()).hexdigest()

    def get_cycle_count(self) -> int:
        """[summary]

        Returns:
            int: [description]
        """
        return Instruction.cycle_counts[self.opcode]

    def get_size(self) -> int:
        return Instruction.operand_sizes[self.mode] + 1

    def get_opcode(self) -> str:
        """[summary]

        Returns:
            str: [description]
        """
        return self.opcode

    def get_operand(self) -> (str, bool):
        """[summary]

        Returns:
            str: [description]
        """
        if self.address and self.address.value is None and self.address.relative is None:
            raise RuntimeError("Relative address is managed by segment gen_code to find the label value")

        if self.immediate and self.immediate.value is None:
            raise RuntimeError("Immediate value is managed by segment gen_code to find the label value")

        def_address_value = self.address.value if self.address and self.address.value is not None else 0
        def_immediate_value = self.immediate.value if self.immediate and self.immediate.value is not None else 0

        self.logger.debug(f"Get operand for mode {self.mode}")

        if self.mode in ['imp', 'acc']:
            return None

        elif self.mode in ['imm']:
            return (def_immediate_value & 0xff)

        elif self.mode in ['zpg', 'zpx', 'zpy']:
            return (def_address_value & 0xff)

        elif self.mode in ['rel']:
            if self.address.relative is None:
                raise RuntimeError("Relative address is managed by segment gen_code to find the label value")
            else:
                return (self.address.relative & 0xff)

        else:
            return (def_address_value & 0xffff)

    def __str__(self) -> str:
        """[summary]

        Raises:
            NotImplementedError: [description]

        Returns:
            str: [description]
        """
        val = None
        if self.mode == 'imp':
            val = ""

        elif self.mode == 'imm':
            if self.immediate.name and self.show_labels:
                if self.immediate.high_byte:
                    val = f"#>{self.immediate.name}"
                else:
                    val = f"#<{self.immediate.name}"
            else:
                if self.use_hex:
                    val = f"#${self.immediate.value:02X}" if self.use_upper else f"#${self.immediate.value:02x}"
                else:
                    val = f"#{self.immediate.value}"

        elif self.mode == 'abs':
            if (self.address.name and self.show_labels) or self.address.value is None:
                val = self.address.fullname
            else:
                val = f"${self.address.value:04X}" if self.use_upper else f"${self.address.value:04x}"

        elif self.mode == 'ind':
            if self.address.name and self.show_labels:
                val = f"({self.address.fullname})"
            else:
                val = f"(${self.address.value:04X})" if self.use_upper else f"(${self.address.value:04x})"

        elif self.mode == 'zpg':
            if self.address.name and self.show_labels:
                val = f"{self.address.fullname}"
            else:
                val = f"${self.address.value:02X}" if self.use_upper else f"${self.address.value:02x}"

        elif self.mode == 'zpx':
            if self.address.name and self.show_labels:
                val = f"{self.address.fullname},X" if self.use_upper else f"{self.address.fullname},x"
            else:
                val = f"${self.address.value:02X},X" if self.use_upper else f"${self.address.value:02x},x"

        elif self.mode == 'zpy':
            if self.address.name and self.show_labels:
                val = f"{self.address.fullname},Y" if self.use_upper else f"{self.address.fullname},y"
            else:
                val = f"${self.address.value:02X},Y" if self.use_upper else f"${self.address.value:02x},y"

        elif self.mode == 'abx':
            if self.address.name and self.show_labels:
                val = f"{self.address.fullname},X" if self.use_upper else f"{self.address.fullname},x"
            else:
                val = f"${self.address.value:04X},X" if self.use_upper else f"${self.address.value:04x},x"

        elif self.mode == 'aby':
            if self.address.name and self.show_labels:
                val = f"{self.address.fullname},Y" if self.use_upper else f"{self.address.fullname},y"
            else:
                val = f"${self.address.value:04X},Y" if self.use_upper else f"${self.address.value:04x},y"

        elif self.mode == 'rel':
            if self.address.name and (self.show_labels or self.address.value is None):
                val = self.address.fullname
            else:
                val = f"${self.address.value:04X}" if self.use_upper else f"${self.address.value:04x}"

        elif self.mode == 'iiy':
            val = f"(${self.address.value:02X}),Y" if self.use_upper else f"(${self.address.value:02x}),y"

        elif self.mode == 'iix':
            val = f"(${self.address.value:02X},X)" if self.use_upper else f"(${self.address.value:02x},x)"

        elif self.mode == 'acc':
            val = "a"

        # else:
        #     raise NotImplementedError(f"Model {self.mode}")

        if val is None:
            raise NotImplementedError(f"Model {self.mode}")

        return f"{self.get_instruction_name()} {val}"

