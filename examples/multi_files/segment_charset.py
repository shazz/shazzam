# if shazzam not installed
import sys
sys.path.append(".")

from shazzam.Segment import SegmentType
from shazzam.py64gen import *
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a
from shazzam.macros.aliases import color, vic

with segment(0x1ffe, "charset", segment_type=SegmentType.CHARACTERS) as s:       #0x2000 - 2 header bytes
    incbin(open("resources/aeg_collection_12.64c", "rb").read())