from shazzam.defs import Alias

# ------------------------------------------------------------------------------------------
# Color aliases
# Replace each C64 color value by its name
# ------------------------------------------------------------------------------------------
color = Alias({
    'black'       : 0x00,
    'white'       : 0x01,
    'red'         : 0x02,
    'cyan'        : 0x03,
    'purple'      : 0x04,
    'green'       : 0x05,
    'blue'        : 0x06,
    'yellow'      : 0x07,
    'orange'      : 0x08,
    'brown'       : 0x09,
    'light_red'   : 0x0a,
    'dark_grey'   : 0x0b,
    'grey'        : 0x0c,
    'light_green' : 0x0d,
    'light_blue'  : 0x0e,
    'light_grey'  : 0x0f
})


# ------------------------------------------------------------------------------------------
# VIC Enum
# Declare VIC registers
# ------------------------------------------------------------------------------------------
vic = Alias({
    'start'               : 0xd000,
    'sprite0_x'           : 0xd000,
    'sprite0_y'           : 0xd001,
    'sprite1_x'           : 0xd002,
    'sprite1_y'           : 0xd003,
    'sprite2_x'           : 0xd004,
    'sprite2_y'           : 0xd005,
    'sprite3_x'           : 0xd006,
    'sprite3_y'           : 0xd007,
    'sprite4_x'           : 0xd008,
    'sprite4_y'           : 0xd009,
    'sprite5_x'           : 0xd00a,
    'sprite5_y'           : 0xd00b,
    'sprite6_x'           : 0xd00c,
    'sprite6_y'           : 0xd00d,
    'sprite7_x'           : 0xd00e,
    'sprite7_y'           : 0xd00f,
    'sprites_x'           : 0xd010,
    'scr_ctrl'            : 0xd011,
    'raster_line'         : 0xd012,
    'lightpen_x'          : 0xd013,
    'lightpen_y'          : 0xd014,
    'sprite_en'           : 0xd015,
    'scr_ctrl2'           : 0xd016,
    'sprite_dblh'         : 0xd017,
    'mem_setup'           : 0xd018,
    'irq_status'          : 0xd019,
    'irq_ctrl'            : 0xd01a,
    'sprite_pri'          : 0xd01b,
    'sprite_colmode'      : 0xd01c,
    'sprite_dblx'         : 0xd01d,
    'sprite_spr_coll'     : 0xd01e,
    'sprite_bck_coll'     : 0xd01f,
    'border_col'          : 0xd020,
    'bck_col'             : 0xd021,
    'back_extra_col1'     : 0xd022,
    'back_extra_col2'     : 0xd023,
    'back_extra_col3'     : 0xd024,
    'sprite_extra_col1'   : 0xd025,
    'sprite_extra_col2'   : 0xd026,
    'sprite0_color'       : 0xd027,
    'sprite1_color'       : 0xd028,
    'sprite2_color'       : 0xd029,
    'sprite3_color'       : 0xd02a,
    'sprite4_color'       : 0xd02b,
    'sprite5_color'       : 0xd02c,
    'sprite6_color'       : 0xd02d,
    'sprite7_color'       : 0xd02e,
})