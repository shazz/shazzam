from time import sleep
from contextlib import contextmanager
import hashlib
import os
import dill

from reloading import reloading

import shazzam.globals as g
from shazzam.Instruction import Instruction
from shazzam.defs import *
from shazzam.Rasterline import Rasterline
from shazzam.Segment import Segment
from shazzam.Address import Address
from shazzam.Immediate import Immediate
from shazzam.Cruncher import Cruncher
from shazzam.Assembler import Assembler
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
def segment(start_adr: int, name: str, use_relative_addressing: bool = False, check_address_dups: bool = True) -> Segment:
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

    seg = Segment(start_adr=start_adr, name=name.upper(), use_relative_addressing=use_relative_addressing)
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

def gen_code(header: str = None, prefs: Alias = None) -> None:
    """[summary]

    Args:
        header (str, optional): [description]. Defaults to None.
    """
    global _PROGRAM

    overlaps = _check_segments_ovelap()

    if header is None:
        header  = "; Generated code using Shazzam py64gen\n"
        header += "; Copyright (C) 2021 TRSi\n"
        header += "; \n"
        header += "; https://github.com/shazz/shazzam\n\n"

    if prefs:
        g.logger.debug(f"Setting assembler pref: {prefs}")
        set_prefs(default_code_segment=prefs.default_code_segment, code_format=prefs.code, comments_format=prefs.comments, directive_prefix=prefs.directive)

    for segment in g._PROGRAM.segments:

        g.logger.debug(f"generating code for segment {segment.name} from {g._PROGRAM.segments}")
        segment.change_format()
        code = segment.gen_code()

        if code:
            os.makedirs(f"generated/{g._PROGRAM.name}", exist_ok = True)
            with open(f"generated/{g._PROGRAM.name}/{segment.name}.asm", "w") as f:
                f.writelines(header)
                f.writelines(code)

def gen_listing(header: str = None) -> None:
    """[summary] gen_listing

    Args:
        header (str, optional): [description]. Defaults to None.
    """
    global _PROGRAM

    if header is None:
        header  = "; Generated listing using Shazzam py64gen\n"
        header += "; Copyright (C) 2021 TRSi\n"
        header += "; \n"
        header += "; https://github.com/shazz/shazzam\n\n"

    prefs = Alias( {
            "default_code_segment": "CODE",
            "code": [CodeFormat.USE_HEX, CodeFormat.BYTECODE, CodeFormat.ADDRESS, CodeFormat.SHOW_LABELS],
            "comments": CommentsFormat.USE_SEMICOLON,
            "directive": DirectiveFormat.USE_DOT
        })
    set_prefs(default_code_segment=prefs.default_code_segment, code_format=prefs.code, comments_format=prefs.comments, directive_prefix=prefs.directive)

    for segment in g._PROGRAM.segments:

        segment.change_format()
        code = segment.gen_code()

        if code:
            os.makedirs(f"generated/{g._PROGRAM.name}", exist_ok = True)
            with open(f"generated/{g._PROGRAM.name}/{segment.name}.lst", "w") as f:
                f.writelines(header)
                f.writelines(code)

def assemble_segment(assembler: Assembler) -> None:
    """Assemble segment

    Args:
        assembler ([type]): [description]
        cruncher (None): [description]
    """
    global _CURRENT_CONTEXT, _PROGRAM

    if g._CURRENT_CONTEXT is None:
        raise RuntimeError(f"No segment defined!")

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
            g.logger.error(f"The cruncher class {cruncher.__class__} needs to implement crunch_prg()!")
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

    #TODO: how to make this works if a segment is defined after this call ?
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

    for segment in _PROGRAM:

        if code:
            raise NotImplementedError()

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
        g.logger.debug(f"Relative address: {value:04X} - ({get_current_address():04X}+2) = {rel_address:04X}")

        if rel_address > 0xff:
            raise ValueError(f"Relative address cannot be bigger than a byte: {get_current_address():04X} - {value:04X} = {rel_address:04X}")

        return Address(value=value, relative=rel_address)
    else:
        raise ValueError("Relative address must be an int or a non empty string")

def imm(value: Any) -> Immediate:
    if isinstance(value, str):
        if value.startswith('>'):
            return Immediate(name=value[1:], high_byte=True)
        elif value.startswith('<'):
            return Immediate(name=value[1:], high_byte=False)
        else:
            raise ValueError(f"Low byte (<) or High byte (>) must be specified. Not {value}")

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
        raise RuntimeError(f"No segment defined!")

    if name == None or len(name) == 0:
        raise ValueError(f"Label cannot be empty")

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
        raise RuntimeError(f"No segment defined!")

    return g._CURRENT_CONTEXT.get_anonymous_label(name)

def byte(value: Any) -> bytearray:

    global _CURRENT_CONTEXT
    if g._CURRENT_CONTEXT is None:
        raise RuntimeError(f"No segment defined!")

    bcode = None
    if isinstance(value, str):
        if value.startswith('>'):
            return g._CURRENT_CONTEXT.add_byte(Immediate(name=value[1:], high_byte=True))
        elif value.startswith('<'):
            return g._CURRENT_CONTEXT.add_byte(Immediate(name=value[1:], high_byte=False))
        else:
            g.logger.warning(f"Low byte (<) or High byte (>) not specified. Considering this is a character string")

            ret_array = []
            for v in value:
                ret_array.append(g._CURRENT_CONTEXT.add_byte(Immediate(value=ord(v))))

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
        raise RuntimeError(f"No segment defined!")

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
        raise RuntimeError(f"No segment defined!")

    if data is not None:
        if not isinstance(data, bytearray):
            raise ValueError(f"incbin argument muust be a bytearray and not a {type(data)}")

        for b in data:
            g._CURRENT_CONTEXT.add_byte(Immediate(value=b))

def get_current_address() -> int:

    global _CURRENT_CONTEXT
    if g._CURRENT_CONTEXT is None:
        raise RuntimeError(f"No segment defined!")

    return g._CURRENT_CONTEXT.next_position

# ---------------------------------------------------------------------
# Utils
# ---------------------------------------------------------------------
_funcs = {}
def generate(func, program_name: str) -> None:
    """[summary]

    Args:
        func ([type]): [description]
    """
    global _PROGRAM
    g._PROGRAM.set_name(program_name)

    for i in reloading(range(10)):
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
        raise ValueError(f"Opcode can't have more than 2 operands!")

    def function_template(*args, **kwargs):

        global _CURRENT_CONTEXT
        if g._CURRENT_CONTEXT is None:
            raise RuntimeError(f"No segment defined!")

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
                raise ValueError(f"1st operand must be an Address or an Immediate, not a {type(args[0])}")

        if len(args) == 2:
            index = args[1]
            if not isinstance(index, enum.EnumMeta):
                raise ValueError(f"2nd operand must be a Register and not a {type(index)}")

        if len(args) > 2:
            raise ValueError(f"Too many arguments!")

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
                    adr = g._CURRENT_CONTEXT.need_label(address.name)
                    return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'abx', address=address))

            if 'aby' in modes and index is RegisterY and not address.indirect:
                if address.value is not None:
                    if 'zpy' in modes and address.value < 0x100:
                        return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'zpy', address=address))
                    elif address.value > 0x100:
                        return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'aby', address=address))
                else:
                    adr = g._CURRENT_CONTEXT.need_label(address.name)
                    return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'aby', address=address))

            if 'abs' in modes and index is None and address and not address.indirect:
                if address.value is not None:
                    if 'zpg' in modes and address.value < 0x100:
                        return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'zpg', address=address))
                    elif address.value >= 0x100:
                        return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'abs', address=address))
                else:
                    adr = g._CURRENT_CONTEXT.need_label(address.name)
                    return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'abs', address=address))

            if 'rel' in modes:
                if address.relative is not None:
                    return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'rel', address=address))
                else:
                    adr = g._CURRENT_CONTEXT.need_label(address.name)
                    return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'rel', address=address))

            if 'imm' in modes and immediate is not None:
                if immediate.value is None:
                    adr = g._CURRENT_CONTEXT.need_label(immediate.name)
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
                if address.value :
                    return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'ind', address=address))
                else:
                    adr = g._CURRENT_CONTEXT.need_label(address.name)
                    return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'ind', address=address))
        except Exception as e:
            import inspect
            callerframerecord = inspect.stack()[1]    # 0 represents this line,  1 represents line at caller

            frame = callerframerecord[0]
            info = inspect.getframeinfo(frame)
            print(info)

            raise

        raise NotImplementedError(f"No condition for {mnemonic} and args: {args}. Possible modes: {modes}")

    return function_template

# ---------------------------------------------------------------------
# Opcodes wrappers
# ---------------------------------------------------------------------


g.initialize()

ADC	= _create_a_function(mnemonic="adc")
AND = _create_a_function(mnemonic="and")
ASL	= _create_a_function(mnemonic="asl")
BCC	= _create_a_function(mnemonic="bcc")
BCS	= _create_a_function(mnemonic="bcs")
BEQ	= _create_a_function(mnemonic="beq")
BIT	= _create_a_function(mnemonic="bit")
BMI	= _create_a_function(mnemonic="bmi")
BNE	= _create_a_function(mnemonic="bne")
BPL	= _create_a_function(mnemonic="bpl")
BRK	= _create_a_function(mnemonic="brk")
BVC	= _create_a_function(mnemonic="bvc")
BVS	= _create_a_function(mnemonic="bvs")
CLC	= _create_a_function(mnemonic="clc")
CLD	= _create_a_function(mnemonic="cld")
CLI	= _create_a_function(mnemonic="cli")
CLV	= _create_a_function(mnemonic="clv")
CMP	= _create_a_function(mnemonic="cmp")
CPX	= _create_a_function(mnemonic="cpx")
CPY	= _create_a_function(mnemonic="cpy")
DEC	= _create_a_function(mnemonic="dec")
DEX	= _create_a_function(mnemonic="dex")
DEY	= _create_a_function(mnemonic="dey")
EOR	= _create_a_function(mnemonic="eor")
INC	= _create_a_function(mnemonic="inc")
INX	= _create_a_function(mnemonic="inx")
INY	= _create_a_function(mnemonic="iny")
JMP	= _create_a_function(mnemonic="jmp")
JSR	= _create_a_function(mnemonic="jsr")
LDA	= _create_a_function(mnemonic="lda")
LDX	= _create_a_function(mnemonic="ldx")
LDY	= _create_a_function(mnemonic="ldy")
LSR	= _create_a_function(mnemonic="lsr")
NOP	= _create_a_function(mnemonic="nop")
ORA	= _create_a_function(mnemonic="ora")
PHA	= _create_a_function(mnemonic="pha")
PHP	= _create_a_function(mnemonic="php")
PLA	= _create_a_function(mnemonic="pla")
PLP	= _create_a_function(mnemonic="plp")
ROL	= _create_a_function(mnemonic="rol")
ROR	= _create_a_function(mnemonic="ror")
RTI	= _create_a_function(mnemonic="rti")
RTS	= _create_a_function(mnemonic="rts")
SBC	= _create_a_function(mnemonic="sbc")
SEC	= _create_a_function(mnemonic="sec")
SED	= _create_a_function(mnemonic="sed")
SEI	= _create_a_function(mnemonic="sei")
STA	= _create_a_function(mnemonic="sta")
STX	= _create_a_function(mnemonic="stx")
STY	= _create_a_function(mnemonic="sty")
TAX	= _create_a_function(mnemonic="tax")
TAY	= _create_a_function(mnemonic="tay")
TSX	= _create_a_function(mnemonic="tsx")
TXA	= _create_a_function(mnemonic="txa")
TXS	= _create_a_function(mnemonic="txs")
TYA	= _create_a_function(mnemonic="tya")

adc	= _create_a_function(mnemonic="adc")
andr = _create_a_function(mnemonic="and")
asl	= _create_a_function(mnemonic="asl")
bcc	= _create_a_function(mnemonic="bcc")
bcs	= _create_a_function(mnemonic="bcs")
beq	= _create_a_function(mnemonic="beq")
bit	= _create_a_function(mnemonic="bit")
bmi	= _create_a_function(mnemonic="bmi")
bne	= _create_a_function(mnemonic="bne")
bpl	= _create_a_function(mnemonic="bpl")
brk	= _create_a_function(mnemonic="brk")
bvc	= _create_a_function(mnemonic="bvc")
bvs	= _create_a_function(mnemonic="bvs")
clc	= _create_a_function(mnemonic="clc")
cld	= _create_a_function(mnemonic="cld")
cli	= _create_a_function(mnemonic="cli")
clv	= _create_a_function(mnemonic="clv")
cmp	= _create_a_function(mnemonic="cmp")
cpx	= _create_a_function(mnemonic="cpx")
cpy	= _create_a_function(mnemonic="cpy")
dec	= _create_a_function(mnemonic="dec")
dex	= _create_a_function(mnemonic="dex")
dey	= _create_a_function(mnemonic="dey")
eor	= _create_a_function(mnemonic="eor")
inc	= _create_a_function(mnemonic="inc")
inx	= _create_a_function(mnemonic="inx")
iny	= _create_a_function(mnemonic="iny")
jmp	= _create_a_function(mnemonic="jmp")
jsr	= _create_a_function(mnemonic="jsr")
lda	= _create_a_function(mnemonic="lda")
ldx	= _create_a_function(mnemonic="ldx")
ldy	= _create_a_function(mnemonic="ldy")
lsr	= _create_a_function(mnemonic="lsr")
nop	= _create_a_function(mnemonic="nop")
ora	= _create_a_function(mnemonic="ora")
pha	= _create_a_function(mnemonic="pha")
php	= _create_a_function(mnemonic="php")
pla	= _create_a_function(mnemonic="pla")
plp	= _create_a_function(mnemonic="plp")
rol	= _create_a_function(mnemonic="rol")
ror	= _create_a_function(mnemonic="ror")
rti	= _create_a_function(mnemonic="rti")
rts	= _create_a_function(mnemonic="rts")
sbc	= _create_a_function(mnemonic="sbc")
sec	= _create_a_function(mnemonic="sec")
sed	= _create_a_function(mnemonic="sed")
sei	= _create_a_function(mnemonic="sei")
sta	= _create_a_function(mnemonic="sta")
stx	= _create_a_function(mnemonic="stx")
sty	= _create_a_function(mnemonic="sty")
tax	= _create_a_function(mnemonic="tax")
tay	= _create_a_function(mnemonic="tay")
tsx	= _create_a_function(mnemonic="tsx")
txa	= _create_a_function(mnemonic="txa")
txs	= _create_a_function(mnemonic="txs")
tya	= _create_a_function(mnemonic="tya")

# -----------------------------------------------------------
# Private functions
# -----------------------------------------------------------

def _check_segments_ovelap(code_segment: str = "CODE") -> None:

    intervals = []
    for segment in g._PROGRAM.segments:
        if segment.name == code_segment:
            intervals.append((segment.start_adr, segment.end_adr+13))   # adding basic header 13 bytes
        else:
            intervals.append((segment.start_adr, segment.end_adr))

    intervals.sort()
    g.logger.info(f"Checking overlapping intervals: {[(hex(interval[0]), hex(interval[1])) for interval in intervals]}")

    for i in range(1, len(intervals)):
        if intervals[i][0] <= intervals[i-1][1]:
            raise ValueError(f"The segments {g._PROGRAM.segments[i-1].name} and {g._PROGRAM.segments[i].name} overlap!")


