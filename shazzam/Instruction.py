import hashlib
import logging
from shazzam.Address import Address
from shazzam.Immediate import Immediate

class Instruction():
    """6502 Instruction class"""
    cycle_counts = [
       # 0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F
         7, 6, 2, 8, 3, 3, 5, 5, 3, 2, 2, 2, 4, 4, 6, 6, # 0
         2, 5, 2, 8, 4, 4, 6, 6, 2, 4, 2, 7, 4, 4, 7, 7, # 1
         6, 6, 2, 8, 3, 3, 5, 5, 4, 2, 2, 2, 4, 4, 6, 6, # 2
         2, 5, 2, 8, 4, 4, 6, 6, 2, 4, 2, 7, 4, 4, 7, 7, # 3
         6, 6, 2, 8, 3, 3, 5, 5, 3, 2, 2, 2, 3, 4, 6, 6, # 4
         2, 5, 2, 8, 4, 4, 6, 6, 2, 4, 2, 7, 4, 4, 7, 7, # 5
         6, 6, 2, 8, 3, 3, 5, 5, 4, 2, 2, 2, 5, 4, 6, 6, # 6
         2, 5, 2, 8, 4, 4, 6, 6, 2, 4, 2, 7, 4, 4, 7, 7, # 7
         2, 6, 2, 6, 3, 3, 3, 3, 2, 2, 2, 2, 4, 4, 4, 4, # 8
         2, 6, 2, 6, 4, 4, 4, 4, 2, 5, 2, 5, 5, 5, 5, 5, # 9
         2, 6, 2, 6, 3, 3, 3, 3, 2, 2, 2, 2, 4, 4, 4, 4, # A
         2, 5, 2, 5, 4, 4, 4, 4, 2, 4, 2, 4, 4, 4, 4, 4, # B
         2, 6, 2, 8, 3, 3, 5, 5, 2, 2, 2, 2, 4, 4, 6, 6, # C
         2, 5, 2, 8, 4, 4, 6, 6, 2, 4, 2, 7, 4, 4, 7, 7, # D
         2, 6, 2, 8, 3, 3, 5, 5, 2, 2, 2, 2, 4, 4, 6, 6, # E
         2, 5, 2, 8, 4, 4, 6, 6, 2, 4, 2, 7, 4, 4, 7, 7  # F
      ]

    opcodes = [
        #     0,8           1,9           2,A           3,B           4,C           5,D           6,E           7,F  */
        ["brk","imp"],["ora","iix"],["___","___"],["___","___"],["___","___"],["ora","zpg"],["asl","zpg"],["___","___"],  # 00
        ["php","imp"],["ora","imm"],["asl","acc"],["___","___"],["___","___"],["ora","abs"],["asl","abs"],["___","___"],  # 08
        ["bpl","rel"],["ora","iiy"],["___","___"],["___","___"],["___","___"],["ora","zpx"],["asl","zpx"],["___","___"],  # 10
        ["clc","imp"],["ora","aby"],["___","___"],["___","___"],["___","___"],["ora","abx"],["asl","abx"],["___","___"],  # 18
        ["jsr","abs"],["and","iix"],["___","___"],["___","___"],["bit","zpg"],["and","zpg"],["rol","zpg"],["___","___"],  # 20
        ["plp","imp"],["and","imm"],["rol","acc"],["___","___"],["bit","abs"],["and","abs"],["rol","abs"],["___","___"],  # 28
        ["bmi","rel"],["and","iiy"],["___","___"],["___","___"],["___","___"],["and","zpx"],["rol","zpx"],["___","___"],  # 30
        ["sec","imp"],["and","aby"],["___","___"],["___","___"],["___","___"],["and","abx"],["rol","abx"],["___","___"],  # 38
        ["rti","imp"],["eor","iix"],["___","___"],["___","___"],["___","___"],["eor","zpg"],["lsr","zpg"],["___","___"],  # 40
        ["pha","imp"],["eor","imm"],["lsr","acc"],["___","___"],["jmp","abs"],["eor","abs"],["lsr","abs"],["___","___"],  # 48
        ["bvc","rel"],["eor","iiy"],["___","___"],["___","___"],["___","___"],["eor","zpx"],["lsr","zpx"],["___","___"],  # 50
        ["cli","imp"],["eor","aby"],["___","___"],["___","___"],["___","___"],["eor","abx"],["lsr","abx"],["___","___"],  # 58
        ["rts","imp"],["adc","iix"],["___","___"],["___","___"],["___","___"],["adc","zpg"],["ror","zpg"],["___","___"],  # 60
        ["pla","imp"],["adc","imm"],["ror","acc"],["___","___"],["jmp","ind"],["adc","abs"],["ror","abs"],["___","___"],  # 68
        ["bvs","rel"],["adc","iiy"],["___","___"],["___","___"],["___","___"],["adc","zpx"],["ror","zpx"],["___","___"],  # 70
        ["sei","imp"],["adc","aby"],["___","___"],["___","___"],["___","___"],["adc","abx"],["ror","abx"],["___","___"],  # 78
        ["___","___"],["sta","iix"],["___","___"],["___","___"],["sty","zpg"],["sta","zpg"],["stx","zpg"],["___","___"],  # 80
        ["dey","imp"],["___","___"],["txa","imp"],["___","___"],["sty","abs"],["sta","abs"],["stx","abs"],["___","___"],  # 88
        ["bcc","rel"],["sta","iiy"],["___","___"],["___","___"],["sty","zpx"],["sta","zpx"],["stx","zpy"],["___","___"],  # 90
        ["tya","imp"],["sta","aby"],["txs","imp"],["___","___"],["___","___"],["sta","abx"],["___","___"],["___","___"],  # 98
        ["ldy","imm"],["lda","iix"],["ldx","imm"],["___","___"],["ldy","zpg"],["lda","zpg"],["ldx","zpg"],["___","___"],  # A0
        ["tay","imp"],["lda","imm"],["tax","imp"],["___","___"],["ldy","abs"],["lda","abs"],["ldx","abs"],["___","___"],  # A8
        ["bcs","rel"],["lda","iiy"],["___","___"],["___","___"],["ldy","zpx"],["lda","zpx"],["ldx","zpy"],["___","___"],  # B0
        ["clv","imp"],["lda","aby"],["tsx","imp"],["___","___"],["ldy","abx"],["lda","abx"],["ldx","aby"],["___","___"],  # B8
        ["cpy","imm"],["cmp","iix"],["___","___"],["___","___"],["cpy","zpg"],["cmp","zpg"],["dec","zpg"],["___","___"],  # C0
        ["iny","imp"],["cmp","imm"],["dex","imp"],["___","___"],["cpy","abs"],["cmp","abs"],["dec","abs"],["___","___"],  # C8
        ["bne","rel"],["cmp","iiy"],["___","___"],["___","___"],["___","___"],["cmp","zpx"],["dec","zpx"],["___","___"],  # D0
        ["cld","imp"],["cmp","aby"],["___","___"],["___","___"],["___","___"],["cmp","abx"],["dec","abx"],["___","___"],  # D8
        ["cpx","imm"],["sbc","iix"],["___","___"],["___","___"],["cpx","zpg"],["sbc","zpg"],["inc","zpg"],["___","___"],  # E0
        ["inx","imp"],["sbc","imm"],["nop","imp"],["___","___"],["cpx","abs"],["sbc","abs"],["inc","abs"],["___","___"],  # E8
        ["beq","rel"],["sbc","iiy"],["___","___"],["___","___"],["___","___"],["sbc","zpx"],["inc","zpx"],["___","___"],  # F0
        ["sed","imp"],["sbc","aby"],["___","___"],["___","___"],["___","___"],["sbc","abx"],["inc","abx"],["___","___"]   # F8
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
        'acc': 1,
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
            raise ValueError(f"Unknwon addressing {mode} for instruction {instruction_name}")

        if self.opcode is None:
            raise ValueError(f"Unknwon instruction {instruction_name} with addressing mode {mode}")

        if immediate and not isinstance(immediate, Immediate):
            raise ValueError("immediate has to be a Immediate object"
                             )
        if address and not isinstance(address, Address):
            raise ValueError("address has to be a Address object")

        self.address = address
        self.immediate = immediate

        # set by segment
        self.end_address = None
        self.bytecode = None

        self.logger.debug(f"instruction created: {self.instruction_name} / {self.opcode} / {self.mode}")

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
            raise RuntimeError(f"Relative address is managed by segment gen_code to find the label value")

        if self.immediate and self.immediate.value is None:
            raise RuntimeError(f"Immediate value is managed by segment gen_code to find the label value")

        def_address_value = self.address.value if self.address and self.address.value is not None else 0
        def_immediate_value = self.immediate.value if self.immediate and self.immediate.value is not None else 0

        self.logger.debug(f"Get operand for mode {self.mode}")

        if self.mode in ['imp']:
            return None

        elif self.mode in ['imm', 'acc']:
            return (def_immediate_value & 0xff)

        elif self.mode in ['zpg', 'zpx', 'zpy']:
            return (def_address_value & 0xff)

        elif self.mode in ['rel']:
            if self.address.relative is None:
                raise RuntimeError(f"Relative address is managed by segment gen_code to find the label value")
                # return (0 & 0xffff)
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
                val = self.address.name
            else:
                val = f"${self.address.value:04X}" if self.use_upper else f"${self.address.value:04x}"

        elif self.mode == 'ind':
            if self.address.name and self.show_labels:
                val = f"({self.address.name})"
            else:
                val = f"(${self.address.value:04X})" if self.use_upper else f"(${self.address.value:04x})"

        elif self.mode == 'zpg':
            if self.address.name and self.show_labels:
                val = f"{self.address.name}"
            else:
                val = f"${self.address.value:02X}" if self.use_upper else f"${self.address.value:02x}"

        elif self.mode == 'zpx':
            if self.address.name and self.show_labels:
                val = f"{self.address.name},X" if self.use_upper else f"{self.address.name},x"
            else:
                val = f"${self.address.value:02X},X" if self.use_upper else f"${self.address.value:02x},x"

        elif self.mode == 'zpy':
            if self.address.name and self.show_labels:
                val = f"{self.address.name},Y" if self.use_upper else f"{self.address.name},y"
            else:
                val = f"${self.address.value:02X},Y" if self.use_upper else f"${self.address.value:02x},y"
        elif self.mode == 'abx':
            if self.address.name and self.show_labels:
                val = f"{self.address.name},X" if self.use_upper else f"{self.address.name},x"
            else:
                val = f"${self.address.value:04X},X" if self.use_upper else f"${self.address.value:04x},x"

        elif self.mode == 'aby':
            if self.address.name and self.show_labels:
                val = f"{self.address.name},Y" if self.use_upper else f"{self.address.name},y"
            else:
                val = f"${self.address.value:04X},Y" if self.use_upper else f"${self.address.value:04x},y"

        elif self.mode == 'rel':
            if self.address.name and (self.show_labels or self.address.value is None):
                val = self.address.name
            else:
                val = f"${self.address.value:04X}" if self.use_upper else f"${self.address.value:04x}"

        elif self.mode == 'iiy':
            val = f"(${self.address.value:02X}),Y" if self.use_upper else f"(${self.address.value:02x}),y"

        elif self.mode == 'iix':
            val = f"(${self.address.value:02X},X)" if self.use_upper else f"(${self.address.value:02x},x)"

        else:
            raise NotImplementedError(f"Model {self.mode}")

        if val is None:
            raise NotImplementedError(f"Model {self.mode}")

        return f"{self.get_instruction_name()} {val}"

