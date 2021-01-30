from shazzam.optimizer.MemorySegment import MemorySegment
from shazzam.optimizer.Part import Part
from shazzam.optimizer.Bank import Bank

import copy
from enum import Enum
from typing import List, Tuple
import logging


class Heuristics():

    def __init__(self, segments: List[MemorySegment], parts: List[Part], banks: List[Bank]):

        self.logger = logging.getLogger("shazzam")

        self.segments = copy.deepcopy(segments)
        self.parts = copy.deepcopy(parts)
        self.is_fitted = False
        self.banks = banks

        self.groups = self._get_parts_groups()

        self._sort_parts_by_priority()
        self.best_banks = self._select_best_bank()

        self.logger.debug(f"MemorySegments reorganized in:")
        for segment in self.segments:
            self.logger.debug(f" - {segment}")

    def best_fit(self) -> List[MemorySegment]:
        """allocate memory to blocks as per Best fit algorithm

        Returns:
            List[MemorySegment]: [description]
        """
        if self.is_fitted:
            raise RuntimeError("Already fitted!")

        # pick each process and find suitable blocks according to its size and assign to it
        for part in self.parts:

            if part.fixed_address is not None:
                try:
                    segment = self._get_segment(start_address=part.fixed_address)
                    self._allocate(segment, part)
                except ValueError as e:
                    self.logger.error(e)
            else:
                segments = self.segments

                # restrict to best bank segments
                if part.part_type in [Part.PartType.SPRITE, Part.PartType.BITMAP, Part.PartType.CHARACTERS, Part.PartType.SCREEN_MEM]:
                    segments = self._get_segments_for_bank(self.gfx_banks[part.group])

                # Find the best fit block within all segments
                best_segment = None
                for segment in segments:
                    if segment.remaining_size >= part.size and self._is_compatible(segment, part):
                        if best_segment is None:
                            best_segment = segment
                        elif best_segment.remaining_size > segment.remaining_size:
                            best_segment = segment

                # If we could find a block for current process
                if best_segment is not None:
                    self._allocate(best_segment, part)
                else:
                    self.logger.warning(f"Warning! No segment found for part {part}!")

        self.is_fitted = True

        return self.segments

    def next_fit(self) -> List[MemorySegment]:
        """allocate memory to blocks as per Next fit algorithm

        Raises:
            ValueError: [description]

        Returns:
            List[MemorySegment]: [description]
        """
        if self.is_fitted:
            raise RuntimeError("Already fitted!")

        previous_idx = 0

        # pick each process and find suitable blocks according to its size ad assign to it
        for part in self.parts:

            if part.fixed_address is None:
                segments = self.segments

                # restrict to best bank segments
                if part.part_type in [Part.PartType.SPRITE, Part.PartType.BITMAP, Part.PartType.CHARACTERS, Part.PartType.SCREEN_MEM]:
                    segments = self._get_segments_for_bank(self.gfx_banks[part.group])

                # Do not start from beginning
                for idx in range(previous_idx, len(segments)):
                    segment = segments[idx]
                    if segment.remaining_size >= part.size and self._is_compatible(segment, part):
                        self._allocate(segment, part)

                        previous_idx = idx if idx < len(segments) else 0
                        break
            else:
                try:
                    segment = self._get_segment(start_address=part.fixed_address)
                    self._allocate(segment, part)
                except ValueError as e:
                    raise e
                    self.logger.error(e)

        self.is_fitted = True

        return self.segments

    def first_fit(self) -> List[MemorySegment]:
        """[summary]

        Raises:
            RuntimeError: [description]

        Returns:
            List[MemorySegment]: [description]
        """
        if self.is_fitted:
            raise RuntimeError("Already fitted!")

        # Initially no block is assigned to any process pick each process and find suitable blocks according to its size ad assign to it
        for part in self.parts:

            if part.fixed_address is None:
                segments = self.segments

                # restrict to best bank segments
                if part.part_type in [Part.PartType.SPRITE, Part.PartType.BITMAP, Part.PartType.CHARACTERS, Part.PartType.SCREEN_MEM]:
                    segments = self._get_segments_for_bank(self.gfx_banks[part.group])

                for segment in segments:
                    if segment.remaining_size >= part.size and self._is_compatible(segment, part):
                        self._allocate(segment, part)
                        break
            else:
                try:
                    segment = self._get_segment(start_address=part.fixed_address)
                    self.logger.debug(f"For part {part}, targetted segment is {segment}")
                    self._allocate(segment, part)
                except ValueError as e:
                    self.logger.error(e)

        self.is_fitted = True

        return self.segments

    def first_fit_decreasing(self) -> None:
        """allocate memory to blocks as per First Fit Decreasing algorithm"""

        # reorder parts by size decreasing and priority
        self._sort_parts_by_size()

        # fit as usual
        self.first_fit()

    def best_fit_decreasing(self) -> None:
        """allocate memory to blocks as per Best Fit Decreasing algorithm"""

        # reorder parts by size decreasing and priority
        self._sort_parts_by_size()

        # fit as usual
        self.best_fit()

    def next_fit_decreasing(self) -> None:
        """allocate memory to blocks as per Next Fit Decreasing algorithm"""

        # reorder parts by size decreasing and priority
        self._sort_parts_by_size()

        # fit as usual
        self.next_fit()

    def generate_c64jasm_segments(self) -> None:
        """Generate segments file to be used in c64jasm"""

        with open("segments.jasm", "w") as f:
            for i, segment in enumerate(self.segments):
                for alloc in segment.allocations:
                    line = f"!segment {alloc.part.name.upper()} {{ from: ${alloc.start_address:04x}, to: ${alloc.end_address:04x} }}\n"
                    f.write(line)

        #TODO: add Bank and d018 information

    def print_results(self, validate_results: bool = True) -> None:
        """Print results"""

        # stats
        allocated = 0
        used = 0
        not_allocated = 0
        free = 0

        for i, segment in enumerate(self.segments):
            self.logger.info(f"Segment {i} [${segment.start_address:04x} - ${segment.end_address:04x}] of size {segment.initial_size} has {segment.remaining_size} bytes remaining ({round(100*segment.remaining_size/segment.initial_size, 2)}%)")

            used_in_segment = (segment.initial_size - segment.remaining_size)
            used += used_in_segment
            free += segment.remaining_size

            if used_in_segment > 0:
                not_allocated += segment.remaining_size

            for alloc in segment.allocations:
                self.logger.info(f" - Part {alloc.part} is allocated at [${alloc.start_address:04x} - ${alloc.end_address:04x}]")
                allocated += alloc.initial_size

        self.logger.info(f"Total allocated      : {allocated} bytes")
        self.logger.info(f"Total not allocated  : {not_allocated} bytes")
        self.logger.info(f"Total free           : {free} bytes")

        if validate_results:
            self._validate_results()
            self.logger.info("Segments allocation validated")

        assert allocated == used, f"Total allocated {allocated} should be equal to total used in segment {used}"

    def _split_segments(self, part) -> None:
        """Split a segment in 2 parts to support fixed allocation

        Args:
            part ([type]): [description]
        """

        segment = self._get_segment(part.fixed_address)

        if part.fixed_address > segment.start_address:

            low_segment = MemorySegment(
                start_address = segment.start_address,
                end_address = part.fixed_address - 1,
                segment_type = segment.segment_type)

            self.segments.insert(self.segments.index(segment), low_segment)

            segment.start_address = part.fixed_address

        # print("\nMemorySegments updated")
        # for segment in self.segments:
        #     print(f"\t - {segment}")

    def _select_best_bank(self) -> None:
        """Select best VIC bank based on gfx parts to store"""

        self.gfx_banks = {}
        banks_used = []
        for group in self.groups:

            gfx_mem_required = 0
            for part in self.parts:
                gfx_mem_required += part.size if part.group == group and part.part_type in [Part.PartType.SPRITE, Part.PartType.BITMAP, Part.PartType.CHARACTERS, Part.PartType.SCREEN_MEM] else 0

            bank_used_mem = []
            for bank in self.banks:
                available_mem = bank.size - gfx_mem_required
                if available_mem >= 0 and bank not in banks_used:
                    bank_used_mem.append((bank, available_mem))

            if len(bank_used_mem) == 0:
                raise ValueError(f"Gfx data exceeds biggest bank capacity, more groups are needed to store {gfx_mem_required} bytes")

            best_banks = sorted(bank_used_mem, key=lambda banks: banks[1], reverse=False)

            self.logger.debug(f"Possible banks to store {gfx_mem_required} bytes of graphics: {best_banks} ")
            first_available_bank = best_banks[0][0]
            self.gfx_banks[group] = first_available_bank
            banks_used.append(first_available_bank)

            self.logger.debug(f"For group '{group}', bank {first_available_bank} is selected")
            self._get_segments_for_bank(first_available_bank)

    def _sort_parts_by_size(self) -> None:
        """Sort the parts by priority then by size decreasing"""

        self.parts = sorted(self.parts, key=lambda parts: parts.size, reverse=True)
        self._sort_parts_by_priority()

    def _get_parts_groups(self) -> List[str]:
        """[summary]

        Returns:
            List[str]: [description]
        """

        groups  = []
        for part in self.parts:
            if part.group is not None and part.group not in groups:
                groups.append(part.group)

        return groups

    def _sort_parts_by_priority(self) -> None:
        """Sort the part by priority (fixed addresses first then gfx then code/generic data)"""

        high_priority_parts = []
        medium_priority_parts = []
        low_priority_parts = []

        # give medium priority to some gfx parts
        for part in self.parts:
            if part.part_type in [Part.PartType.SPRITE, Part.PartType.BITMAP, Part.PartType.CHARACTERS]:
                low_priority_parts.insert(0, part)
            else:
                low_priority_parts.append(part)

        # give medium priority to screen mem
        for part in low_priority_parts:
            if part.part_type in [Part.PartType.SCREEN_MEM]:
                medium_priority_parts.insert(0, part)
            else:
                medium_priority_parts.append(part)

        # give high priority to fixed address part
        for part in medium_priority_parts:
            if part.fixed_address is not None:
                high_priority_parts.insert(0, part)
                self._split_segments(part)
            else:
                high_priority_parts.append(part)

        self.parts = high_priority_parts

        self.logger.debug("Parts reorganized by priority")
        for part in self.parts:
            self.logger.debug(f" - {part}")

    def _get_segments_for_bank(self, bank: Bank) -> List[MemorySegment]:

        segments = []

        for adr_range in bank.addresses_ranges:
            start_address = adr_range[0]
            end_address  = adr_range[1]

            self.logger.debug(f"Looking for segment on range [${start_address:04x} - ${end_address:04x}] for Bank {bank}")
            for segment in self.segments:
                # print(f"Checking in segment range: [${segment.start_address:04x} - ${segment.end_address:04x}]")
                if segment.start_address >= start_address and segment.end_address <= end_address:
                    segments.append(segment)

                elif start_address >= segment.start_address and end_address <= segment.end_address:
                    # split the segment

                    self.logger.debug(f"MemorySegment is split to match banks")
                    if start_address > segment.start_address:
                        low_seg = MemorySegment(
                            start_address = segment.start_address,
                            end_address = start_address - 1,
                            segment_type = segment.segment_type)
                        self.segments.insert(self.segments.index(segment), low_seg)
                        self.logger.debug(f" - low segment: {low_seg}")

                    if end_address < segment.end_address:
                        high_seg = MemorySegment(
                            start_address = end_address + 1,
                            end_address = segment.end_address,
                            segment_type = segment.segment_type)
                        self.segments.insert(self.segments.index(segment)+1, high_seg)
                        self.logger.debug(f" - high segment {high_seg}")

                    segment.start_address = start_address
                    segment.end_address = end_address
                    self.logger.debug(f" - mid segment {segment}")


        if len(segments) == 0:
            raise ValueError(f"No segments found for bank {bank}")

        self.logger.debug(f"Bank {bank} contains the segments: {segments}")

        return segments

    def _get_segment(self, start_address: int) -> MemorySegment:
        """Find segment containing the given address

        Args:
            start_address (int): Part start address

        Raises:
            ValueError: if no MemorySegment found

        Returns:
            MemorySegment: Found segment
        """

        for segment in self.segments:
            if segment.start_address <= start_address and segment.end_address > start_address:
                return segment

        raise ValueError(f"No segment found for this fixed address: {start_address:04x}")

    def _is_compatible(self, segment: MemorySegment, part: Part) -> bool:
        """[summary]

        Args:
            segment (MemorySegment): [description]
            part (Part): [description]

        Returns:
            bool: True is compatible
        """
        if segment.segment_type is MemorySegment.SegmentType.IO:
            return part.part_type == Part.PartType.REGISTERS

        elif segment.segment_type is MemorySegment.SegmentType.UserRAM:
            return part.part_type not in [Part.PartType.REGISTERS]

        elif segment.Restricted:
            return False

    def _allocate(self, segment: MemorySegment, part: Part) -> None:
        """Allocate a part in a segment if compatible

        Args:
            segment (MemorySegment): [description]
            part (Part): [description]

        Raises:
            ValueError: if they are not compatible
        """

        self.logger.debug(f"Checking {part} can be allocated in {segment}")
        if not self._is_compatible(segment, part):
            raise ValueError(f"Part {part.name} of type {part.part_type.name} is not compatible with the segment {segment.name} of type {segment.segment_type.name}")

        segment.allocate(part)

    def _validate_results(self) -> None:
        """Validate results"""

        for segment in self.segments:
            for alloc in segment.allocations:
                assert self._is_compatible(segment, alloc.part), f"Part {alloc.part} is not compatible with MemorySegment {segment}"
                if alloc.part.fixed_address is not None:
                    assert alloc.start_address == alloc.part.fixed_address, f"Part {alloc.part} should start at ${alloc.part.fixed_address:04x} but starts at ${alloc.start_address:04x}"

                if alloc.part.part_type in [Part.PartType.SPRITE, Part.PartType.BITMAP, Part.PartType.CHARACTERS, Part.PartType.SCREEN_MEM]:
                    bank_assigned = self.gfx_banks[alloc.part.group]
                    segments_in_bank = self._get_segments_for_bank(bank_assigned)
                    part_in_segment = False
                    for segment in segments_in_bank:
                        if alloc.start_address >= segment.start_address and (alloc.start_address + alloc.part.size) <= segment.end_address:
                            part_in_segment = True

                    # checking gfx part is in VIC bank assigned for this group
                    assert part_in_segment == True, f"Part {alloc.part} should be in segments {segments_in_bank} from banks {bank_assigned}"

                    # checking alignment
                    if alloc.part.part_type is Part.PartType.SCREEN_MEM:
                        assert alloc.start_address % 0x400 == 0, f"Screen Memory parts have to be aligned on 0x400 boundary"
