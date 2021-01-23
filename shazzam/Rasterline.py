
from shazzam.defs import *
import shazzam.globals as g

import logging

class Rasterline():
    """Rasteline class"""
    def __init__(self, system: System = System.PAL, mode: DetectMode = DetectMode.MANUAL, nb_sprites: int = 8, y_pos: int = 0, y_scroll: int = 0):
        """[summary]

        Args:
            system (System, optional): [description]. Defaults to System.PAL.
            mode (DetectMode, optional): [description]. Defaults to DetectMode.MANUAL.
            nb_sprites (int, optional): [description]. Defaults to 8.
            y_pos (int, optional): [description]. Defaults to 0.
            y_scroll (int, optional): [description]. Defaults to 0.
        """
        self.mode = mode
        self.system = system
        self.logger = logging.getLogger("shazzam")

        if mode is DetectMode.MANUAL:
            self.nb_sprites = nb_sprites
            self.y_pos = y_pos
            self.y_scroll = y_scroll
        else:
            self.nb_sprites, self.y_pos, self.y_scroll = self._autodetect()

        self.used_cycles = 0

    def _compute_available_cycles(self):
        """[summary]

        Returns:
            [type]: [description]
        """
        # max cycles per rasterline, depends on PAL or NTSC
        max_cycles = self.system.value

        # DMA steal for sprites
        max_cycles -= self.nb_sprites*2

        # check for badline
        if (self.y_pos >= 0x30) and (self.y_pos <= 0xf7) and ((self.y_pos & 7) == self.y_scroll):
            max_cycles -= 40

        return max_cycles

    def _autodetect(self) -> None:
        """[summary]

        Raises:
            NotImplementedError: [description]
        """
        raise NotImplementedError()

    def add_cycles(self, cycles: int) -> None:
        """[summary]

        Args:
            cycles (int): [description]
        """
        self.used_cycles += cycles

    def close(self) -> None:
        """[summary]

        Raises:
            ValueError: [description]
        """
        max_cycles = self._compute_available_cycles()

        if self.used_cycles > max_cycles:
            raise ValueError(f"Too many cycles used in rasterline {self.y_pos }: {self.used_cycles} used on {max_cycles} available")
        elif self.used_cycles < max_cycles:
            self.logger.warning(f"{self.used_cycles} cycles used in rasterline {self.y_pos } on {max_cycles} available, {max_cycles-self.used_cycles} left")
