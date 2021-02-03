from enum import Enum, auto


class Alias(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


class RegisterX(Enum):
    foo = 0


class RegisterY(Enum):
    foo = 0


class RegisterACC(Enum):
    foo = 0


class CodeFormat(Enum):
    BYTECODE = auto()
    ADDRESS = auto()
    CYCLES = auto()
    UPPERCASE = auto()
    USE_HEX = auto()
    SHOW_LABELS = auto()


class CommentsFormat(Enum):
    USE_SEMICOLON = auto()
    USE_SLASH = auto()
    USE_SHARP = auto()


class DirectiveFormat(Enum):
    NO_PREFIX = auto()
    USE_DOT = auto()
    USE_EXCLAMATION = auto()


class DirectiveDelimiter(Enum):
    DOUBLE_QUOTE = auto()
    NO_DELIMITER = auto()


class LabelFormat(Enum):
    NO_PREFIX = auto()
    USE_DOT = auto()


class DetectMode(Enum):
    AUTO = 0
    MANUAL = 1


class System(Enum):
    PAL = 63
    NTSC = 65
