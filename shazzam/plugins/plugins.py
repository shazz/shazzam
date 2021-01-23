from typing import Dict

# ---------------------------------------------------------------------
# SPD Sprites file parser
#
# SPD file format information
# bytes 00,01,02 = "SPD"
# byte 03 = version number of spritepad
# byte 04 = number of sprites
# byte 05 = number of animations
# byte 06 = color transparent
# byte 07 = color multicolor 1
# byte 08 = color multicolor 2
# byte 09 = start of sprite data
# byte 73 = 0-3 color, 4 overlay, 7 multicolor/singlecolor
# bytes xx = "00", "00", "01", "00" added at the end of file (SpritePad animation info)
# ---------------------------------------------------------------------
def read_spd(filename: str) -> Dict:

    with open(filename, "rb") as f:
        buf = f.read()
        numSprites = buf[4]+1
        data = []
        colors = []
        for i in range(numSprites):
            offs = i*64+9
            data_bytes = []
            for j in range(64):
                data_bytes.append(buf[offs + j])
            data.append(bytearray(data_bytes))
            colors.append(0x0f & buf[8+(64*(i+1))])

        return {
            "numSprites": numSprites,
            "enableMask": (1<<numSprites)-1,
            "colors": colors,
            "bg": buf[6],
            "multicol1": buf[7],
            "multicol2": buf[8],
            "data": data
        }

# ---------------------------------------------------------------------
# Parse SID file
#
# Extract SID start, init, play addresses and player data
# ---------------------------------------------------------------------
def read_sid(filename: str) -> Dict:

    def readWord(buf, offs):
        return buf[offs] + (buf[offs+1] << 8)

    def readWordBE(buf, offs):
        return (buf[offs]<<8) + buf[offs+1]

    with open(filename, "rb") as f:
        buf = f.read()

        version = readWordBE(buf, 4)
        dataOffset = readWordBE(buf, 6)
        startAddress = readWord(buf, dataOffset)
        init = readWordBE(buf, 0x0a)
        play = readWordBE(buf, 0x0c)
        numSongs = readWord(buf, 0x0e)

        return {
            "start_address": startAddress,
            "data": buf[dataOffset+2:],
            "init": startAddress,
            "play": startAddress + 3
        }

# ---------------------------------------------------------------------
# Get fade2black color table
# ---------------------------------------------------------------------
def get_fade_table(start, nb_elements):
    fade_2_black_chain = [0x00, 0x0d, 0x09, 0x0c, 0x02, 0x08, 0x00, 0x0f, 0x02, 0x00, 0x08, 0x09, 0x04, 0x03, 0x04, 0x05]

    fade = [0 for i in range(nb_elements)]
    col = start

    for i in range(nb_elements):
        col = fade_2_black_chain[col]
        fade[i] = col

    return fade

# ---------------------------------------------------------------------
# Convert ASCII list to bytes with offset
# ---------------------------------------------------------------------
def ascii_to_byte(text, offset):
    res = [asc(text[i]) - offset for i in range(len(text))]
    # res = Array(text.length).fill(0).map((v,i) => text.charCodeAt(i) - offset)
    return res
