from shazzam.Cruncher import Cruncher
from shazzam.py64gen import RegisterACC as a
from shazzam.py64gen import RegisterX as x
from shazzam.py64gen import RegisterY as y
from shazzam.py64gen import *


class Nucrunch(Cruncher):

    def __init__(self, exe_path: str):

        cmd_prg_template = [exe_path, '-cbxo',
                            "OUTPUT_TO_SET", "FILENAME_TO_SET"]
        cmd_bin_template = [exe_path, '-cxo',
                            "OUTPUT_TO_SET", "FILENAME_TO_SET"]
        super().__init__("nucrucnh", exe_path, cmd_prg_template, cmd_bin_template)

    def generate_depacker_routine(self, address: int) -> None:
        """generate_depacker_routine

        Args:
            address (int): [description]

        Raises:
            NotImplementedError: [description]
        """
        nop()
