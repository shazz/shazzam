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

    def crunch_prg(self, filename: str, extra_params: List = None) -> None:
        """Crunch program

        Args:
            filename (str): [description]
        """
        if self.prg_cmd is None:
            raise RuntimeError("Packer command line for PRG is not set!")

        output_filename = f"{os.path.splitext(filename)[0]}_packed.prg"
        self.prg_cmd[self.prg_cmd.index("FILENAME_TO_SET")] = filename
        self.prg_cmd[self.prg_cmd.index("OUTPUT_TO_SET")] = output_filename

        if extra_params and len(extra_params) > 0:
            self.prg_cmd[1:1] = extra_params


        self.logger.info(f"Crunching {filename} with {self.packer_name} command: {self.prg_cmd }")
        data = subprocess.Popen(self.prg_cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        stdout_data, stderr_data = data.communicate()

        err = stderr_data.decode()
        if "error" in err:
            self.logger.error(err)
            raise RuntimeError(f"Program cannot be packed due to: {err}")
        else:
            self.logger.info(f"{filename} packed to {os.path.getsize(output_filename)} bytes")


    def crunch_incbin(self, filename: str, extra_params: List = None) -> bytearray:
        """crunch_incbin

        Args:
            filename (str): [description]
            extra_params (List, optional): [description]. Defaults to None.

        Raises:
            RuntimeError: [description]
        """
        if self.incbin_cmd is None:
            raise RuntimeError("Packer command line for incbin is not set!")

        output_filename = f"{os.path.splitext(filename)[0]}.bin"

        self.incbin_cmd[self.incbin_cmd.index("FILENAME_TO_SET")] = filename
        self.incbin_cmd[self.incbin_cmd.index("OUTPUT_TO_SET")] = output_filename

        if extra_params and len(extra_params) > 0:
            self.prg_cmd[1:1] = extra_params

        self.logger.info(f"Crunching {filename} with {self.packer_name} command: {self.incbin_cmd }")
        data = subprocess.Popen(self.incbin_cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        stdout_data, stderr_data = data.communicate()

        # check packing ratio
        unpacked_size = os.path.getsize(filename)
        packed_size = os.path.getsize(output_filename)
        if packed_size >= unpacked_size:
            raise RuntimeError(f"Packing doesn't shrink the incbin. Size increased from {unpacked_size} to {packed_size} bytes")

        if len(stderr_data) > 1:
            self.logger.error(stderr_data.decode())
            raise RuntimeError(f"Segment cannot be packed due to: {stderr_data.decode()}")

        self.logger.info(f"{filename} was {unpacked_size} bytes, packed to {packed_size} bytes")
        with open(output_filename, "rb") as f:
            barr = f.read()

        return bytearray(barr)

    def generate_depacker_routine(self, address: int) -> None:
        pass



