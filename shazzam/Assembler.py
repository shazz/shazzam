import logging
from typing import List

from shazzam.Segment import Segment


class Assembler():
    """
    This class defines the interface to be implemented by cross-assembler drivers.
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

    def support_basic(self):
        """[summary]

        Returns:
            [type]: [description]
        """
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

    def segments_definition_gen(self, segments: List[Segment]) -> str:
        """[summary]

        Args:
            segments (List[Segment]): [description]

        Returns:
            str: [description]
        """
        return ""

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
