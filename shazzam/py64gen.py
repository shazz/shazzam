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
from shazzam.Cruncher import Cruncher
from shazzam.Assembler import Assembler

from typing import List


# ---------------------------------------------------------------------
# py64gen public functions
# ---------------------------------------------------------------------
def set_prefs(code_format: List[CodeFormat], comments_format: CommentsFormat, directive_prefix: DirectiveFormat):
    global _CODE_FORMAT, _COMMENTS_FORMAT, _DIRECTIVE_PREFIX

    g._CODE_FORMAT = code_format
    g._COMMENTS_FORMAT = comments_format
    g._DIRECTIVE_PREFIX = directive_prefix

@contextmanager
def segment(start_adr: int, name: str, use_relative_addressing: bool = False) -> Segment:
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

    seg = Segment(start_adr=start_adr, name=name, use_relative_addressing=use_relative_addressing)
    g._CURRENT_CONTEXT = seg

    yield seg

    found = False
    for segment in g._PROGRAM.segments:
        if segment.start_adr == start_adr:
            found = True

            g._PROGRAM.segments.remove(segment)
            g._PROGRAM.segments.append(seg)

            break

    if not found:
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

def gen_code(prg_name: str, header: str = None) -> None:
    """[summary]

    Args:
        header (str, optional): [description]. Defaults to None.
    """
    global _PROGRAM

    g._PROGRAM.set_name(prg_name)

    if header is None:
        header  = "; Generated code using Shazzam py64gen\n"
        header += "; Copyright (C) 2021 TRSi\n"
        header += "; \n"
        header += "; https://github.com/shazz/shazzam\n\n"

    for segment in g._PROGRAM.segments:

        code = segment.gen_code()

        if code:
            os.makedirs(f"generated/{g._PROGRAM.name}", exist_ok = True)
            with open(f"generated/{g._PROGRAM.name}/{segment.name}.asm", "w") as f:
                f.writelines(header)
                f.writelines(code)

def assemble_segment(assembler: Assembler, cruncher: Cruncher = None) -> None:
    """Assemble segment

    Args:
        assembler ([type]): [description]
        cruncher (None): [description]
    """
    global _CURRENT_CONTEXT

    output_file = assembler.assemble_segment(_CURRENT_CONTEXT)

    if cruncher is not None:
        try:
            cruncher.crunch_incbin(output_file)
        except AttributeError as e:
            g.logger.error(f"The cruncher class {cruncher.__class__} needs to implement crunch_incbin()!")
            g.logger.error(e)

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

def gen_sparkle_script():
    """[summary]

    Raises:
        NotImplementedError: [description]
    """
    global _PROGRAM

    for segment in _PROGRAM:

        code = segment.gen_code()
        if code:
            raise NotImplementedError()

# ---------------------------------------------------------------------
# Assembler directives
# ---------------------------------------------------------------------
def label(name: str, is_global: bool = False):
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

    seg_label_address = g._CURRENT_CONTEXT.add_label(name)

    if is_global:
        g._PROGRAM.add_label(name, seg_label_address)
        print(g._PROGRAM.global_labels)

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

def byte(value: int = None, values: [] = None, label: str = None) -> bytearray:
    """byte assembler directive

    Args:
        value (int, optional): [description]. Defaults to None.
        values ([type], optional): [description]. Defaults to None.
        label (str, optional): [description]. Defaults to None.

    Raises:
        RuntimeError: [description]
        ValueError: [description]

    Returns:
        bytearray: [description]
    """
    global _CURRENT_CONTEXT
    if g._CURRENT_CONTEXT is None:
        raise RuntimeError(f"No segment defined!")

    if value and value > 0xff:
        raise ValueError(f"Value exceed byte size: {value}")
    else:
        return g._CURRENT_CONTEXT.add_byte(value, label)

    if values:
        ret_array = []
        for value in values:
            if value > 0xff:
                raise ValueError(f"Value exceed byte size: {value}")
            ret_array.append(g._CURRENT_CONTEXT.add_byte(value, label))
        return bytearray(ret_array)


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

    for b in data:
        g._CURRENT_CONTEXT.add_byte(b)


# ---------------------------------------------------------------------
# Utils
# ---------------------------------------------------------------------
_funcs = {}
def generate(func) -> None:
    """[summary]

    Args:
        func ([type]): [description]
    """
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

        sleep(0.5)
    generate(func)

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
    for opcode in Instruction.opcodes:
        if opcode[0] == mnemonic:
            modes.append(opcode[1])

    def function_template(*args, **kwargs):

        global _CURRENT_CONTEXT
        if g._CURRENT_CONTEXT is None:
            raise RuntimeError(f"No segment defined!")

        label       = kwargs['label'] if 'label' in kwargs else None
        imm         = kwargs['imm'] if 'imm' in kwargs else None
        rel_adr     = kwargs['rel_adr'] if 'rel_adr' in kwargs else None
        abs_adr     = kwargs['abs_adr'] if 'abs_adr' in kwargs else None
        index       = kwargs['index'] if 'index' in kwargs else None
        ind_adr     = kwargs['ind_adr'] if 'ind_adr' in kwargs else None

        if label and label == "":
            raise ValueError("Label cannot be empty")

        g.logger.debug(f"Adding conditions for modes: {modes}")

        if 'zpx' in modes and index is Register.X:
            if label:
                adr = g.g._CURRENT_CONTEXT.need_label(label)
                return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'zpx', label=label))
            elif abs_adr is not None:
                if abs_adr < 0x100:
                   return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'zpx', abs_adr))

        if 'zpy' in modes and index is Register.Y:
            if label:
                adr = g._CURRENT_CONTEXT.need_label(label)
                return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'zpy', label=label))
            elif abs_adr is not None:
                if abs_adr < 0x100:
                   return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'zpy', abs_adr))

        if 'abx' in modes and index is Register.X:
            if label:
                adr = g._CURRENT_CONTEXT.need_label(label)
                return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'abx', label=label))
            elif abs_adr is not None:
                if 'zpx' in modes and abs_adr < 0x100:
                   return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'zpx', abs_adr))
                else:
                   return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'abx', abs_adr))

        if 'aby' in modes and index is Register.Y:
            if label:
                adr = g._CURRENT_CONTEXT.need_label(label)
                return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'aby', label=label))
            elif abs_adr is not None:
                if 'zpy' in modes and abs_adr < 0x100:
                   return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'zpy', abs_adr))
                else:
                   return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'aby', abs_adr))

        if 'abs' in modes and index is None:
            if label:
                adr = g._CURRENT_CONTEXT.need_label(label)
                return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'abs', label=label))
            elif abs_adr is not None:
                if 'zpg' in modes and abs_adr < 0x100:
                   return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'zpg', value=abs_adr))
                else:
                   return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'abs', value=abs_adr))

        if 'rel' in modes:
            if rel_adr is not None:
                return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'rel', value=rel_adr))
            else:
                return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'rel', label=label))

        if 'imm' in modes and imm is not None:
             return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'imm', value=imm))

        if 'imp' in modes:
             return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'imp'))

        if 'iix' in modes and ind_adr is not None and index is Register.X:
            if label:
                adr = g._CURRENT_CONTEXT.need_label(label)
                return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'iix', label=label))
            elif ind_adr is not None:
                return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'iix', value=ind_adr))

        if 'iiy' in modes and ind_adr is not None and index is Register.Y:
            if label:
                adr = g._CURRENT_CONTEXT.need_label(label)
                return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'iiy', label=label))
            elif ind_adr is not None:
                return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'iiy', value=ind_adr))

        if 'acc' in modes and index is Register.A:
             return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'acc'))

        if 'ind' in modes:
            if label:
                adr = g._CURRENT_CONTEXT.need_label(label)
                return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'ind', label=label))
            elif ind_adr is not None:
                return g._CURRENT_CONTEXT.add_instruction(Instruction(mnemonic, 'ind', value=ind_adr))

        raise NotImplementedError(f"No condition for {mnemonic} and args: {kwargs}. Possible modes: {modes}")

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

