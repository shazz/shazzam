from shazzam.Instruction import Instruction

class ByteData(Instruction):
    """ByteData class"""
    def __init__(self, value, label):
        """[summary]

        Args:
            value ([type]): [description]
            label ([type]): [description]
        """
        self.value = value
        self.label = label
        self.use_upper = True

    def get_operand(self) -> str:
        """[summary]

        Returns:
            str: [description]
        """
        return None

    def get_opcode(self) -> str:
        """[summary]

        Returns:
            str: [description]
        """
        return self.value

    def __str__(self) -> str:
        """[summary]

        Returns:
            str: [description]
        """
        return f"byte ${self.value:02X}" if self.use_upper else f"${self.value:02x}"

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