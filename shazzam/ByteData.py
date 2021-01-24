from shazzam.Instruction import Instruction
from shazzam.Immediate import Immediate

class ByteData(Instruction):
    """ByteData class"""
    def __init__(self, immediate: Immediate):
        """[summary]

        Args:
            value ([type]): [description]
            label ([type]): [description]
        """
        self.immediate = immediate
        self.use_upper = True
        self.address = None

    def get_operand(self) -> str:
        """[summary]

        Returns:
            str: [description]
        """
        return None, True

    def get_opcode(self) -> str:
        """[summary]

        Returns:
            str: [description]
        """
        return self.immediate.value

    def __str__(self) -> str:
        """[summary]

        Returns:
            str: [description]
        """
        return f"byte ${self.immediate.value:02X}" if self.use_upper else f"${self.immediate.value:02x}"

    def get_cycle_count(self) -> int:
        """[summary]

        Returns:
            int: [description]
        """
        return 0

    def get_size(self) -> int:
        """[summary]

        Returns:
            int: [description]
        """
        return 1