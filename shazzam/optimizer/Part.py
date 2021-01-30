from enum import Enum
from typing import List, Tuple

class Part():

    class PartType(Enum):
        CODE = 0
        REGISTERS = 1
        SPRITE = 2
        CHARACTERS = 3
        SCREEN_MEM = 4
        BITMAP = 5
        GENERIC_DATA = 6

    def __init__(self, size: int, name: str, part_type: PartType, group: str = None, fixed_address: int = None):
        self.size = size
        self.name = name
        self.part_type = part_type
        self.fixed_address = fixed_address
        self.group = group

        if part_type in [Part.PartType.SPRITE, Part.PartType.CHARACTERS, Part.PartType.SCREEN_MEM, Part.PartType.BITMAP] and group is None:
            raise ValueError(f"Graphical parts need to be grouped")

    def __str__(self):
        return f"{self.name}{f'[{self.group}]' if self.group is not None else ''} of type {self.part_type.name} ({self.size } bytes){f' at ${self.fixed_address:04x}' if self.fixed_address is not None else ''}"

    def __repr__(self):
        return self.__str__()
