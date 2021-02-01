from time import sleep
from contextlib import contextmanager
import hashlib
import os
import dill

from reloading import reloading

import shazzam.globals as g
from shazzam.Instruction import Instruction
from shazzam.defs import CodeFormat, CommentsFormat, DirectiveFormat, System, DetectMode, Alias
from shazzam.defs import RegisterACC, RegisterX, RegisterY
from shazzam.Rasterline import Rasterline
from shazzam.Segment import Segment, SegmentType
from shazzam.Address import Address
from shazzam.Immediate import Immediate
from shazzam.Cruncher import Cruncher
from shazzam.Assembler import Assembler

from shazzam.optimizer.SegmentOptimizer import SegmentOptimizer, SegmentOptimizerType
from shazzam.optimizer.C64Mode import C64Mode
from shazzam.optimizer.Part import Part
from shazzam.optimizer.MemorySegment import MemorySegment

import enum
from typing import List, Any, Dict


# ---------------------------------------------------------------------
# py64gen public functions
# ---------------------------------------------------------------------
def set_prefs(default_code_segment: str, code_format: List[CodeFormat], comments_format: CommentsFormat, directive_prefix: DirectiveFormat):
    global _CODE_FORMAT, _COMMENTS_FORMAT, _DIRECTIVE_PREFIX

    g._CODE_FORMAT = code_format
    g._COMMENTS_FORMAT = comments_format
    g._DIRECTIVE_PREFIX = directive_prefix
    g._DEFAULT_CODE_SEGMENT = default_code_segment


@contextmanager
def segment(start_adr: int, name: str, use_relative_addressing: bool = False, check_address_dups: bool = True, fixed_address: bool = False, segment_type: SegmentType = SegmentType.CODE, group: int = None) -> Segment:
    """[summary]

    Args:
        start_adr (int): [description]
        name (str): [description]
        gen_files (bool, optional): [description]. Defaults to True.

    Returns:
        Segment: [description]

    Yields:
        Iterator[Segment]: [description]
    """
    global _CURRENT_CONTEXT, _PROGRAM

    seg = Segment(start_adr=start_adr, name=name.upper(), use_relative_addressing=use_relative_addressing, fixed_address=fixed_address, segment_type=segment_type, group=group)
    g._CURRENT_CONTEXT = seg

    yield seg

    found = False
    for segment in g._PROGRAM.segments:

        # check segments with same base address
        if segment.start_adr == start_adr and segment.name != seg.name and check_address_dups:
            raise ValueError(f"Multiple segments have the same start address {start_adr:04X}: {segment.name} and {seg.name}")

        # else
        if segment.start_adr == start_adr and segment.name == seg.name:
            found = True

            g.logger.debug(f"Removing segment {segment.name} to PROGRAM")
            g._PROGRAM.segments.remove(segment)

            g.logger.debug(f"Adding segment {segment.name} to PROGRAM")
            g._PROGRAM.segments.append(seg)
            break

    if not found:
        g.logger.debug(f"Adding new segment {seg.name} to PROGRAM")
        g._PROGRAM.segments.append(seg)

    g._CURRENT_CONTEXT.close()
    g._CURRENT_CONTEXT = None


@contextmanager
def rasterline(system: System = System.PAL, mode: DetectMode = DetectMode.MANUAL, nb_sprites: int = 8, y_pos: int = 0, y_scroll: int = 0) -> Rasterline:
    """[summary]

    Args:
        system (System, optional): [description]. Defaults to System.PAL.
        mode (DetectMode, optional): [description]. Defaults to DetectMode.MANUAL.
        nb_sprites (int, optional): [description]. Defaults to 8.
        y_pos (int, optional): [description]. Defaults to 0.
        y_scroll (int, optional): [description]. Defaults to 0.

    Returns:
        Rasterline: [description]

    Yields:
        Iterator[Rasterline]: [description]
    """
    global _CURRENT_RASTER, _PROGRAM, _CURRENT_CONTEXT

    line = Rasterline(system, mode, nb_sprites, y_pos, y_scroll)
    g._CURRENT_RASTER = line

    yield line

    # seg = _CURRENT_CONTEXT

    g._CURRENT_RASTER.close()
    g._CURRENT_RASTER = None


def gen_code(header: str = None, format_code: Alias = None, gen_listing: bool = True, format_listing: Alias = None) -> None:
    """[summary]

    Args:
        header (str, optional): [description]. Defaults to None.
        format_code (Alias, optional): [description]. Defaults to None.
        gen_listing (bool, optional): [description]. Defaults to True.
        format_listing (Alias, optional): [description]. Defaults to None.
    """
    global _PROGRAM

    _check_segments_overlap()

    if header is None:
        header  = "; Generated code using Shazzam py64gen\n"
        header += "; DO NOT EDIT, MODIFICATIONS WILL BE LOST\n"
        header += "; Copyright (C) 2021 TRSi\n"
        header += "; \n"
        header += "; https://github.com/shazz/shazzam\n\n"

    if format_code:
        g.logger.debug(f"Setting assembler pref: {format_code}")
        set_prefs(
            default_code_segment=format_code.default_code_segment,
            code_format=format_code.code,
            comments_format=format_code.comments,
            directive_prefix=format_code.directive)

    for segment in g._PROGRAM.segments:

        g.logger.debug(
            f"generating code for segment {segment.name} from {g._PROGRAM.segments}")
        segment.change_format()
        code = segment.gen_code()

        if code:
            os.makedirs(f"generated/{g._PROGRAM.name}", exist_ok=True)
            with open(f"generated/{g._PROGRAM.name}/{segment.name}.asm", "w") as f:
                f.writelines(header)
                f.writelines(code)

    if gen_listing:
        if format_listing is None:
            g.logger.debug(f"Setting listing format: {format_code}")
            format_listing = Alias({
                "default_code_segment": "CODE",
                "code": [CodeFormat.USE_HEX, CodeFormat.BYTECODE, CodeFormat.CYCLES, CodeFormat.ADDRESS, CodeFormat.SHOW_LABELS],
                "comments": CommentsFormat.USE_SEMICOLON,
                "directive": DirectiveFormat.USE_DOT
            })

        set_prefs(
            default_code_segment=format_listing.default_code_segment,
            code_format=format_listing.code,
            comments_format=format_listing.comments,
            directive_prefix=format_listing.directive)

        for segment in g._PROGRAM.segments:

            segment.change_format()
            code = segment.gen_code(listing=True)

            if code:
                os.makedirs(f"generated/{g._PROGRAM.name}", exist_ok=True)
                with open(f"generated/{g._PROGRAM.name}/{segment.name}.lst", "w") as f:
                    f.writelines(header)
                    f.writelines(code)


def assemble_segment(assembler: Assembler) -> None:
    """[summary]

    Args:
        assembler (Assembler): [description]

    Raises:
        RuntimeError: [description]

    Returns:
        [type]: [description]
    """
    global _CURRENT_CONTEXT, _PROGRAM

    if g._CURRENT_CONTEXT is None:
        raise RuntimeError("No segment defined!")

    output_file = assembler.assemble_segment(g._PROGRAM, g._CURRENT_CONTEXT)

    return output_file


def assemble_prg(assembler: Assembler, start_address: int, cruncher: Cruncher = None) -> None:
    """Assemble listing

    Args:
        assembler ([type]): [description]
        start_address (int): [description]
        cruncher (None): [description]
    """
    global _PROGRAM

    output_file = assembler.assemble_prg(g._PROGRAM, start_address)

    if cruncher is not None:
        try:
            cruncher.crunch_prg(output_file)
        except AttributeError as e:
            g.logger.error(
                f"The cruncher class {cruncher.__class__} needs to implement crunch_prg()!")
            g.logger.error(e)


def get_segment_addresses(name: str) -> int:
    """get_segment_start_address

    Args:
        name (str): [description]

    Raises:
        ValueError: [description]

    Returns:
        int: [description]
    """
    global _PROGRAM

    # import threading
    # x = threading.Thread(target=_watch_segment, args=(name,))

    # TODO: how to make this works if a segment is defined after this call ?
    for segment in g._PROGRAM.segments:

        if segment.name.upper() == name.upper():
            return Alias({
                "start_address": segment.start_adr,
                "end_address": segment.end_adr
            })

    raise ValueError(f"Segment {name} not (yet?) found!")

# def _watch_segment(name):
#     import time
#     print(f"Looking for segment {name}")

#     not_found = True

#     while not_found:
#         for segment in g._PROGRAM.segments:
#             if segment.name.upper() == name.upper():
#                 info = Alias({
#                     "start_address": segment.start_adr,
#                     "end_address": segment.end_adr
#                 })
#                 not_found = False
#                 break
#         time.sleep(1)
#     return info


def gen_irqloader_script(irqloader, parts_definition: Dict):
    """gen_irqloader_script

    Args:
        irqloader ([type]): [description]
        parts_definition (Dict): [description]

    Raises:
        NotImplementedError: [description]
    """
    global _PROGRAM
    raise NotImplementedError()

def optimize_segments(specific_memory_org: List = None, bank_setup: C64Mode = C64Mode.IO_VISIBLE, optimizer_type: SegmentOptimizerType = SegmentOptimizerType.BFD):
    """[summary]

    Args:
        specific_memory_org (List, optional): [description]. Defaults to None.
        bank_setup (C64Mode, optional): [description]. Defaults to C64Mode.IO_VISIBLE.
        optimizer_type (SegmentOptimizerType, optional): [description]. Defaults to SegmentOptimizerType.BFD.

    Raises:
        ValueError: [description]

    Returns:
        [type]: [description]
    """
    global _PROGRAM

    optimizer = SegmentOptimizer()
    optimizer.select_bank(bank_setup)

    if specific_memory_org and len(specific_memory_org) > 0:
        for location in specific_memory_org:
            optimizer.add_memory_segment(location.start_address, location.end_address, location.type)
    else:
        optimizer.add_memory_segment(0x0200, 0x3FFF, MemorySegment.SegmentType.UserRAM)
        optimizer.add_memory_segment(0x4000, 0x7FFF, MemorySegment.SegmentType.UserRAM)
        optimizer.add_memory_segment(0x8000, 0xBFFF, MemorySegment.SegmentType.UserRAM)
        optimizer.add_memory_segment(0xC000, 0xCFFF, MemorySegment.SegmentType.UserRAM)
        optimizer.add_memory_segment(0xD000, 0xDFFF, MemorySegment.SegmentType.IO)
        optimizer.add_memory_segment(0xE000, 0xFFFF, MemorySegment.SegmentType.UserRAM)

    for segment in g._PROGRAM.segments:
        optimizer.add_code_segment(size=segment.size, name=segment.name, part_type=segment.segment_type, fixed_address=segment.fixed_start_address, group=segment.group)

    if optimizer_type is SegmentOptimizerType.FF:
        results = optimizer.run_first_fit()
    elif optimizer_type is SegmentOptimizerType.NF:
        results = optimizer.run_next_fit()
    elif optimizer_type is SegmentOptimizerType.BF:
        results = optimizer.run_best_fit()
    elif optimizer_type is SegmentOptimizerType.FFD:
        results = optimizer.run_first_fit_decreasing()
    elif optimizer_type is SegmentOptimizerType.NFD:
        results = optimizer.run_next_fit_decreasing()
    elif optimizer_type is SegmentOptimizerType.BFD:
        results = optimizer.run_best_fit_decreasing()
    else:
        raise ValueError(f"Unknown optimizer: {optimizer_type}")

    return results

# ---------------------------------------------------------------------
# Assembler directives
# ---------------------------------------------------------------------


def at(value: Any) -> Address:
    if isinstance(value, str) and value != "":
        return Address(name=value)
    elif isinstance(value, int):
        return Address(value=value)
    else:
        raise ValueError("Address must be an int or a non empty string")


def ind_at(value: Any) -> Address:
    if isinstance(value, str) and value != "":
        return Address(name=value, indirect=True)
    elif isinstance(value, int):
        return Address(value=value, indirect=True)
    else:
        raise ValueError("Address must be an int or a non empty string")


def rel_at(value: Any) -> Address:
    if isinstance(value, str) and value != "":
        return Address(name=value)
    elif isinstance(value, int):
        rel_address = (value - (get_current_address() + 2)) & 0xff
        g.logger.debug(
            f"Relative address: {value:04X} - ({get_current_address():04X}+2) = {rel_address:04X}")

        if rel_address > 0xff:
            raise ValueError(
                f"Relative address cannot be bigger than a byte: {get_current_address():04X} - {value:04X} = {rel_address:04X}")

        return Address(value=value, relative=rel_address)
    else:
        raise ValueError(
            "Relative address must be an int or a non empty string")


def imm(value: Any) -> Immediate:
    if isinstance(value, str):
        if value.startswith('>'):
            return Immediate(name=value[1:], high_byte=True)
        elif value.startswith('<'):
            return Immediate(name=value[1:], high_byte=False)
        else:
            raise ValueError(
                f"Low byte (<) or High byte (>) must be specified. Not {value}")

    elif isinstance(value, int):
        return Immediate(value=value)
    else:
        raise ValueError("Immediate must be an int or a string")


def label(name: str, is_global: bool = False) -> Address:
    """[summary]

    Args:
        name (str): [description]

    Raises:
        RuntimeError: [description]
        ValueError: [description]
    """
    global _CURRENT_CONTEXT
    if g._CURRENT_CONTEXT is None:
        raise RuntimeError("No segment defined!")

    if name is None or len(name) == 0:
        raise ValueError("Label cannot be empty")

    label: Address = g._CURRENT_CONTEXT.add_label(name)

    if is_global:
        g._PROGRAM.add_label(label)
        # TODO: generate include file? with globals addresses ?

    return label


def get_anonymous_label(name: str) -> str:
    """[summary]

    Args:
        name (str): [description]

    Raises:
        RuntimeError: [description]

    Returns:
        str: [description]
    """
    global _CURRENT_CONTEXT
    if g._CURRENT_CONTEXT is None:
        raise RuntimeError("No segment defined!")

    return g._CURRENT_CONTEXT.get_anonymous_label(name)


def byte(value: Any) -> bytearray:

    global _CURRENT_CONTEXT
    if g._CURRENT_CONTEXT is None:
        raise RuntimeError("No segment defined!")

    if isinstance(value, str):
        if value.startswith('>'):
            return g._CURRENT_CONTEXT.add_byte(Immediate(name=value[1:], high_byte=True))
        elif value.startswith('<'):
            return g._CURRENT_CONTEXT.add_byte(Immediate(name=value[1:], high_byte=False))
        else:
            g.logger.warning(
                "Low byte (<) or High byte (>) not specified. Considering this is a character string")

            ret_array = []
            for v in value:
                ret_array.append(g._CURRENT_CONTEXT.add_byte(
                    Immediate(value=ord(v))))

            return ret_array

    elif isinstance(value, int):
        return g._CURRENT_CONTEXT.add_byte(Immediate(value=value))

    elif isinstance(value, list):
        ret_array = []
        for v in value:
            ret_array.append(g._CURRENT_CONTEXT.add_byte(Immediate(value=v)))
        return bytearray(ret_array)
    else:
        raise ValueError("Immediate must be an int or a string")


def word(value: int, label: str) -> None:
    """[summary]

    Args:
        value (int): [description]
        label (str): [description]

    Raises:
        RuntimeError: [description]
        ValueError: [description]
    """
    global _CURRENT_CONTEXT
    if g._CURRENT_CONTEXT is None:
        raise RuntimeError("No segment defined!")

    if value > 0xffff:
        raise ValueError(f"Value exceed word size: {value}")

    g._CURRENT_CONTEXT.add_word(value, label)


def incbin(data: bytearray) -> None:
    """[summary]

    Args:
        data (bytearray): [description]

    Raises:
        RuntimeError: [description]
    """
    global _CURRENT_CONTEXT
    if g._CURRENT_CONTEXT is None:
        raise RuntimeError("No segment defined!")

    if data is not None:
        if not (isinstance(data, bytearray) or isinstance(data, bytes)):
            raise ValueError(
                f"incbin argument must be a bytearray and not a {type(data)}")

        g.logger.info(f"Incbin {len(data)} bytes of data")
        for b in data:
            g._CURRENT_CONTEXT.add_byte(Immediate(value=b))


def get_current_address() -> int:

    global _CURRENT_CONTEXT
    if g._CURRENT_CONTEXT is None:
        raise RuntimeError("No segment defined!")

    return g._CURRENT_CONTEXT.next_position

def get_label_address(label: str) -> int:

    global _CURRENT_CONTEXT
    if g._CURRENT_CONTEXT is None:
        raise RuntimeError("No segment defined!")

    if isinstance(label, str):
        if label in g._CURRENT_CONTEXT.labels:
            adr = g._CURRENT_CONTEXT.labels[label]
            if adr.value is not None:
                return adr.value
            else:
                raise ValueError(f"label {start_address} not yet resolved")
        else:
            raise ValueError(f"label {start_address} not found")


# -----------------------------------------------------------
# Private functions
# -----------------------------------------------------------
def _check_segments_overlap(code_segment: str = "CODE") -> None:

    intervals = []
    for segment in g._PROGRAM.segments:
        if segment.name == code_segment:
            # adding basic header 13 bytes
            intervals.append((segment.start_adr, segment.end_adr+13))
        else:
            intervals.append((segment.start_adr, segment.end_adr))

    intervals.sort()
    g.logger.info(
        f"Checking overlapping intervals: {[(hex(interval[0]), hex(interval[1])) for interval in intervals]}")

    for i in range(1, len(intervals)):
        if intervals[i][0] <= intervals[i-1][1]:
            raise ValueError(
                f"The segments {g._PROGRAM.segments[i-1].name} and {g._PROGRAM.segments[i].name} overlap!")

# ---------------------------------------------------------------------
# Utils
# ---------------------------------------------------------------------
_funcs = {}
def generate(func, program_name: str) -> None:
    """generate

    Args:
        func ([type]): [description]
        program_name (str): [description]

    Raises:
        RuntimeError: [description]
    """
    global _PROGRAM
    g._PROGRAM.set_name(program_name)

    for i in reloading(range(10)):

        # check mnemonic mistakes like rts, nop...
        src_lines = dill.source.getsourcelines(func.__dict__['__inner__'])[0]
        for line in src_lines:
            for opcode in Instruction.opcodes:
                if opcode[0] in line and len(line.strip()) == 3:
                    raise RuntimeError(f"Mnemonic '{opcode[0]}'' cannot be called without () ! Should be {opcode[0]}()")

        # check source has changed
        src = dill.source.getsource(func.__dict__['__inner__'])

        # src = dill.source.getsource(func)
        h = hashlib.md5(src.encode()).hexdigest()

        if func.__name__ not in _funcs:
            _funcs[func.__name__] = h
            func()
        else:
            if _funcs[func.__name__] != h:
                _funcs[func.__name__] = h
                func()

        sleep(1.0)
    generate(func, program_name)


def _create_a_function(*args, **kwargs):
    """[summary]

    Raises:
        RuntimeError: [description]
        ValueError: [description]
        NotImplementedError: [description]

    Returns:
        [type]: [description]
    """
    mnemonic = kwargs['mnemonic']
    g.logger.debug(f'creating wrapper for {mnemonic}')
    modes = []

    opcode_found = False
    for opcode in Instruction.opcodes:
        if opcode[0] == mnemonic:
            modes.append(opcode[1])
            opcode_found = True

    if not opcode_found:
        raise ValueError(f"Opcode {mnemonic} doesn't exist!")

    if len(args) > 2:
        raise ValueError("Opcode can't have more than 2 operands!")

    def function_template(*args, **kwargs):

        global _CURRENT_CONTEXT
        if g._CURRENT_CONTEXT is None:
            raise RuntimeError("No segment defined!")

        address = None
        immediate = None
        index = None

        if len(args) > 0:
            if isinstance(args[0], Address):
                address = args[0]
            elif isinstance(args[0], Immediate):
                immediate = args[0]
            elif isinstance(args[0], enum.EnumMeta):
                index = args[0]
            else:
                raise ValueError(
                    f"1st operand must be an Address or an Immediate, not a {type(args[0])}")

        if len(args) == 2:
            index = args[1]
            if not isinstance(index, enum.EnumMeta):
                raise ValueError(
                    f"2nd operand must be a Register and not a {type(index)}")

        if len(args) > 2:
            raise ValueError("Too many arguments!")

        g.logger.debug(f"Adding conditions for modes: {modes}")

        try:
            if 'zpx' in modes and index is RegisterX and address.value and not address.indirect and address.value < 0x100:
                return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'zpx', address=address))

            if 'zpy' in modes and index is RegisterY and address.value and not address.indirect and address.value < 0x100:
                return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'zpy', address=address))

            if 'abx' in modes and index is RegisterX and not address.indirect:
                if address.value is not None:
                    if 'zpx' in modes and address.value < 0x100:
                        return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'zpx', address=address))
                    elif address.value > 0x100:
                        return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'abx', address=address))
                else:
                    g._CURRENT_CONTEXT.need_label(address.name)
                    return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'abx', address=address))

            if 'aby' in modes and index is RegisterY and not address.indirect:
                if address.value is not None:
                    if 'zpy' in modes and address.value < 0x100:
                        return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'zpy', address=address))
                    elif address.value > 0x100:
                        return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'aby', address=address))
                else:
                    g._CURRENT_CONTEXT.need_label(address.name)
                    return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'aby', address=address))

            if 'abs' in modes and index is None and address and not address.indirect:
                if address.value is not None:
                    if 'zpg' in modes and address.value < 0x100:
                        return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'zpg', address=address))
                    elif address.value >= 0x100:
                        return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'abs', address=address))
                else:
                    g._CURRENT_CONTEXT.need_label(address.name)
                    return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'abs', address=address))

            if 'rel' in modes:
                if address.relative is not None:
                    return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'rel', address=address))
                else:
                    g._CURRENT_CONTEXT.need_label(address.name)
                    return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'rel', address=address))

            if 'imm' in modes and immediate is not None:
                if immediate.value is None:
                    g._CURRENT_CONTEXT.need_label(immediate.name)
                return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'imm', immediate=immediate))

            if 'imp' in modes:
                return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'imp'))

            if 'iix' in modes and index is RegisterX and address and address.indirect:
                if address.value and address.value <= 0x100:
                    return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'iix', address=address))

            if 'iiy' in modes and index is RegisterY and address and address.indirect:
                if address.value and address.value <= 0x100:
                    return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'iiy', address=address))

            if 'acc' in modes and index is RegisterACC:
                return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'acc'))

            if 'ind' in modes:
                if address.value:
                    return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'ind', address=address))
                else:
                    g._CURRENT_CONTEXT.need_label(address.name)
                    return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'ind', address=address))
        except Exception:
            import inspect
            # 0 represents this line,  1 represents line at caller
            callerframerecord = inspect.stack()[1]

            frame = callerframerecord[0]
            info = inspect.getframeinfo(frame)
            print(f"Error: {info}")

            raise

        raise NotImplementedError(
            f"No condition for {mnemonic} and args: {args}. Possible modes: {modes}")

    return function_template

# ---------------------------------------------------------------------
# Opcodes wrappers
# ---------------------------------------------------------------------


g.initialize()

adc = ADC = _create_a_function(mnemonic="adc")
alr = ALR = _create_a_function(mnemonic="alr")
anc = ANC = _create_a_function(mnemonic="anc")
andr= AND = _create_a_function(mnemonic="and")
arr = ARR = _create_a_function(mnemonic="arr")
asl = ASL = _create_a_function(mnemonic="asl")
bcc = BCC = _create_a_function(mnemonic="bcc")
bcs = BCS = _create_a_function(mnemonic="bcs")
beq = BEQ = _create_a_function(mnemonic="beq")
bit = BIT = _create_a_function(mnemonic="bit")
bmi = BMI = _create_a_function(mnemonic="bmi")
bne = BNE = _create_a_function(mnemonic="bne")
bpl = BPL = _create_a_function(mnemonic="bpl")
brk = BRK = _create_a_function(mnemonic="brk")
bvc = BVC = _create_a_function(mnemonic="bvc")
bvs = BVS = _create_a_function(mnemonic="bvs")
clc = CLC = _create_a_function(mnemonic="clc")
cld = CLD = _create_a_function(mnemonic="cld")
cli = CLI = _create_a_function(mnemonic="cli")
clv = CLV = _create_a_function(mnemonic="clv")
cmp = CMP = _create_a_function(mnemonic="cmp")
cpx = CPX = _create_a_function(mnemonic="cpx")
cpy = CPY = _create_a_function(mnemonic="cpy")
dcp = DCP = _create_a_function(mnemonic="dcp")
dec = DEC = _create_a_function(mnemonic="dec")
dex = DEX = _create_a_function(mnemonic="dex")
dey = DEY = _create_a_function(mnemonic="dey")
eor = EOR = _create_a_function(mnemonic="eor")
inc = INC = _create_a_function(mnemonic="inc")
inx = INX = _create_a_function(mnemonic="inx")
isc = ISC = _create_a_function(mnemonic="isc")
iny = INY = _create_a_function(mnemonic="iny")
jmp = JMP = _create_a_function(mnemonic="jmp")
jsr = JSR = _create_a_function(mnemonic="jsr")
lax = LAX = _create_a_function(mnemonic="lax")
lda = LDA = _create_a_function(mnemonic="lda")
ldx = LDX = _create_a_function(mnemonic="ldx")
ldy = LDY = _create_a_function(mnemonic="ldy")
lsr = LSR = _create_a_function(mnemonic="lsr")
nop = NOP = _create_a_function(mnemonic="nop")
ora = ORA = _create_a_function(mnemonic="ora")
pha = PHA = _create_a_function(mnemonic="pha")
php = PHP = _create_a_function(mnemonic="php")
pla = PLA = _create_a_function(mnemonic="pla")
plp = PLP = _create_a_function(mnemonic="plp")
rla = RLA = _create_a_function(mnemonic="rla")
rol = ROL = _create_a_function(mnemonic="rol")
ror = ROR = _create_a_function(mnemonic="ror")
rra = RRA = _create_a_function(mnemonic="rra")
rti = RTI = _create_a_function(mnemonic="rti")
rts = RTS = _create_a_function(mnemonic="rts")
sax = SAX = _create_a_function(mnemonic="sax")
sbc = SBC = _create_a_function(mnemonic="sbc")
sbx = SBX = _create_a_function(mnemonic="sbx")
sec = SEC = _create_a_function(mnemonic="sec")
sed = SED = _create_a_function(mnemonic="sed")
sei = SEI = _create_a_function(mnemonic="sei")
slo = SLO = _create_a_function(mnemonic="slo")
sre = SRE = _create_a_function(mnemonic="sre")
sta = STA = _create_a_function(mnemonic="sta")
stx = STX = _create_a_function(mnemonic="stx")
sty = STY = _create_a_function(mnemonic="sty")
tax = TAX = _create_a_function(mnemonic="tax")
tay = TAY = _create_a_function(mnemonic="tay")
tsx = TSX = _create_a_function(mnemonic="tsx")
txa = TXA = _create_a_function(mnemonic="txa")
txs = TXS = _create_a_function(mnemonic="txs")
tya = TYA = _create_a_function(mnemonic="tya")

