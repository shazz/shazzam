
class Immediate():

    def __init__(self, name: str = None, value: int = None, high_byte: bool = None):

        if name is None and value is None:
            raise ValueError("Immediate is void")

        if name and high_byte is None:
            raise ValueError("high_byte not specified")

        if value and value > 0xff:
            raise ValueError(f"Immediate value {value} exceeds 1 byte")

        self.name = name
        self.high_byte = high_byte
        self._value = value
        self._add_modifier = None
        self._sub_modifier = None

    @property
    def value(self):
        if self._value is None:
            return None

        if self._add_modifier:
            self._value += self._add_modifier

        if self._sub_modifier:
            self._value -= self._sub_modifier

        return self._value

    @value.setter
    def value(self, val: int) -> None:
        if(val > 0xff):
            raise ValueError(f"Immediate value {val} exceeds 1 byte")

        self._value = val

    def __add__(self, adder):
        self._add_modifier = adder

    def __sub__(self, subber):
        self._sub_modifier = subber

    def __str__(self):
        if self.name:
            return f"{self.name}"
        elif self._value:
            return f"{self._value:04X}"
        else:
            raise RuntimeError("Immediate is void")
