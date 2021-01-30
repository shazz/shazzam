from enum import Enum

class C64Mode(Enum):
    IO_VISIBLE = 1
    ULTIMAX_WITH_IO = 2
    ULTIMAX_WITHOUT_IO = 3
    ONLY_RAM = 4