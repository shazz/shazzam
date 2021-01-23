import subprocess
import os
import logging

from shazzam.Cruncher import Cruncher

class Nucrunch(Cruncher):

    def __init__(self, exe_path: str):

        cmd_prg_template = [exe_path, '-cbxo', "OUTPUT_TO_SET", "FILENAME_TO_SET" ]
        cmd_bin_template = [exe_path, '-cxo', "OUTPUT_TO_SET", "FILENAME_TO_SET" ]
        super().__init__("nucrucnh", exe_path, cmd_prg_template, cmd_bin_template)

    def generate_depacker_routine(self, address: int) -> None:
        """generate_depacker_routine

        Args:
            address (int): [description]

        Raises:
            NotImplementedError: [description]
        """
        with segment(address, "depacker") as s:
            nop()
            raise NotImplementedError()

