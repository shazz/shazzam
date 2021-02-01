from shazzam.defs import Alias, CodeFormat, CommentsFormat, DirectiveFormat
from shazzam.Assembler import Assembler
from shazzam.Segment import Segment
from shazzam.Program import Program

import subprocess
import os
from typing import List


class CC65(Assembler):

    makefile = \
        """CA65   = ca65
CL65   = cl65
LD65   = ld65

APP = %1.prg

all: $(APP)

%1.prg: %2
	$(CL65) -v -g -d -t c64 --cpu 6502X -C gen-c64-asm.cfg%3 $^ -o $@

clean:
	rm -f *.o *.prg
"""
    symbols = \
        """SYMBOLS {
    __LOADADDR__: type = import;
}
"""

    memory = \
        """MEMORY {
    ZP:       file = "", start = $0002,  size = $00FE,      define = yes;
    LOADADDR: file = %O, start = %1 - 2, size = $0002;
%2
}
"""
    segments = \
        """SEGMENTS {
    ZEROPAGE: load = ZP,       type = zp,  optional = yes;
    LOADADDR: load = LOADADDR, type = ro;
%%
}
"""

    segments_main = \
"""    EXEHDR:   load = MAIN,     type = ro,  optional = yes;
    CODE:     load = MAIN,     type = rw;
    DATA:     load = MAIN,     type = rw,  optional = yes;
    BSS:      load = MAIN,     type = bss, optional = yes, define = yes;
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
        return Alias({
            # "code": [CodeFormat.USE_HEX, CodeFormat.SHOW_LABELS],
            "code": [CodeFormat.USE_HEX, CodeFormat.CYCLES],
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
        cmd = [self.path, '-t', 'c64', '--cpu', '6502X', f"generated/{program.name}/{segment.name}.asm"]

        cmd.append('-o')
        cmd.append(segment_filename)

        self.logger.info(
            f"Assembling {segment.name} segment using CL65 command: {cmd}")
        data = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        data.communicate()

        self.logger.info(f"{segment.name} assembled")

        return segment_filename

    def assemble_prg(self, program: Program, start_address: int) -> str:
        """assemble

        Args:
            program ([type]): [description]
            start_address (int): [description]
        """
        program_filename = f'generated/{program.name}/{program.name}.prg'

        self._generate_config(start_address, program)
        self._generate_makefile(program)

        # calling cl65
        try:
            self._get_segment_by_name(self.get_code_segment(), program.segments)
            cmd = [self.path, '-v', '-g', '-d', '-t', 'c64', '--cpu', '6502X', '-C', f'generated/{program.name}/gen-c64-asm.cfg', '-u', '__EXEHDR__']
        except ValueError:
            cmd = [self.path, '-v', '-g', '-d', '-t', 'c64', '--cpu', '6502X', '-C', f'generated/{program.name}/gen-c64-asm.cfg']

        for segment in program.segments:
            cmd.append(f"generated/{program.name}/{segment.name}.asm")

        cmd.append('-o')
        cmd.append(program_filename)

        self.logger.info(f"Assembling {program.name} using CL65 command: {cmd}")
        data = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_data, stderr_data = data.communicate()

        if len(stderr_data) > 1:
            self.logger.error(stderr_data)
        else:
            self.logger.info(f"{program_filename} ({os.path.getsize(program_filename)} bytes) assembled and linked")

        return program_filename

    def _generate_config(self, start_address, program):
        """_generate_config

        Args:
            start_address ([type]): [description]
            program ([type]): [description]

        Raises:
            RuntimeError: [description]
        """
        # sort segment by address
        sorted_adr = sorted([segment.start_adr for segment in program.segments])
        self.logger.info(f"Segments addresses: {[hex(adr) for adr in sorted_adr]}")

        # set load address that will be the 2 PRG first bytes
        seg = self._get_segment_by_address(sorted_adr[0], program.segments)
        CC65.memory = CC65.memory.replace("%1", f"${seg.start_adr:04X}")

        mem_lines = []
        for i, segment_adr in enumerate(sorted_adr):
            seg = self._get_segment_by_address(segment_adr, program.segments)

            self.logger.info(f"Checking memory for segment {seg.name}")
            if seg.name not in ["DATA", "BSS"]:
                if i != len(sorted_adr)-1:
                    seg_size = self._get_segment_by_address(sorted_adr[i+1], program.segments).start_adr - seg.start_adr
                else:
                    seg_size = seg.end_adr-seg.start_adr

                # check if default 0801 segment is defined
                if seg.name == 'CODE':
                    mem_lines.append(f"\tMAIN:\tfile = %O, start = ${seg.start_adr:04X},      size = ${seg_size:04X},    fill = yes;\n")
                else:
                    mem_lines.append(f"\t{seg.name}:\tfile = %O, start = ${seg.start_adr:04X},      size = ${seg_size:04X},    fill = yes;\n")

        self.logger.info(f"Adding lines: {mem_lines}")
        CC65.memory = CC65.memory.replace("%2", ''.join(mem_lines))

        # gen segments
        seg_lines = ""
        for seg in program.segments:
            if seg.name not in ["CODE", "DATA", "BSS"]:
                seg_lines += f"\t{seg.name}:\tload = {seg.name},\ttype = rw, optional = no, define = yes;\n"
            elif seg.name == 'CODE':
                seg_lines += CC65.segments_main
            else:
                self.logger.info(f"{seg.name} segment already managed")

        self.logger.debug(f"Adding lines in configuration: {seg_lines}")
        CC65.segments = CC65.segments.replace("%%", seg_lines)

        with open(f"generated/{program.name}/gen-c64-asm.cfg", "w") as f:
            f.write(CC65.symbols)
            f.write(CC65.memory)
            f.write(CC65.segments)

        self.logger.debug("CC65 configuration files written")

    def _generate_makefile(self, program):
        """_generate_makefile

        Args:
            program ([type]): [description]
        """
        makefile = CC65.makefile.replace("%1", program.name)

        asm_files = []
        for segment in program.segments:
            asm_files.append(f"{segment.name}.asm")

        makefile = makefile.replace("%2", ' '.join(asm_files))

        try:
            self._get_segment_by_name(self.get_code_segment(), program.segments)
            makefile = makefile.replace("%3", " -u __EXEHDR__")
        except ValueError:
            makefile = makefile.replace("%3", "")

        with open(f"generated/{program.name}/Makefile", "w") as f:
                f.write(makefile)

        self.logger.debug("CC65 Makefile file written")

    def _get_segment_by_address(self, address: int, segments: List[Segment]) -> Segment:
        """_get_segment_by_address

        Args:
            address (int): [description]
            segments (List[Segment]): [description]

        Raises:
            ValueError: [description]

        Returns:
            Segment: [description]
        """
        for segment in segments:
            if segment.start_adr == address:
                return segment

        raise ValueError(f"No Segment found starting at {address:04X}")

    def _get_segment_by_name(self, name: str, segments: List[Segment]) -> Segment:
        """[summary]

        Args:
            name (str): [description]
            segments (List[Segment]): [description]

        Raises:
            ValueError: [description]

        Returns:
            Segment: [description]
        """
        for segment in segments:
            if segment.name == name:
                return segment

        raise ValueError(f"No Segment found with name {name}")