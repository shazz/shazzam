from shazzam.Cruncher import Cruncher
from shazzam.py64gen import *
# from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a


class Pucrunch(Cruncher):

    def __init__(self, exe_path: str):

        cmd_prg_template = [exe_path, 'FILENAME_TO_SET', "OUTPUT_TO_SET"]
        cmd_bin_template = [exe_path, 'FILENAME_TO_SET', "OUTPUT_TO_SET"]
        super().__init__("pucrunch", exe_path, cmd_prg_template, cmd_bin_template)

    def generate_depacker_routine(self, address: int) -> None:
        """generate_depacker_routine

        Args:
            address (int): [description]

        Raises:
            NotImplementedError: [description]
        """
        # -----------------------------------------------------------------------------
        # ZX0 decoder by Einar Saukas
        # "Standard" version (69 bytes only)
        # -----------------------------------------------------------------------------
        # Parameters:
        #   HL: source address (compressed data)
        #   DE: destination address (decompressing)
        # -----------------------------------------------------------------------------

        # label("dzx0_standard")
        # lda(im(0xff))                    # ld      bc, $ffff               # preserve default offset 1
        # tax()
        # pha()
        # pha()                           # push    bc
        # clc()
        # adc(imm(1))
        # tax
        # tya()

        # m.add16()                       #inc     bc
        # lda(imm(0x80))                  # ld a, $80

        # label("dzx0s_literals")
        # jsr(at("dzx0s_elias"))             # obtain length
        # ldir                            # copy literals
        # add     a, a                    # copy from last offset or new offset?
        # jr      c, dzx0s_new_offset
        # jsr(at("dzx0s_elias"))             # obtain length

        # label("dzx0s_copy")
        # ex      (sp), hl                # preserve source, restore offset
        # push    hl                      # preserve offset
        # add     hl, de                  # calculate destination - offset
        # ldir                            # copy from offset
        # pop     hl                      # restore offset
        # ex      (sp), hl                # preserve offset, restore source
        # add     a, a                    # copy from literals or new offset?
        # jr      nc, dzx0s_literals

        # label("dzx0s_new_offset")
        # jsr(at("dzx0s_elias"))             # obtain offset MSB
        # ex      af, af'
        # pop     af                      # discard last offset
        # xor     a                       # adjust for negative offset
        # sub     c
        # ret     z                       # check end marker
        # ld      b, a
        # ex      af, af'
        # ld      c, (hl)                 # obtain offset LSB
        # inc     hl
        # rr      b                       # last offset bit becomes first length bit
        # rr      c
        # push    bc                      # preserve new offset
        # ld      bc, 1                   # obtain length
        # call    nc, dzx0s_elias_backtrack
        # inc     bc
        # jmp(at("dzx0s_copy"))

        # label("dzx0s_elias")
        # inc     c                       # interlaced Elias gamma coding

        # label("dzx0s_elias_loop")
        # add     a, a
        # jr      nz, dzx0s_elias_skip
        # ld      a, (hl)                 # load another group of 8 bits
        # inc     hl
        # rla

        # label("dzx0s_elias_skip")
        # ret     c

        # label("dzx0s_elias_backtrack")
        # add     a, a
        # rl      c
        # rl      b
        # jmp(at("dzx0s_elias_loop"))