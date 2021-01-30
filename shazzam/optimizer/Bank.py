from typing import List, Tuple


class Bank():

    def __init__(self, number, addresses_ranges: List[Tuple]):
        self.number = number
        self.addresses_ranges = addresses_ranges
        self.size = 0

        for adr_range in addresses_ranges:
            if adr_range[1] < adr_range[0]:
                raise ValueError(f"address range has to be ordered: {adr_range}")
            self.size += adr_range[1] - adr_range[0]

    def __str__(self):
        return f"Bank {self.number} - {self.size} bytes on {len(self.addresses_ranges)} segment(s)"

    def __repr__(self):
        return self.__str__()