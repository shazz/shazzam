# ---------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------
from shazzam.defs import CodeFormat, CommentsFormat, DirectiveFormat, DirectiveDelimiter, DirectiveExport
from shazzam.Program import Program

import logging
import sys


def initialize():
    global _CODE_FORMAT, _COMMENTS_FORMAT, _DIRECTIVE_PREFIX, _DEFAULT_CODE_SEGMENT, _DIRECTIVE_DELIMITER, _DIRECTIVE_EXPORT
    global _PROGRAM, _GLOBAL_LABELS, _CURRENT_CONTEXT, _CURRENT_RASTER, _LISTING_FORMAT
    global logger

    print("Program created")
    _PROGRAM = Program()
    _GLOBAL_LABELS = {}
    _CURRENT_CONTEXT = None
    _CURRENT_RASTER = None

    # _CODE_FORMAT =  [ CodeFormat.BYTECODE, CodeFormat.ADDRESS, CodeFormat.CYCLES, CodeFormat.UPPERCASE, CodeFormat.USE_HEX, CodeFormat.SHOW_LABELS ]
    _CODE_FORMAT = [CodeFormat.BYTECODE, CodeFormat.ADDRESS, CodeFormat.CYCLES, CodeFormat.UPPERCASE, CodeFormat.USE_HEX]
    _COMMENTS_FORMAT = CommentsFormat.USE_SEMICOLON
    _DIRECTIVE_PREFIX = DirectiveFormat.NO_PREFIX
    _DIRECTIVE_EXPORT = DirectiveExport.USE_EXPORT_DIRECTIVE
    _DIRECTIVE_DELIMITER = DirectiveDelimiter.DOUBLE_QUOTE
    _DEFAULT_CODE_SEGMENT = "CODE"
    _LISTING_FORMAT = [CodeFormat.BYTECODE, CodeFormat.ADDRESS, CodeFormat.CYCLES, CodeFormat.UPPERCASE, CodeFormat.USE_HEX]

    logger = logging.getLogger("shazzam")
    logger.setLevel(logging.INFO)

    # formatter = logging.Formatter('%(levelname)s : %(funcName)s : %(message)s')
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
