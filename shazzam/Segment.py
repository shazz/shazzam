
import shazzam.globals as g
from shazzam.defs import *
from shazzam.Instruction import Instruction
from shazzam.Address import Address
from shazzam.ByteData import ByteData
from shazzam.Rasterline import Rasterline
from shazzam.Emu6502 import Emu6502
from shazzam.Immediate import Immediate

import binascii
from typing import List
import io
from functools import reduce
import logging

# ---------------------------------------------------------------------
# internal utils
# ---------------------------------------------------------------------
def _insert(source_str, insert_str, pos):
    """[summary]

    Args:
        source_str ([type]): [description]
        insert_str ([type]): [description]
        pos ([type]): [description]

    Returns:
        [type]: [description]
    """
    return source_str[:pos] + insert_str + source_str[pos:len(source_str)-len(insert_str)]

# ---------------------------------------------------------------------
# Segment class
# ---------------------------------------------------------------------
class Segment():
    """Segment class"""
    comments_chars = {
        CommentsFormat.USE_SEMICOLON: ';',
        CommentsFormat.USE_SHARP: "#",
        CommentsFormat.USE_SLASH: "//"
    }

    directive_prefix = {
        DirectiveFormat.NO_PREFIX: '',
        DirectiveFormat.USE_DOT: '.',
        DirectiveFormat.USE_EXCLAMATION: '!'
    }

    def __init__(self, start_adr: int, name: str, code_format: List[CodeFormat] = None, comments_format: CommentsFormat = None, directive_prefix: DirectiveFormat = None, use_relative_addressing: bool = False):
        """[summary]

        Args:
            start_adr (int): [description]
            name (str): [description]
            code_format (List[CodeFormat], optional): [description]. Defaults to None.
            comments_format (CommentsFormat, optional): [description]. Defaults to CommentsFormat.USE_SEMICOLON.
            directive_prefix (DirectiveFormat, optional): [description]. Defaults to DirectiveFormat.USE_DOT.
        """
        self.start_adr = start_adr
        self.end_adr = start_adr
        self.instructions = {}
        self.next_position = start_adr
        self.name = name
        self.total_cycles_used = 0
        self.labels = {}
        self.required_labels = {}
        self.use_relative_addressing = use_relative_addressing
        self.logger = logging.getLogger("shazzam")

        if code_format is None:
            code_format = g._CODE_FORMAT
        if comments_format is None:
            comments_format = g._COMMENTS_FORMAT
        if directive_prefix is None:
            directive_prefix = g._DIRECTIVE_PREFIX

        self.logger.debug(f"Prefs: {code_format} / {comments_format} / {directive_prefix}")

        self.show_address = True if CodeFormat.ADDRESS in code_format else False
        self.show_bytecode = True if CodeFormat.BYTECODE in code_format else False
        self.show_cycles = True if CodeFormat.CYCLES in code_format else False
        self.use_uppercase = True if CodeFormat.UPPERCASE in code_format else False
        self.use_hex = True if CodeFormat.USE_HEX in code_format else False
        self.show_labels = True if CodeFormat.SHOW_LABELS in code_format else False

        self.comment_char = Segment.comments_chars[comments_format]
        self.directive_prefix = Segment.directive_prefix[directive_prefix]

        self.rasterlines = {}
        self.anonymous_labels = {}

    def change_format(self):

        code_format = g._CODE_FORMAT
        comments_format = g._COMMENTS_FORMAT
        directive_prefix = g._DIRECTIVE_PREFIX

        self.logger.debug(f"Reset Prefs: {code_format} / {comments_format} / {directive_prefix}")

        self.show_address = True if CodeFormat.ADDRESS in code_format else False
        self.show_bytecode = True if CodeFormat.BYTECODE in code_format else False
        self.show_cycles = True if CodeFormat.CYCLES in code_format else False
        self.use_uppercase = True if CodeFormat.UPPERCASE in code_format else False
        self.use_hex = True if CodeFormat.USE_HEX in code_format else False
        self.show_labels = True if CodeFormat.SHOW_LABELS in code_format else False

    def close(self) -> None:
        """[summary]
        """
        self.end_adr = self.next_position

    def add_instruction(self, instr: Instruction) -> bytearray:
        """[summary]

        Args:
            instr (Instruction): [description]

        Returns:
            bytearray: [description]
        """
        self.instructions[self.next_position] = instr
        self.next_position += instr.get_size()
        self.total_cycles_used += instr.get_cycle_count()
        instr.end_address = self.next_position

        # check size, relative addresses,...
        instr.check_constraints()

        if g._CURRENT_RASTER is not None:
            self.logger.debug(f"Adding {instr} to rasterline")
            g._CURRENT_RASTER.add_cycles(instr.get_cycle_count())

        bcode, resolved = self.get_bytecode(instr)

        if not resolved:
            g.logger.warning("bytecade cannot be generated yet")
            return None

        return bcode

    def add_byte(self, immediate: Immediate) -> None:
        """[summary]

        Args:
            immediate (Immediate): [description]

        Returns:
            [type]: [description]
        """
        data = ByteData(immediate)
        self.instructions[self.next_position] = data
        self.next_position += 1
        self.logger.debug(f"Added byte, next pos is not {self.next_position:04X}")

        return self.get_bytecode(data)

    def add_label(self, name: str) -> Address:
        """Add segment label

        Args:
            name (str): [description]

        Raises:
            ValueError: [description]

        Returns:
            Address: [description]
        """
        if name in self.labels:
            raise ValueError(f"Label {name} already defined in segment at {self.labels[name]}")

        self.labels[name] = Address(name=name, value=self.next_position)

        return self.labels[name]

    def get_label(self, name: str) -> Address:

        if name not in self.labels:
            self.logger.warning(f"label '{name}' cannot be found in segment")
            raise ValueError(f"Cannot find label '{name}' in segment")

        return self.labels[name]

    def need_label(self, name: str, relative: bool = False) -> None:
        """[summary]

        Args:
            label (str): [description]
            relative (bool, optional): [description]. Defaults to False.
        """
        self.required_labels[name] = {
            "from": self.next_position,
            "relative": relative
        }

    def get_segment_bytecode(self) -> bytearray:

        self.resolve_labels()

        bytecode = bytearray([])
        for adr, instr in self.instructions.items():
            bcode, resolved = self.get_bytecode(instr)
            if not resolved:
                raise ValueError("Bytecodecannot be generated yet")
            bytecode += bcode

        return bytecode

    def get_bytecode(self, instr: Instruction) -> bytearray:
        """[summary]

        Args:
            instr (Instruction): [description]

        Returns:
            bytearray: [description]
        """
        # print(instr.get_operand())
        ope, resolved = instr.get_operand()
        op = instr.get_opcode()

        if ope is not None:
            if instr.get_size() == 2+1:
                self.logger.debug(f"Get bytecode for {instr:}: opcode: {op:02X} operand: {ope:04X}")
                data = [op, ope & 0xff, (ope >> 8) & 0xff]
            else:
                self.logger.debug(f"Get bytecode for {instr:}: opcode: {op:02X} operand: {ope:02X}")
                data = [op, ope & 0xff]
        else:
            self.logger.debug(f"Get bytecode for {instr:}: opcode: {op:02X}")
            data = [instr.get_opcode()]

        self.logger.debug(f"Got bytecode for {instr}: {data}")

        return bytearray(data), resolved

    def resolve_labels(self) -> None:
        """Replace all instructions with their absolute address.

        Raises:
            ValueError: [description]
            ValueError: [description]
        """
        # check labels
        self.logger.debug(f"Required labels: {self.required_labels}")
        for label, params in self.required_labels.items():

            if (label not in self.labels) and (label not in g._PROGRAM.global_labels):
                print("global:", g._PROGRAM.global_labels)
                raise ValueError(f"Label {label} is used but not defined locally or globally!")

            if params['relative'] and abs(params['from'] - self.labels[label].address) > 255:
                raise ValueError(f"Label {label} branch at {params['from']} is more than 1 bytes!")

        # resolve labels now!
        for adr, instr in self.instructions.items():
            self.logger.debug(f"Checking label for {instr} at {adr:04X}")

            if instr.immediate and instr.immediate.name:
                self.logger.debug(f"-> immediate label name: {instr.immediate.name}")

                if instr.immediate.name in self.labels:
                    if self.use_relative_addressing:
                        instr.immediate.value = self.labels[instr.label.name].address - adr - instr.get_size() if adr < self.labels[instr.label] else adr - self.labels[instr.label] - instr.get_size()
                        self.logger.info(f"Use relative addressing to label {instr.label} at {self.labels[instr.label.address]:04X} from {adr:04X} will be: {instr.value}")

                    else:
                        val = self.labels[instr.immediate.name].value & 0xff if not instr.immediate.high_byte else (self.labels[instr.immediate.name].value >> 8) & 0xff

                        instr.immediate.value = val
                        instr.immediate.name = self.labels[instr.immediate.name].name

                elif instr.immediate.name in g._PROGRAM.global_labels:
                    val = g._PROGRAM.global_labels[instr.immediate.name].value & 0xff if not instr.immediate.high_byte else (g._PROGRAM.global_labels[instr.immediate.name].value >> 8) & 0xff

                    instr.immediate.value = val
                    instr.immediate.name = g._PROGRAM.global_labels[instr.immediate.name].name
                else:
                    raise ValueError(f"Label {label} cannot be resolved locally or globally!")

            elif instr.address and instr.address.name:
                self.logger.debug(f"-> address label name: {instr.address.name}")
                if instr.address.name in self.labels:
                    instr.address.value = self.labels[instr.address.name].value
                    instr.address.name = self.labels[instr.address.name].name

                elif instr.address.name in g._PROGRAM.global_labels:
                    instr.address.value = g._PROGRAM.global_labels[instr.address.name].value
                    instr.address.name = g._PROGRAM.global_labels[instr.address.name].name
                else:
                    raise ValueError(f"Label {label} cannot be resolved locally or globally!")

                self.logger.debug(f"Label {instr.address.name} replaced by absolute address {instr.address.value:04X}")

    def gen_code(self) -> None:
        """Generates assembly code.

        Returns:
            [type]: [description]
        """
        self.resolve_labels()

        code = []

        # add segment directive
        code.append(f'\t\t{self.directive_prefix}segment "{self.name}"\n')

        code_template_index = {
            "address": 0,
            "bytecode": 8 if self.show_address else 0,
            "label": 40 if self.show_bytecode else 8 if self.show_address else 0,
            "instruction": 50 if self.show_bytecode else 18 if self.show_address else 10,
            "cycles": 70 if self.show_bytecode else 38 if self.show_address else 30,
        }

        process_byte = True
        for adr, instr in self.instructions.items():

            if self.use_uppercase:
                instr.use_upper = True
            if self.use_hex:
                instr.use_hex = True

            label = [k for k,v in self.labels.items() if v.value == adr]

            # substract start address if relative addressing
            address_offset = self.start_adr if self.use_relative_addressing else 0

            if isinstance(instr, ByteData):
                if process_byte:

                    process_byte = False

                    prefix = self.directive_prefix

                    nb_bytes = 0

                    #TODO: break if a label is defined in the middle else won't be shown
                    # won't work with process_byte bool
                    try:
                        while adr+nb_bytes in self.instructions and isinstance(self.instructions[adr+nb_bytes], ByteData):
                            nb_bytes += 1
                    except KeyError as e:
                        self.logger.error(f"Could not find address {adr+nb_bytes} (${adr+nb_bytes:04X}) in {self.instructions.keys()}")
                        raise

                    self.logger.debug(f"{nb_bytes} bytes of data before instruction")
                    if nb_bytes > 8:

                        # manage the remaining bytes if not a multiple of 8
                        nb_rows = nb_bytes // 8 + 1 if nb_bytes % 8 != 0 else nb_bytes // 8

                        for row in range(nb_rows):

                            r_label = [k for k,v in self.labels.items() if v.value == adr+(row*8)]
                            s_label = f"{r_label[0]}:" if r_label else ""

                            s_address = f"{adr+(row*8)-address_offset:04X}:" if self.show_address else ""
                            bcode = ""
                            for b in range(min(8, nb_bytes-(8*row))):
                                bytedata = self.instructions[adr+(row*8)+b]

                                g_bcode, resolved = self.get_bytecode(bytedata)
                                if not resolved:
                                    raise ValueError("Bytecode cannot be yet generated")
                                bcode += str(binascii.hexlify(g_bcode))[2:].replace("'", "").upper()
                            bcode1 = " ".join(bcode[i:i+2] for i in range(0, len(bcode), 2))
                            bcode2 = '$'+", $".join(bcode[i:i+2] for i in range(0, len(bcode), 2))

                            line = ' '*100
                            if self.show_address:
                                line = _insert(line, s_address, code_template_index["address"])
                            if self.show_bytecode:
                                line = _insert(line, bcode1, code_template_index["bytecode"])

                            line = _insert(line, s_label, code_template_index["label"])
                            line = _insert(line, f"{prefix}byte {bcode2}", code_template_index["instruction"])
                            line.strip()
                            line  += '\n'

                            code.append(line)
                    else:
                        s_address = f"{adr-address_offset:04X}:" if self.show_address else ""

                        r_label = [k for k,v in self.labels.items() if v.value == adr]
                        s_label = f"{r_label[0]}:" if r_label else ""

                        bcode = ""
                        for b in range(nb_bytes):
                            bytedata = self.instructions[adr+b]

                            g_bcode, resolved = self.get_bytecode(bytedata)
                            if not resolved:
                                raise ValueError("Bytecode cannot be yet generated")
                            bcode += str(binascii.hexlify(g_bcode))[2:].replace("'", "").upper()
                        bcode1 = " ".join(bcode[i:i+2] for i in range(0, len(bcode), 2))
                        bcode2 = '$'+", $".join(bcode[i:i+2] for i in range(0, len(bcode), 2))

                        line = ' '*100
                        if self.show_address:
                            line = _insert(line, s_address, code_template_index["address"])
                        if self.show_bytecode:
                            line = _insert(line, bcode1, code_template_index["bytecode"])

                        line = _insert(line, s_label, code_template_index["label"])
                        line = _insert(line, f"{prefix}byte {bcode2}", code_template_index["instruction"])
                        line.strip()
                        line  += '\n'

                        code.append(line)
            else:
                process_byte = True
                s_address = f"{adr-address_offset:04X}:" if self.show_address else ""
                s_label = f"{label[0]}:" if label else ""

                g_bcode, resolved = self.get_bytecode(instr)
                if not resolved:
                    raise ValueError("Bytecode cannot be yet generated")
                bcode = str(binascii.hexlify(g_bcode))[2:].replace("'", "").upper()    # remove leading 'b and trailing '. Ex: bytearray(b'\xa9\x0b') A90B
                bcode = " ".join(bcode[i:i+2] for i in range(0, len(bcode), 2))

                s_bytecode = f"{bcode}" if self.show_bytecode else ""

                cycles = instr.get_cycle_count()
                s_cycles = f"{self.comment_char} {cycles}" if self.show_cycles and cycles > 0 else ""

                prefix = self.directive_prefix if isinstance(instr, ByteData) else ''

                line = ' '*100
                line = _insert(line, s_address, code_template_index["address"])
                line = _insert(line, s_bytecode, code_template_index["bytecode"])
                line = _insert(line, s_label, code_template_index["label"])
                line = _insert(line, f"{prefix}{instr}", code_template_index["instruction"])
                line = _insert(line, s_cycles, code_template_index["cycles"])
                line.strip()
                line  += '\n'

                code.append(line)

        return code

    def emulate(self, start_address: int = None):
        """Emulates the code from start_address .

        Args:
            start_address (int, optional): [description]. Defaults to None.

        Returns:
            [type]: [description]
        """
        if start_address is None:
            start_address = self.start_adr

        emu = Emu6502()
        ram = io.BytesIO(self.get_segment_bytecode())

        self.logger.info(f"Emulating from {self.start_adr:04X}, to {self.next_position:04X} starting at {start_address:04X}")

        cpu_state, mmu_state = emu.load_and_run(ram, self.start_adr, self.next_position, start_address)

        return cpu_state, mmu_state

    def get_last_instruction(self) -> Instruction:
        """[summary]

        Returns:
            Instruction: [description]
        """
        self.logger.debug(f"Instructions in the current segment: {list(self.instructions.keys())}")
        return self.instructions[list(self.instructions.keys())[-1]]

    def get_stats(self):
        """[summary]

        Returns:
            [type]: [description]
        """
        if len(self.instructions) == 0:
            raise RuntimeError(f"No instruction in the segment!")

        last_instr = self.get_last_instruction()
        return {
            "size": self.next_position - self.start_adr,
            "cycles_used": self.total_cycles_used,
            "instructions": len(self.instructions),
            "start_address": hex(self.start_adr),
            "current_address": hex(self.next_position),
            "last_instruction": {
                "code": str(last_instr),
                "size": last_instr.get_size(),
                "cycles": last_instr.get_cycle_count()
            }
        }


    def get_anonymous_label(self, prefix: str) -> str:
        """Generate an anonymous label, in a macro for example

        Args:
            prefix (str): [description]

        Returns:
            str: [description]
        """
        if prefix not in self.anonymous_labels:
            self.anonymous_labels[prefix] = 0
        else:
            self.anonymous_labels[prefix] += 1

        return f"_{prefix}_{self.anonymous_labels[prefix]}"

    # def checksum(self) -> int:
    #     return reduce(lambda x,y : hashlib.md5((x+y).encode()).hexdigest(), [item.hash() for item in self.instructions.values()])

    def add_rasterline(self, index: int, rasterline: Rasterline) -> None:
        """[summary]

        Args:
            index (int): [description]
            rasterline (Rasterline): [description]
        """
        self.rasterlines[index] = rasterline
