import logging

class Address():

    def __init__(self, name: str = None, value: int = None, relative: int = None, indirect: bool = False):

        self.logger = logging.getLogger("shazzam")

        if name is None and value is None and indirect is None:
            raise ValueError("Address cannot be void")

        if value and value > 0xffff:
            raise ValueError(f"Address value {value} exceeds 1 word")

        self.name = name
        self._value = value
        self.indirect = indirect
        self.relative = relative
        self._add_modifier = None
        self._sub_modifier = None

    @property
    def value(self):
        if self._value is None:
            return None

        if self._add_modifier:
            self.logger.debug(f"Adding {self._add_modifier} to {self._value} = {self._value + self._add_modifier}")
            return self._value + self._add_modifier

        if self._sub_modifier:
            return self._value - self._sub_modifier

        return self._value

    @value.setter
    def value(self, val):
         if(val > 0xffff):
            raise ValueError(f"Address value {val} exceeds 1 word")

         self._value = val

    def __add__(self, adder):
        self.logger.debug(f"Adding {adder} to {self.name}")
        self._add_modifier = adder
        return self

    def __sub__(self, subber):
        self.logger.debug(f"Substracting {subber} to {self.name}")
        self._sub_modifier = subber
        return self

    def __str__(self):
        if self._value and self.name:
            return f"{self.name}@{self._value:04X}"
        elif self._value:
            return f"{self._value:04X}"
        elif self.name:
            return f"{self.name}@unknown"
        elif self.relative is not None:
            return f"{self.relative}"
        else:
            raise RuntimeError("Address is void")

    def __repr__(self):
        return self.__str__()