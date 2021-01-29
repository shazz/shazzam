from shazzam.defs import Alias, CodeFormat, CommentsFormat, DirectiveFormat
from shazzam.Assembler import Assembler
from shazzam.Segment import Segment
from shazzam.Program import Program

import subprocess
import os
from typing import List


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
        return Alias({
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
        cmd = [self.path, '-t', 'c64',
               f"generated/{program.name}/{segment.name}.asm"]

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

        self.generate_config(start_address, program)

        # seg_lines
        cmd = [self.path, '-v', '-g', '-d', '-t', 'c64', '-C',
               f'generated/{program.name}/gen-c64-asm.cfg', '-u', '__EXEHDR__']
        for segment in program.segments:
            cmd.append(f"generated/{program.name}/{segment.name}.asm")

        cmd.append('-o')
        cmd.append(program_filename)

        # cl65 -t c64 -C generated/c64-asm.cfg -u __EXEHDR__ generated/entry.asm generated/INIT.asm generated/IRQ.asm -o main.prg
        self.logger.info(
            f"Assembling {program.name} using CL65 command: {cmd}")
        data = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_data, stderr_data = data.communicate()

        if len(stderr_data) > 1:
            self.logger.error(stderr_data)
        else:
            self.logger.info(
                f"{program_filename} ({os.path.getsize(program_filename)} bytes) assembled and linked")

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
        non_default_segments = []
        default_segments = []
        for i, segment in enumerate(program.segments):
            if segment.name in ["CODE", "DATA", "BSS"]:
                entry_point_found = True
                default_segments.append(segment)
            else:
                non_default_segments.append(segment)

        if entry_point_found is False:
            raise RuntimeError("Entry point in CODE, DATA or BSS segment not found!")

        # find segment next to BASIC header
        sorted_non_default_segments_adr = sorted(
            [segment.start_adr for segment in non_default_segments])
        sorted_default_segments_adr = sorted(
            [segment.start_adr for segment in default_segments])

        all_segments_adr = sorted(
            sorted_non_default_segments_adr + sorted_default_segments_adr)

        if len(sorted_non_default_segments_adr) > 0:
            # TODO: test with node default entry point
            # first_segment_address = sorted_non_default_segments_adr[sorted_non_default_segments_adr.index(start_address)+1]
            first_segment_address = sorted_non_default_segments_adr[0]
            CC65.memory = CC65.memory.replace(
                "%%%", f"${first_segment_address:04X}")
        else:
            # start_adr = sorted_default_segments_adr[0]
            end_adr = sorted_default_segments_adr[-1]
            for segment in default_segments:
                end_adr = max(end_adr, segment.end_adr)

            self.logger.info("Adding basic header to default segment")
            end_adr += CC65.basic_header_size
            # main_size = start_address + CC65.basic_header_size + (program.segments[0].size)
            # main_size = end_adr - start_adr
            # self.logger.info(f"Only one CODE segment of size: {program.segments[0].size} + {CC65.basic_header_size} + 0x{start_address:04X} = {main_size:04X}")
            CC65.memory = CC65.memory.replace("%%%", f"${end_adr:04X}")

        mem_lines = ""

        self.logger.debug(
            f"Browsing segments by increasing addresses: {all_segments_adr}")
        for i, adr in enumerate(all_segments_adr):
            segment = self._get_segment_by_address(adr, program.segments)

            if segment.name not in ["CODE", "DATA", "BSS"]:
                if i != len(all_segments_adr)-1:
                    seg_size = self._get_segment_by_address(
                        all_segments_adr[i+1], program.segments).start_adr - segment.start_adr
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

        self.logger.debug(f"Adding lines in configuration: {seg_lines}")
        CC65.segments = CC65.segments.replace("%%", seg_lines)

        with open(f"generated/{program.name}/gen-c64-asm.cfg", "w") as f:
            f.write(CC65.features)
            f.write(CC65.symbols)
            f.write(CC65.memory)
            f.write(CC65.segments)

        self.logger.debug("CC65 configuration files written")

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
