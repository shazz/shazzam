from shazzam.defs import Alias, CodeFormat, CommentsFormat, DirectiveFormat, DirectiveDelimiter
from shazzam.Assembler import Assembler
from shazzam.Segment import Segment
from shazzam.Program import Program

import subprocess
import os
from typing import List


class C64jasm(Assembler):

    def __init__(self, name: str, exe_path: str):
        super().__init__(name, exe_path)

    def get_code_segment_address(self) -> str:
        raise NotImplementedError()

    def get_code_segment(self) -> str:
        return "CODE"

    def get_data_segment(self) -> str:
        raise NotImplementedError()

    def get_bss_segment(self) -> str:
        raise NotImplementedError()

    def get_code_format(self):
        """get_code_format

        Returns:
            [type]: [description]
        """
        return Alias({
            # "code": [CodeFormat.USE_HEX, CodeFormat.SHOW_LABELS],
            "code": [CodeFormat.USE_HEX, CodeFormat.CYCLES],
            "comments": CommentsFormat.USE_SEMICOLON,
            "directive": DirectiveFormat.USE_EXCLAMATION,
            "delimiter": DirectiveDelimiter.NO_DELIMITER
        })

    def assemble_segment(self, program: Program, segment: Segment) -> str:
        """assemble_segment

        Args:
            segment (Segment): [description]

        Returns:
            str: [description]
        """
        segment_filename = f'generated/{program.name}/{segment.name}.o'
        raise NotImplementedError()

        return segment_filename

    def assemble_prg(self, program: Program, start_address: int) -> str:
        """assemble

        Args:
            program ([type]): [description]
            start_address (int): [description]
        """
        program_filename = f'generated/{program.name}/{program.name}.prg'

        # calling c64jasm
        # cmd = ["node", self.path, '--disasm-file', f'generated/{program.name}/{program.name}.lst', '--labels-file', f'generated/{program.name}/{program.name}.labels', '--out', program_filename]
        cmd = [self.path, '--disasm-file', f'generated/{program.name}/{program.name}.lst', '--labels-file', f'generated/{program.name}/{program.name}.labels', '--out', program_filename]

        for segment in program.segments:
            cmd.append(f"generated/{program.name}/{segment.name}.asm")

        self.logger.info(f"Assembling {program.name} using c64jasm command: {cmd}")
        data = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_data, stderr_data = data.communicate()

        print(stdout_data.decode('utf-8'))

        if len(stderr_data) > 1:
            self.logger.error(stderr_data.decode('utf-8'))
        else:
            self.logger.info(f"{program_filename} ({os.path.getsize(program_filename)} bytes) assembled and linked")

        return program_filename

    def segments_definition_gen(self, segments: List[Segment]):

        code = ""
        for segment in segments:
            code += f"!segment {segment.name}(start=${segment.start_adr:04X}, end=${segment.end_adr:04X})\n"

        return code

