from shazzam.optimizer.MemorySegment import MemorySegment
from shazzam.optimizer.Part import Part
from shazzam.optimizer.Bank import Bank
from shazzam.optimizer.C64Mode import C64Mode
from shazzam.optimizer.Heuristics import Heuristics

import copy
from enum import Enum, auto
from typing import List, Tuple
import logging


class SegmentOptimizerType(Enum):
    FF = auto()
    NF = auto()
    BF = auto()
    FFD = auto()
    NFD = auto()
    BFD = auto()

class SegmentOptimizer():

    def __init__(self):
        self.logger = logging.getLogger("shazzam")
        self.parts = []
        self.segments = []
        self.bank = []
        self.mode = None

    def select_bank(self, mode: C64Mode):

        if mode is C64Mode.IO_VISIBLE:
                self.banks = [
                    Bank(0, addresses_ranges=[(0x0200, 0x0fff), (0x2000, 0x3fff)]),
                    Bank(1, addresses_ranges=[(0x4000, 0x7fff)]),
                    Bank(2, addresses_ranges=[(0x8000, 0x8fff), (0xa000, 0xbfff)]),
                    Bank(3, addresses_ranges=[(0xc000, 0xcfff), (0xe000, 0xffff)])
                ]
        elif mode is C64Mode.ULTIMAX_WITH_IO:
            self.banks = [
                Bank(0, addresses_ranges=[(0x0200, 0x3fff)]),
                Bank(1, addresses_ranges=[(0x4000, 0x7fff)]),
                Bank(2, addresses_ranges=[(0x8000, 0xbfff)]),
                Bank(3, addresses_ranges=[(0xc000, 0xcfff), (0xe000, 0xffff)])
            ]
        elif mode is C64Mode.ULTIMAX_WITHOUT_IO:
            self.banks = [
                Bank(0, addresses_ranges=[(0x0200, 0x3fff)]),
                Bank(1, addresses_ranges=[(0x4000, 0x7fff)]),
                Bank(2, addresses_ranges=[(0x8000, 0xbfff)]),
                Bank(3, addresses_ranges=[(0xc000, 0xffff)])
            ]
        elif mode is C64Mode.ONLY_RAM:
            self.banks = [
                Bank(0, addresses_ranges=[(0x0200, 0x0fff), (0x2000, 0x3fff)]),
                Bank(1, addresses_ranges=[(0x4000, 0x7fff)]),
                Bank(2, addresses_ranges=[(0x8000, 0x8fff), (0xa000, 0xbfff)]),
                Bank(3, addresses_ranges=[(0xc000, 0xffff)])
            ]
        else:
            raise ValueError(f"Unknown mode {mode.name}")

        self.mode = mode

    def add_code_segment(self, size: int, name: str, part_type: Part.PartType, fixed_address: int = None, group: int = None):
        self.parts.append(Part(size=size, name=name, part_type=part_type, group=None, fixed_address=fixed_address))

    def add_memory_segment(self, start_address: int, end_address: int, segment_type: MemorySegment.SegmentType):
        self.segments.append(MemorySegment(start_address, end_address, segment_type))

    def run_best_fit(self):
        self.print_constraints()
        self.logger.info("----------- First Fit -----------")

        heuristics = Heuristics(self.segments, self.parts, self.banks)
        heuristics.first_fit()
        heuristics.print_results()

    def run_next_fit(self):
        self.print_constraints()
        self.logger.info("----------- Next Fit -----------")

        heuristics = Heuristics(self.segments, self.parts, self.banks)
        heuristics.next_fit()
        heuristics.print_results()

    def run_best_fit(self):
        self.print_constraints()
        self.logger.info("----------- Best Fit -----------")

        heuristics = Heuristics(self.segments, self.parts, self.banks)
        heuristics.best_fit()
        heuristics.print_results()

    def run_first_fit_decreasing(self):
        self.print_constraints()
        self.logger.info("----------- First Fit Decreasing -----------")

        heuristics = Heuristics(self.segments, self.parts, self.banks)
        heuristics.first_fit_decreasing()
        heuristics.print_results()

    def run_next_fit_decreasing(self):
        self.print_constraints()
        self.logger.info("----------- Next Fit Decreasing -----------")

        heuristics = Heuristics(self.segments, self.parts, self.banks)
        heuristics.next_fit_decreasing()
        heuristics.print_results()

    def run_best_fit_decreasing(self):
        self.print_constraints()
        self.logger.info("----------- Best Fit Decreasing -----------")

        heuristics = Heuristics(self.segments, self.parts, self.banks)
        heuristics.best_fit_decreasing()
        heuristics.print_results()

    def print_constraints(self):
        self.logger.info("------------------------------------CONSTRAINTS-----------------------------------------")
        self.logger.info(f"Need to allocate {len(self.parts)} parts ({sum([part.size for part in self.parts])} bytes) in the following memory segments, in mode {self.mode.name}:")
        for i, part in enumerate(self.parts):
            self.logger.info(f" - Part {i}: {part}")
        for i, segment in enumerate(self.segments):
            self.logger.info(f"{i}: {segment}")

        self.logger.info("-----------------------------------------------------------------------------------------")

    #     parts = [
    #         Part( 889, "SID", Part.PartType.CODE, fixed_address=0x1000),
    #         Part( 123, "Init", Part.PartType.CODE),
    #         Part( 252, "IRQ_top", Part.PartType.CODE),
    #         Part(3341, "IRQ_draw", Part.PartType.CODE),
    #         Part( 502, "IRQ_no_border", Part.PartType.CODE),
    #         Part(1909, "Routines", Part.PartType.CODE),
    #         Part(2564, "Tables_sprites", Part.PartType.GENERIC_DATA),
    #         Part(2564, "Tables_bitmap", Part.PartType.GENERIC_DATA),
    #         Part(1280, "Sprites1", Part.PartType.SPRITE, group="1"),
    #         Part(2560, "Sprites2", Part.PartType.SPRITE, group="2"),
    #         Part(8000, "Bitmap1", Part.PartType.BITMAP, group="1"),
    #         Part(1000, "Screen_ram1", Part.PartType.SCREEN_MEM, group="1"),
    #         Part(8000, "Bitmap2", Part.PartType.BITMAP, group="2"),
    #         Part(1000, "Screen_ram2", Part.PartType.SCREEN_MEM, group="2"),
    #         Part(1000, "Color_ram", Part.PartType.REGISTERS, fixed_address=0xd800),
    #     ]
