from shazzam.optimizer.Part import Part

from enum import Enum
from typing import List, Tuple
import logging

class MemorySegment():

    class SegmentType(Enum):
        UserRAM = 0
        IO = 1
        Restricted = 2

    def __init__(self, start_address: int, end_address: int, segment_type: SegmentType):
        self._start_address = start_address
        self._end_address = end_address
        self.remaining_size = self.end_address - self.start_address
        self.segment_type = segment_type

        self.allocations = []
        self.logger = logging.getLogger("shazzam")

    @property
    def initial_size(self):
        return self.end_address - self.start_address

    @property
    def end_address(self):
        return self._end_address

    @end_address.setter
    def end_address(self, value):
        self._end_address = value
        self.remaining_size = self.end_address - self.start_address

    @property
    def start_address(self):
        return self._start_address

    @start_address.setter
    def start_address(self, value):
        self._start_address = value
        self.remaining_size = self.end_address - self.start_address

    def allocate(self, part: Part) -> None:
        """Allocate a part in a segment

        Args:
            part (Part): [description]

        Raises:
            ValueError: [description]
        """
        self.logger.debug(f"Trying to allocate {part} in {self}")

        allocated_start_adr = self.start_address + self.initial_size - self.remaining_size
        space_to_allocate = part.size

        # Manage alignment, screen mem should be aligned on $400 boundary
        if part.part_type is Part.PartType.SCREEN_MEM:
            misalign = allocated_start_adr % 0x400
            if misalign != 0:
                allocated_start_adr += (0x400 - misalign)
                self.logger.warning(f"segment next pointer is realigned from ${allocated_start_adr:04x} to ${allocated_start_adr-(0x400 - misalign):04x} to support Screen Memory")
                space_to_allocate += (0x400 - misalign)

        # Manage alignment, screen mem should be aligned on $400 boundary
        if part.part_type is Part.PartType.SPRITE:
            misalign = allocated_start_adr % 0x40
            if misalign != 0:
                allocated_start_adr += (0x40 - misalign)
                self.logger.warning(f"segment next pointer is realigned from ${allocated_start_adr:04x} to ${allocated_start_adr-(0x40 - misalign):04x} to support Sprite pointers")
                space_to_allocate += (0x40 - misalign)

        # Manage alignment, screen mem should be aligned on $400 boundary
        if part.part_type is Part.PartType.CHARACTERS:
            misalign = allocated_start_adr % 0x800
            if misalign != 0:
                allocated_start_adr += (0x800 - misalign)
                self.logger.warning(f"segment next pointer is realigned from ${allocated_start_adr:04x} to ${allocated_start_adr-(0x800 - misalign):04x} to support Character Memory")
                space_to_allocate += (0x800 - misalign)

        if space_to_allocate > self.remaining_size:
            raise ValueError(f"Not enough memory to add part {part} in the {self}! Only {self.remaining_size} bytes remaining. May be due to alignment")

        allocated_segment = AllocatedMemorySegment(allocated_start_adr, allocated_start_adr + space_to_allocate, self.segment_type, part)

        self.logger.debug(f"Allocating part {part} in {self} from {allocated_start_adr:04x} to {allocated_start_adr + space_to_allocate:04x}")

        self.allocations.append(allocated_segment)
        self.remaining_size -= space_to_allocate

    def __str__(self):
        return f"MemorySegment type: {self.segment_type.name}, size: {self.initial_size} bytes with {self.remaining_size} bytes remaining - [${self.start_address:04x} - ${self.end_address:04x}]"

    def __repr__(self):
        return self.__str__()

class AllocatedMemorySegment(MemorySegment):

    def __init__(self, start_address: int, end_address: int, segment_type: MemorySegment.SegmentType, part: Part):
        super().__init__(start_address, end_address, segment_type)
        self.part = part
