
class Address():

    def __init__(self, name: str = None, value: int = None, indirect: bool = False):

        if name is None and value is None:
            raise ValueError("Address is void")

        if value and value > 0xffff:
            raise ValueError(f"Address value {value} exceeds 1 word")

        self.name = name
        self._value = value
        self.indirect = indirect
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
    def value(self, val):
         if(val > 0xffff):
            raise ValueError(f"Address value {val} exceeds 1 word")

         self._value = val

    def __add__(self, adder):
        self._add_modifier = adder

    def __sub__(self, subber):
        self._sub_modifier = subber

    def __str__(self):
        if self._value and self.name:
            return f"{self.name}@{self._value:04X}"
        elif self._value:
            return f"{self._value:04X}"
        elif self.name:
            return f"{self.name}@unknown"
        else:
            raise RuntimeError("Address is void")
