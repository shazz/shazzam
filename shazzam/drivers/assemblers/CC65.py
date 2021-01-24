from shazzam.defs import *
from shazzam.Assembler import Assembler
from shazzam.Segment import Segment
from shazzam.Program import Program

import subprocess
import os
import logging

class CC65(Assembler):

    features = \
"""FEATURES {
    STARTADDRESS: default = %%;
}
"""

    symbols = \
"""SYMBOLS {
    __LOADADDR__: type = import;
}
"""

    memory = \
"""MEMORY {
    ZP:       file = "", start = $0002,  size = $00FE,      define = yes;
    LOADADDR: file = %O, start = %S - 2, size = $0002;
    MAIN:     file = %O, start = %S,     size = %%% - %S,   fill = yes;
%%
}
"""

    segments = \
"""SEGMENTS {
    ZEROPAGE: load = ZP,       type = zp,  optional = yes;
    LOADADDR: load = LOADADDR, type = ro;
    EXEHDR:   load = MAIN,     type = ro,  optional = yes;
    CODE:     load = MAIN,     type = rw;
    DATA:     load = MAIN,     type = rw,  optional = yes;
    BSS:      load = MAIN,     type = bss, optional = yes, define = yes;
%%
}
"""

    basic_header_size = 13

    def __init__(self, name: str, exe_path: str):
        super().__init__(name, exe_path)

    def get_code_segment(self) -> str:
        """get_code_segment

        Returns:
            str: [description]
        """
        return "CODE"

    def get_data_segment(self) -> str:
        """get_data_segment

        Returns:
            str: [description]
        """
        return "DATA"

    def get_bss_segment(self) -> str:
        """get_bss_segment

        Returns:
            str: [description]
        """
        return "BSS"

    def get_code_format(self):
        """get_code_format

        Returns:
            [type]: [description]
        """
        return Alias( {
            # "code": [CodeFormat.USE_HEX, CodeFormat.SHOW_LABELS],
            "code": [CodeFormat.USE_HEX],
            "comments": CommentsFormat.USE_SEMICOLON,
            "directive": DirectiveFormat.USE_DOT
        })

    def assemble_segment(self, program: Program, segment: Segment) -> str:
        """assemble_segment

        Args:
            segment (Segment): [description]

        Returns:
            str: [description]
        """
        segment_filename = f'generated/{program.name}/{segment.name}.o'

        # seg_lines
        cmd = [self.path, '-t', 'c64', f"generated/{program.name}/{segment.name}.asm"]

        cmd.append('-o')
        cmd.append(segment_filename)

        self.logger.info(f"Assembling {segment.name} segment using CL65 command: {cmd}")
        data = subprocess.Popen(cmd, stdout = subprocess.PIPE)
        output = data.communicate()

        return segment_filename

    def assemble_prg(self, program: Program, start_address: int) -> str:
        """assemble

        Args:
            program ([type]): [description]
            start_address (int): [description]
        """
        program_filename = f'generated/{program.name}/{program.name}.prg'

        self.generate_config(start_address, program)

        # seg_lines
        cmd = [self.path, '-t', 'c64', '-C', f'generated/{program.name}/gen-c64-asm.cfg', '-u', '__EXEHDR__']
        for segment in program.segments:
            cmd.append(f"generated/{program.name}/{segment.name}.asm")

        cmd.append('-o')
        cmd.append(program_filename)

        # cl65 -t c64 -C generated/c64-asm.cfg -u __EXEHDR__ generated/entry.asm generated/INIT.asm generated/IRQ.asm -o main.prg
        self.logger.info(f"Assembling {segment.name} using CL65 command: {cmd}")
        data = subprocess.Popen(cmd, stdout = subprocess.PIPE)
        output = data.communicate()

        return program_filename

    def generate_config(self, start_address, program):
        """generate_config

        Args:
            start_address ([type]): [description]
            program ([type]): [description]

        Raises:
            RuntimeError: [description]
        """
        # gen features
        CC65.features = CC65.features.replace("%%", f"${start_address:04X}")

        # gen memory
        entry_point_found = False
        for i, segment in enumerate(program.segments):
            if segment.name in ["CODE", "DATA", "BSS"]:
                entry_point_found = True

        if entry_point_found is False:
            raise RuntimeError(f"Entry point in CODE, DATA or BSS segment not found!")

        # find segment next to BASIC header
        sorted_segments_adr = sorted([segment.start_adr for segment in program.segments])

        if len(sorted_segments_adr) > 1:
            first_segment_address = sorted_segments_adr[sorted_segments_adr.index(start_address)+1]
            CC65.memory = CC65.memory.replace("%%%", f"${first_segment_address:04X}")
        else:
            main_size = start_address + CC65.basic_header_size + (program.segments[0].size)
            self.logger.info(f"Only one CODE segment of size: {program.segments[0].size} + {CC65.basic_header_size} + 0x{start_address:04X} = {main_size:04X}")
            CC65.memory = CC65.memory.replace("%%%", f"${main_size:04X}")

        mem_lines = ""
        for i, segment in enumerate(program.segments):
            if segment.name not in ["CODE", "DATA", "BSS"]:
                if i < len(program.segments)-1:
                    seg_size = program.segments[i+1].start_adr - segment.start_adr
                else:
                    seg_size = segment.end_adr-segment.start_adr

                mem_lines += f"\t{segment.name}:\tfile = %O, start = ${segment.start_adr:04X},      size = ${seg_size:04X},    fill = yes;\n"

        self.logger.debug(f"Adding lines: {mem_lines}")
        CC65.memory = CC65.memory.replace("%%", mem_lines)

        # gen segments
        seg_lines = ""
        for segment in program.segments:
            if segment.name not in ["CODE", "DATA", "BSS"]:
                seg_lines += f"\t{segment.name}:\tload = {segment.name},\ttype = rw, optional = no, define = yes;\n"

        self.logger.debug(f"Adding lines: {seg_lines}")
        CC65.segments = CC65.segments.replace("%%", seg_lines)

        with open(f"generated/{program.name}/gen-c64-asm.cfg", "w") as f:
            f.write(CC65.features   )
            f.write(CC65.symbols)
            f.write(CC65.memory)
            f.write(CC65.segments)

        self.logger.info("CC65 configuration files written")


