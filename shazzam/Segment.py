
import shazzam.globals as g
from shazzam.defs import CommentsFormat, DirectiveFormat, CodeFormat, Alias, DirectiveDelimiter
from shazzam.Instruction import Instruction
from shazzam.Address import Address
from shazzam.ByteData import ByteData
from shazzam.Rasterline import Rasterline
from shazzam.Emu6502 import Emu6502
from shazzam.Immediate import Immediate

from enum import Enum
import binascii
from typing import List, Any, Dict
import io
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
class SegmentType(Enum):
    CODE = 0
    REGISTERS = 1
    SPRITE = 2
    CHARACTERS = 3
    SCREEN_MEM = 4
    BITMAP = 5
    GENERIC_DATA = 6


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

    directive_delimiter = {
        DirectiveDelimiter.NO_DELIMITER : "",
        DirectiveDelimiter.DOUBLE_QUOTE : '"'
    }

    def __init__(self, start_adr: int, name: str,
                code_format: List[CodeFormat] = None, comments_format: CommentsFormat = None,
                directive_prefix: DirectiveFormat = None, directive_delimiter: DirectiveDelimiter = None, use_relative_addressing: bool = False,
                fixed_address: bool = False, segment_type: SegmentType = SegmentType.CODE, group: int = None):
        """[summary]

        Args:
            start_adr (int): [description]
            name (str): [description]
            code_format (List[CodeFormat], optional): [description]. Defaults to None.
            comments_format (CommentsFormat, optional): [description]. Defaults to CommentsFormat.USE_SEMICOLON.
            directive_prefix (DirectiveFormat, optional): [description]. Defaults to DirectiveFormat.USE_DOT.
        """
        self.logger = logging.getLogger("shazzam")
        self.start_adr = start_adr
        self.end_adr = start_adr
        self.fixed_start_address = start_adr if fixed_address else None
        self.instructions = {}
        self.next_position = start_adr
        self.name = name
        self.total_cycles_used = 0
        self.labels = {}
        self.required_labels = {}
        self.use_relative_addressing = use_relative_addressing
        self.segment_type = segment_type
        self.group = group

        if code_format is None:
            code_format = g._CODE_FORMAT
        if comments_format is None:
            comments_format = g._COMMENTS_FORMAT
        if directive_prefix is None:
            directive_prefix = g._DIRECTIVE_PREFIX
        if directive_delimiter is None:
            directive_delimiter = g._DIRECTIVE_DELIMITER

        self.logger.debug("Prefs: {code_format} / {comments_format} / {directive_prefix}")

        self.show_address = True if CodeFormat.ADDRESS in code_format else False
        self.show_bytecode = True if CodeFormat.BYTECODE in code_format else False
        self.show_cycles = True if CodeFormat.CYCLES in code_format else False
        self.use_uppercase = True if CodeFormat.UPPERCASE in code_format else False
        self.use_hex = True if CodeFormat.USE_HEX in code_format else False
        self.show_labels = True if CodeFormat.SHOW_LABELS in code_format else False

        self.comment_char = Segment.comments_chars[comments_format]
        self.directive_prefix = Segment.directive_prefix[directive_prefix]
        self.directive_delimiter = Segment.directive_delimiter[directive_delimiter]

        self.rasterlines = {}
        self.anonymous_labels = {}

    @property
    def size(self):
        return self.end_adr - self.start_adr

    def change_format(self):
        """change_format"""
        code_format = g._CODE_FORMAT
        comments_format = g._COMMENTS_FORMAT
        directive_prefix = g._DIRECTIVE_PREFIX
        directive_delimiter = g._DIRECTIVE_DELIMITER

        self.logger.info(f"Reset Prefs: {code_format} / {comments_format} / {directive_prefix} / {directive_delimiter}")

        self.show_address = True if CodeFormat.ADDRESS in code_format else False
        self.show_bytecode = True if CodeFormat.BYTECODE in code_format else False
        self.show_cycles = True if CodeFormat.CYCLES in code_format else False
        self.use_uppercase = True if CodeFormat.UPPERCASE in code_format else False
        self.use_hex = True if CodeFormat.USE_HEX in code_format else False
        self.show_labels = True if CodeFormat.SHOW_LABELS in code_format else False
        self.directive_prefix = Segment.directive_prefix[directive_prefix]
        self.directive_delimiter = Segment.directive_delimiter[directive_delimiter]

    def close(self) -> None:
        """[summary]"""
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

        try:
            bcode = self.get_bytecode(instr)
            instr.bytecode = bcode
        except Exception as e:
            g.logger.debug(
                f"bytecode cannot be generated yet, will be resolve later! [{e}]")

        return instr

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
        self.logger.debug(
            f"added byte {immediate.value} at {self.next_position-1:04X}, next pos is not {self.next_position:04X}")

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
            raise ValueError(
                f"Label {name} already defined in segment at {self.labels[name]}")

        self.labels[name] = Address(name=name, value=self.next_position)

        return self.labels[name]

    def get_label(self, name: str) -> Address:
        """get_label

        Args:
            name (str): [description]

        Raises:
            ValueError: [description]

        Returns:
            Address: [description]
        """
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
        """get_segment_bytecode

        Returns:
            bytearray: [description]
        """
        self.resolve_labels()

        bytecode = bytearray([])
        for adr, instr in self.instructions.items():
            bcode = self.get_bytecode(instr)
            bytecode += bcode

        return bytecode

    def get_bytecode(self, instr: Instruction) -> bytearray:
        """[summary]

        Args:
            instr (Instruction): [description]

        Returns:
            bytearray: [description]
        """
        ope = instr.get_operand()
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

        return bytearray(data)

    def resolve_labels(self) -> None:
        """Replace all instructions with their absolute address.

        Raises:
            ValueError: [description]
            ValueError: [description]
        """
        # move end of segment labels
        for label, adr in self.labels.items():
            if adr.value == self.end_adr:
                adr.value = max(list(self.instructions.keys()))
                self.logger.info(f"Label {label} moved to address ${adr.value:04X}")

        # check labels
        self.logger.debug(f"Required labels: {self.required_labels}")
        for label, params in self.required_labels.items():

            if (label not in self.labels) and (label not in g._PROGRAM.global_labels):
                self.logger.debug("global labels:", g._PROGRAM.global_labels)
                raise ValueError(f"Label {label} is used but not defined locally or globally!")

            if params['relative'] and abs(params['from'] - self.labels[label].address) > 255:
                raise ValueError(f"Label {label} branch at {params['from']} is more than 1 bytes!")

        # resolve labels now!
        for adr, instr in self.instructions.items():
            self.logger.debug(f"Checking label for {instr} at {adr:04X}")

            if instr.immediate and instr.immediate.name:
                self.logger.debug(
                    f"-> immediate label name: {instr.immediate.name}")

                if instr.immediate.name in self.labels:

                    val = self.labels[instr.immediate.name].value & 0xff if not instr.immediate.high_byte else (
                        self.labels[instr.immediate.name].value >> 8) & 0xff

                    instr.immediate.value = val
                    instr.immediate.name = self.labels[instr.immediate.name].name

                elif instr.immediate.name in g._PROGRAM.global_labels:
                    val = g._PROGRAM.global_labels[instr.immediate.name].value & 0xff if not instr.immediate.high_byte else (
                        g._PROGRAM.global_labels[instr.immediate.name].value >> 8) & 0xff

                    instr.immediate.value = val
                    instr.immediate.name = g._PROGRAM.global_labels[instr.immediate.name].name
                else:
                    raise ValueError(f"Label {label} cannot be resolved locally or globally!")

            elif instr.address and instr.address.name:
                self.logger.debug(f"-> address label name: {instr.address.name}")
                if instr.address.name in self.labels:

                    if instr.mode == 'rel':
                        self.logger.debug(f"label address: {self.labels[instr.address.name].value}")
                        instr.address.value = self.labels[instr.address.name].value

                        if adr < self.labels[instr.address.name].value:
                            instr.address.relative = self.labels[instr.address.name].value - adr - instr.get_size()
                        else:
                            instr.address.relative = (self.labels[instr.address.name].value - (adr + instr.get_size())) & 0xff

                        self.logger.debug(f"Use relative addressing to label {instr.address.name} at {self.labels[instr.address.name].value:04X} from {adr:04X}")
                    else:
                        instr.address.value = self.labels[instr.address.name].value
                        instr.address.name = self.labels[instr.address.name].name

                elif instr.address.name in g._PROGRAM.global_labels:
                    instr.address.value = g._PROGRAM.global_labels[instr.address.name].value
                    instr.address.name = g._PROGRAM.global_labels[instr.address.name].name
                else:
                    raise ValueError(f"Label {label} cannot be resolved locally or globally!")

                self.logger.debug(f"Label {instr.address.name} replaced by absolute address {instr.address.value:04X}")


    def _gen_listing(self, code, label_size: int):

        self.logger.debug("Generating listing")
        listing_template_index = {
            "address": 0,
            "bytecode": 8 if self.show_address else 0,
            "label": 40 if self.show_bytecode else 8 if self.show_address else 0,
            "instruction": 40+label_size if self.show_bytecode else 8+label_size if self.show_address else label_size,
            "cycles": 40+label_size+20 if self.show_bytecode else 38+label_size+20 if self.show_address else label_size+20,
        }

        remaining_bytes_to_process = 0
        for adr, instr in self.instructions.items():

            instr.show_labels = False

            if self.use_uppercase:
                instr.use_upper = True
            if self.use_hex:
                instr.use_hex = True

            label = [k for k, v in self.labels.items() if v.value == adr]

            # substract start address if relative addressing
            address_offset = self.start_adr if self.use_relative_addressing else 0

            if isinstance(instr, ByteData):
                if remaining_bytes_to_process != 0:
                    remaining_bytes_to_process -= 1
                else:
                    prefix = self.directive_prefix

                    nb_bytes = 0
                    nolabel = True
                    try:
                        while adr+nb_bytes in self.instructions and nolabel and isinstance(self.instructions[adr+nb_bytes], ByteData):
                            nb_bytes += 1
                            nolabel = len([k for k, v in self.labels.items() if v.value == adr+nb_bytes]) == 0
                    except KeyError:
                        self.logger.error(f"Could not find address {adr+nb_bytes} (${adr+nb_bytes:04X}) in {self.instructions.keys()}")
                        raise


                    remaining_bytes_to_process = nb_bytes - 1
                    self.logger.debug(f"{nb_bytes} bytes of data before instruction")
                    if nb_bytes > 8:

                        # manage the remaining bytes if not a multiple of 8
                        nb_rows = nb_bytes // 8 + 1 if nb_bytes % 8 != 0 else nb_bytes // 8

                        for row in range(nb_rows):

                            r_label = [k for k, v in self.labels.items() if v.value == adr+(row*8)]
                            s_label = f"{r_label[0]}:" if r_label else ""

                            s_address = f"{adr+(row*8)-address_offset:04X}:" if self.show_address else ""
                            bcode = ""
                            for b in range(min(8, nb_bytes-(8*row))):
                                bytedata = self.instructions[adr+(row*8)+b]
                                g_bcode = self.get_bytecode(bytedata)
                                bcode += str(binascii.hexlify(g_bcode))[2:].replace("'", "").upper()

                            bcode1 = " ".join(bcode[i:i+2] for i in range(0, len(bcode), 2))
                            bcode2 = '$' + ", $".join(bcode[i:i+2] for i in range(0, len(bcode), 2))

                            line = ' '*100
                            if self.show_address:
                                line = _insert(line, s_address, listing_template_index["address"])
                            if self.show_bytecode:
                                line = _insert(line, bcode1, listing_template_index["bytecode"])

                            line = _insert(line, s_label, listing_template_index["label"])
                            line = _insert(line, f"{prefix}byte {bcode2}", listing_template_index["instruction"])
                            line.strip()
                            line += '\n'

                            code.append(line)
                    else:
                        s_address = f"{adr-address_offset:04X}:" if self.show_address else ""

                        r_label = [k for k, v in self.labels.items() if v.value == adr]
                        s_label = f"{r_label[0]}:" if r_label else ""

                        bcode = ""
                        for b in range(nb_bytes):
                            bytedata = self.instructions[adr+b]
                            g_bcode = self.get_bytecode(bytedata)
                            bcode += str(binascii.hexlify(g_bcode))[2:].replace("'", "").upper()

                        bcode1 = " ".join(bcode[i:i+2] for i in range(0, len(bcode), 2))
                        bcode2 = '$' + ", $".join(bcode[i:i+2] for i in range(0, len(bcode), 2))

                        line = ' '*100
                        if self.show_address:
                            line = _insert(line, s_address, listing_template_index["address"])
                        if self.show_bytecode:
                            line = _insert(line, bcode1, listing_template_index["bytecode"])

                        line = _insert(line, s_label, listing_template_index["label"])
                        line = _insert(line, f"{prefix}byte {bcode2}", listing_template_index["instruction"])
                        line.strip()
                        line += '\n'

                        code.append(line)
            else:
                s_address = f"{adr-address_offset:04X}:" if self.show_address else ""

                if len(label) > 1:
                    self.logger.warning(f"Mutiple labels ({label}) for the same address 0x{adr:04X}")

                s_label = f"{label[0]}:" if label else ""
                g_bcode = self.get_bytecode(instr)

                # remove leading 'b and trailing '. Ex: bytearray(b'\xa9\x0b') A90B
                bcode = str(binascii.hexlify(g_bcode))[2:].replace("'", "").upper()
                bcode = " ".join(bcode[i:i+2] for i in range(0, len(bcode), 2))

                s_bytecode = f"{bcode}" if self.show_bytecode else ""

                cycles = instr.get_cycle_count()
                bytes_used = instr.get_size()
                s_cycles = f"{self.comment_char} #{cycles} - {bytes_used}" if self.show_cycles and cycles > 0 else ""

                prefix = self.directive_prefix if isinstance(instr, ByteData) else ''

                line = ' '*100
                line = _insert(line, s_address, listing_template_index["address"])
                line = _insert(line, s_bytecode, listing_template_index["bytecode"])
                line = _insert(line, s_label, listing_template_index["label"])
                line = _insert(line, f"{prefix}{instr}", listing_template_index["instruction"])
                line = _insert(line, s_cycles, listing_template_index["cycles"])
                line.strip()
                line += '\n'

                code.append(line)

        return code

    def _gen_assembly(self, code, label_size: int):

        self.logger.debug("Generating assembly code")
        code_template_index = {
            "label": 0,
            "instruction": label_size,
            "cycles": label_size+30,
        }

        remaining_bytes_to_process = 0
        for adr, instr in self.instructions.items():

            instr.show_labels = True

            if self.use_uppercase:
                instr.use_upper = True
            if self.use_hex:
                instr.use_hex = True

            label = [k for k, v in self.labels.items() if v.value == adr]

            # substract start address if relative addressing
            address_offset = self.start_adr if self.use_relative_addressing else 0

            if isinstance(instr, ByteData):
                if remaining_bytes_to_process != 0:
                    remaining_bytes_to_process -= 1
                else:
                    self.logger.debug(f"Starting processing bytes at ${adr:04X}")
                    prefix = self.directive_prefix
                    nb_bytes = 0
                    nolabel = True
                    try:
                        while adr+nb_bytes in self.instructions and nolabel and isinstance(self.instructions[adr+nb_bytes], ByteData):
                            nb_bytes += 1
                            nolabel = len([k for k, v in self.labels.items() if v.value == adr+nb_bytes]) == 0
                    except KeyError:
                        self.logger.error(f"Could not find address {adr+nb_bytes} (${adr+nb_bytes:04X}) in {self.instructions.keys()}")
                        raise

                    remaining_bytes_to_process = nb_bytes - 1
                    self.logger.debug(f"{nb_bytes} bytes ({remaining_bytes_to_process}) of data before instruction")
                    if nb_bytes > 8:

                        # manage the remaining bytes if not a multiple of 8
                        nb_rows = nb_bytes // 8 + 1 if nb_bytes % 8 != 0 else nb_bytes // 8

                        for row in range(nb_rows):

                            r_label = [k for k, v in self.labels.items() if v.value == adr+(row*8)]
                            self.logger.debug(f"labels found at {adr+(row*8):04X} : {r_label}")
                            s_label = f"{r_label[0]}:" if r_label else ""

                            bcode = ""
                            for b in range(min(8, nb_bytes-(8*row))):
                                bytedata = self.instructions[adr+(row*8)+b]
                                g_bcode = self.get_bytecode(bytedata)
                                bcode += str(binascii.hexlify(g_bcode))[2:].replace("'", "").upper()

                            bcode2 = '$' + ", $".join(bcode[i:i+2] for i in range(0, len(bcode), 2))

                            line = ' '*100
                            line = _insert(line, s_label, code_template_index["label"])
                            line = _insert(line, f"{prefix}byte {bcode2}", code_template_index["instruction"])
                            line.strip()
                            line += '\n'

                            code.append(line)
                    else:
                        r_label = [k for k, v in self.labels.items() if v.value == adr]
                        self.logger.debug(f"labels found at {adr:04X} : {r_label}")
                        s_label = f"{r_label[0]}:" if r_label else ""

                        bcode = ""
                        for b in range(nb_bytes):
                            bytedata = self.instructions[adr+b]
                            g_bcode = self.get_bytecode(bytedata)
                            bcode += str(binascii.hexlify(g_bcode))[2:].replace("'", "").upper()

                        bcode2 = '$' + ", $".join(bcode[i:i+2] for i in range(0, len(bcode), 2))

                        line = ' '*100
                        line = _insert(line, s_label, code_template_index["label"])
                        line = _insert(line, f"{prefix}byte {bcode2}", code_template_index["instruction"])
                        line.strip()
                        line += '\n'

                        code.append(line)
            else:
                if len(label) > 1:
                    self.logger.warning(f"Mutiple labels ({label}) for the same address 0x{adr:04X}")
                    for i in range(len(label)-1):
                        s_label = f"{label[i]}:"
                        line = ' '*100
                        line = _insert(line, s_label, code_template_index["label"])
                        line.strip()
                        line += '\n'
                        code.append(line)

                s_label = f"{label[-1]}:" if label else ""
                cycles = instr.get_cycle_count()
                bytes_used = instr.get_size()
                s_cycles = f"{self.comment_char} #{cycles} - {bytes_used}" if self.show_cycles and cycles > 0 else ""


                prefix = self.directive_prefix if isinstance(instr, ByteData) else ''

                line = ' '*100
                line = _insert(line, s_label, code_template_index["label"])
                line = _insert(line, f"{prefix}{instr}", code_template_index["instruction"])
                line = _insert(line, s_cycles, code_template_index["cycles"])
                line.strip()
                line += '\n'

                code.append(line)

        return code

    def gen_code(self, listing: bool = False) -> None:
        """Generates assembly code.

        Returns:
            [type]: [description]
        """
        self.resolve_labels()

        code = []

        # add globals import/export
        locals_labels = list(self.labels.keys())
        globals_labels = list(g._PROGRAM.global_labels.keys())

        for label in globals_labels:
            if label not in locals_labels:
                code.append(f'\t\t{self.directive_prefix}import {label}\n')
            else:
                code.append(f'\t\t{self.directive_prefix}export {label}\n')

        code.append('\n')

        # add segment directive
        code.append(f'\t\t{self.directive_prefix}segment {self.directive_delimiter}{self.name}{self.directive_delimiter}\n')

        # get longest label
        if len(locals_labels) > 0:
            label_size = max(10, len(max(locals_labels)) + 8)
        else:
            label_size = 10

        self.logger.debug(f"Label size: {label_size}")

        if listing:
            code = self._gen_listing(code, label_size)
        else:
            cod = self._gen_assembly(code, label_size)

        return code

    def emulate(self, start_address: Any = None, cycles_count_start: Any = None, cycles_count_end: Any = None, debug_mode: bool = False):
        """Emulates the code from start_address .

        Args:
            start_address (int, optional): [description]. Defaults to None.

        Returns:
            [type]: [description]
        """
        self.resolve_labels()

        if start_address is None:
            start_address = self.start_adr

        elif isinstance(start_address, str):
            if start_address in self.labels:
                adr = self.labels[start_address]
                if adr.value is not None:
                    start_address = adr.value
                else:
                    raise ValueError(f"label {start_address} not yet resolved")
            else:
                raise ValueError(f"label {start_address} not found")
        elif not isinstance(start_address, int):
            raise ValueError(f"start_address has to be a label or an int")

        if cycles_count_start is not None:
            if isinstance(cycles_count_start, str) and cycles_count_start in self.labels:
                adr = self.labels[cycles_count_start]
                if adr.value is not None:
                    cycles_count_start = adr.value
                else:
                    raise ValueError(f"label {cycles_count_start} not yet resolved")

        if cycles_count_end is not None:
            if isinstance(cycles_count_end, str) and cycles_count_end in self.labels:
                adr = self.labels[cycles_count_end]
                if adr.value is not None:
                    cycles_count_end = adr.value
                else:
                    raise ValueError(f"label {cycles_count_end} not yet resolved")


        self.logger.debug(f"Emulation start address: {start_address:04X}")
        emu = Emu6502()
        ram = io.BytesIO(self.get_segment_bytecode())

        self.logger.info(f"Emulating from ${self.start_adr:04X}, to ${self.next_position:04X} starting at ${start_address:04X}")
        if cycles_count_start and cycles_count_end:
            self.logger.info(f"Counting cycles between ${cycles_count_start:04X} and ${cycles_count_end:04X}")
            cpu_state, mmu_state, cycles_used = emu.load_and_run(ram, self.start_adr, self.next_position, start_address, cycles_count_start, cycles_count_end, debug_mode=debug_mode)
        else:
            cpu_state, mmu_state, cycles_used = emu.load_and_run(ram, self.start_adr, self.next_position, start_address, debug_mode=debug_mode)


        return cpu_state, mmu_state, cycles_used

    def get_last_instruction(self) -> Instruction:
        """[summary]

        Returns:
            Instruction: [description]
        """
        self.logger.debug(
            f"Instructions in the current segment: {list(self.instructions.keys())}")
        return self.instructions[list(self.instructions.keys())[-1]]

    def get_stats(self):
        """[summary]

        Returns:
            [type]: [description]
        """
        if len(self.instructions) == 0:
            return Alias({
                "start_address": hex(self.start_adr),
            })

        last_instr = self.get_last_instruction()
        return Alias({
            "size": self.next_position - self.start_adr,
            "cycles": self.total_cycles_used,
            "instructions": len(self.instructions),
            "start_address": hex(self.start_adr),
            "current_address": hex(self.next_position),
            "last_instruction": {
                "code": str(last_instr),
                "size": last_instr.get_size(),
                "cycles": last_instr.get_cycle_count()
            }
        })

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
