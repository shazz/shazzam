from shazzam.Cruncher import Cruncher
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a


class Exomizer(Cruncher):

    def __init__(self, exe_path: str):

        cmd_prg_template = [exe_path, 'sfx', 'basic',
                            "FILENAME_TO_SET", '-o', "OUTPUT_TO_SET"]
        cmd_bin_template = [exe_path, 'sfx',
                            "FILENAME_TO_SET", '-o', "OUTPUT_TO_SET"]

        super().__init__("exomizer", exe_path, cmd_prg_template, cmd_bin_template)

    def generate_depacker_routine(self, address: int) -> None:
        """generate_depacker_routine

        Args:
            address (int): [description]

        Raises:
            NotImplementedError: [description]
        """
        nop()
