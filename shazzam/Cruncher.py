import logging
import subprocess
import os
from typing import List

from shazzam.Segment import Segment

class Cruncher():

    def __init__(self, packer_name, exe_path: str, prg_cmd: List, incbin_cmd: List):
        self.path = exe_path
        self.logger = logging.getLogger("shazzam")
        self.prg_cmd = prg_cmd
        self.incbin_cmd = incbin_cmd
        self.packer_name = packer_name

    def crunch_prg(self, filename: str) -> None:
        """Crunch program

        Args:
            filename (str): [description]
        """
        if self.prg_cmd is None:
            raise RuntimeError("Packer command line for PRG is not set!")

        self.prg_cmd[self.prg_cmd.index("FILENAME_TO_SET")] = filename
        self.prg_cmd[self.prg_cmd.index("OUTPUT_TO_SET")] = f"{os.path.splitext(filename)[0]}_packed.prg"

        self.logger.info(f"Crunching {filename} with {self.packer_name} command: {self.prg_cmd }")
        print("---------------------------------------------------------------")
        data = subprocess.Popen(self.prg_cmd, stdout = subprocess.PIPE)
        output = data.communicate()
        print("---------------------------------------------------------------")

    def crunch_incbin(self, payload: bytearray) -> None:
        """crunch_incbin

        Args:
            payload (bytearray): [description]
        """
        if self.incbin_cmd is None:
            raise RuntimeError("Packer command line for PRG is not set!")

        self.incbin_cmd[self.incbin_cmd.index("FILENAME_TO_SET")] = filename
        self.incbin_cmd[self.incbin_cmd.index("OUTPUT_TO_SET")] = f"{os.path.splitext(filename)[0]}.bin"

        self.logger.info(f"Crunching {filename} with {self.packer_name} command: {self.incbin_cmd }")
        print("---------------------------------------------------------------")
        data = subprocess.Popen(self.incbin_cmd, stdout = subprocess.PIPE)
        output = data.communicate()
        print("---------------------------------------------------------------")

    def generate_depacker_routine(self, address: int) -> None:
        pass



