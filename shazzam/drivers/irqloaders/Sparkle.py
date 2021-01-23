import json
import re
import logging
from typing import Dict

from shazzam.Program import Program

class Sparkle():

    def __init__(self):
        self.logger = logging.getLogger("shazzam")

    def gen_sls(self, desc: Dict, program: Program) -> str:

        self.logger.info(f"Generating Sparkle Script file")

        script = "[Sparkle Loader Script]\n\n"
        script += f"Path:\t{desc['demo']['id']}\n"
        script += f"Header:\t{desc['demo']['header']}\n"

        script += f"ID:\t{desc['demo']['id']}\n"

        script += f"Name:\t{desc['demo']['name']}\n"
        script += f"Start:\t{'{0:04x}'.format(desc['sequencer']['segment'])}\n"
        script += f"DirArt:\t{desc['demo']['dir_art']}\n"

        for i, interleave in enumerate(desc['demo']['interleaves']):
            script += f"IL{i}:\t0{interleave}\n"

        script += f"ZP:\t{desc['demo']['zp']}\n"
        script += f"Loop:\t{desc['demo']['loop']}\n\n"

        if 'script' in desc['sequencer']:
            path = desc['sequencer']['script'].replace('/', '\\')
            script += f"Script:\t{path}\n\n"

        parts_order = parts_desc['sequencer']["order"]

        for part_name in parts_order:
            if 'align' in parts_desc[part_name] and parts_desc[part_name]['align'] is True:
                script += "Align\n"

            # add data to bundle
            for data in parts_desc[part_name]['data']:
                path = data['path'].replace('/', '\\')
                address = '{0:04x}'.format(data['address'])
                if "size" in data:
                    offset = '{0:04x}'.format(data['offset'])
                    size = '{0:04x}'.format(data['size'])
                    script += f"File:\t{path}\t{address}\t{offset}\t{size}\n"
                else:
                    script += f"File:\t{path}\t{address}\n"

            # split prg per segment
            part_offset = offsets[part_name]
            self.logger.debug(f"Splitting prg {parts_desc[part_name]}")

            prg_path = parts_desc[part_name]['prg_path'].replace('/', '\\')
            for segment, params in part_offset.items():
                address = '{0:04x}'.format(params['start'])
                delta =  params['start'] - parts_desc[part_name]['seg_start'] + 2
                offset = '{0:04x}'.format(delta)
                size = '{0:04x}'.format(params['size'])

                self.logger.debug(f"Added prg segment: {prg_path} - [{address}, {offset}, {size}]")
                script += f"File:\t{prg_path}\t{address}\t{offset}\t{size}\n"

            script += "\n"

        return script


    def generate_sparkle_script(self, part_filename: str, sparkle_script_name: str):

        demo_offsets = {}
        sls_params = {}

        with open(part_filename, "r") as f:
            parts_desc = json.load(f)

        parts_order = parts_desc['sequencer']["order"]

        # set sls params
        script = gen_sls(parts_desc, demo_offsets)
        with open(f'{sparkle_script_name}.sls', 'w') as f:
            f.write(script)


