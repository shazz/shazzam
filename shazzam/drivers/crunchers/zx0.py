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

        zx0_src_ptr             = 0xf0

        zx0_bitmask             = 0xf5
        zx0_bitvalue            = 0xf6

        zx0_src_buffer          = 0xfc

        def inc_src():
            incsr1 = get_anonymous_label("incsr1")
            inc(at(zx0_src_ptr))
            bne(rel_at(incsr1))
            inc(at(zx0_src_ptr)+1)
            label(incsr1)

        def read_byte():
            lda(ind_at(zx0_src_buffer), y)
            inc_src()

        def read_bit():
            no_reset = get_anonymous_label("no_reset")
            lda(at(zx0_bitmask))
            lsr()
            bne(rel_at(no_reset))
            lda(imm(128))
            read_byte()
            label(no_reset)

            lda(at(zx0_bitvalue))
            andr(at(zx0_bitmask))

        def read_interlaced_elias_gamma():
            read = get_anonymous_label("read")
            label(read)
            read_bit()
            bne(rel_at(loop))

            
