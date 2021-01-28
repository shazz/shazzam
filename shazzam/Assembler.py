import logging

from shazzam.Segment import Segment


class Assembler():
    """
    This class defines the interface to be implemented by cross-assembler drivers.
    The default one is CC65.
    """

    def __init__(self, name: str, exe_path: str):
        self.path = exe_path
        self.logger = logging.getLogger("shazzam")
        self.name = name

    def get_code_segment(self) -> str:
        """get_code_segment

        Returns:
            str: [description]
        """
        pass

    def get_code_format(self):
        """get_code_format"""
        pass

    def assemble_segment(self, segment: Segment) -> str:
        """assemble_segment

        Args:
            segment (Segment): [description]

        Returns:
            str: [description]
        """
        pass

    def assemble_prg(self, program, start_address: int) -> str:
        """assemble_prg

        Args:
            program ([type]): [description]
            start_address (int): [description]

        Returns:
            str: [description]
        """
        pass
