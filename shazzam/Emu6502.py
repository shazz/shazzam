import logging
from io import BytesIO
import traceback
from enum import Enum, auto
from typing import List

import cooked_input as ci
from cooked_input import GetInputCommand, GetInputInterrupt, CommandResponse, COMMAND_ACTION_NOP, COMMAND_ACTION_CANCEL, COMMAND_ACTION_USE_VALUE

from py65emu.cpu import CPU
from py65emu.mmu import MMU

from shazzam.Instruction import Instruction

class Action(Enum):
    READ_MEMORY = auto()
    READ_REGISTERS = auto()
    EXIT = auto()
    RUN_NEXT = auto()
    SHOW_INSTRUCTION = auto()
    SHOW_CYCLES_COUNT = auto()
    SET_BREAKPOINT = auto()
    CLEAR_BREAKPOINT = auto()

class Emu6502():

    def __init__(self):
        self.logger = logging.getLogger("shazzam")
        self.breakpoints = []
        self.mmu = None
        self.cpu = None
        self.debug_mode = False
        self.breakpoint_in = -1
        self.nb_cycles_used = 0

    def reset_breakpoint(self, address : int):
        """[summary]

        Args:
            address (int): [description]

        Raises:
            ValueError: [description]
        """
        if isinstance(address, int) and address in range(0, 0xffff):
            if address not in self.breakpoints:
                self.breakpoints.append(address)
            else:
                self.breakpoints.remove(address)
        else:
            raise ValueError(f"Invalid breakpoint {address}")

    def clear_beakpoints(self):
        """Clear all breakpoints"""
        self.breakpoints = []
        self.logger.debug("All breakpoints are removed")

    def load_and_run(self, segments: List, entry_address: int, stop_address: int = None, cycles_count_start: int = None, cycles_count_end: int = None, debug_mode: bool = False) -> (CPU, MMU, int):
        """[summary]

        Args:
            segments (List[Segment]): [description]
            entry_address (int): [description]
            cycles_count_start (int, optional): [description]. Defaults to None.
            cycles_count_end (int, optional): [description]. Defaults to None.
            debug_mode (bool, optional): [description]. Defaults to False.

        Returns:
            CPU, MMU, int: [description]
        """
        low_ram = (0x0000, segments[0].start_adr, False)
        hi_ram = (segments[-1].end_adr, 0xffff, False)

        mmu_segments = []

        mmu_segments.append(low_ram)
        for seg in segments:
            bytecode = BytesIO(seg.get_segment_bytecode())
            mmu_s = (seg.start_adr, seg.end_adr - seg.start_adr, False, bytecode)
            mmu_segments.append(mmu_s)
        mmu_segments.append(hi_ram)

        self.logger.info(mmu_segments)
        self.debug_mode = debug_mode

        self.mmu = MMU(mmu_segments)
        self.cpu = CPU(self.mmu, entry_address)

        counting_enabled = False if cycles_count_start is not None else True
        stop_address = 0xffff if stop_address is None else stop_address

        self.logger.info(f"Loading code from {segments[0].start_adr:04X} to {segments[-1].end_adr:04X}")
        self.logger.debug(f"Set PC at {entry_address:04X}")
        self.logger.debug(f"Emulating from ${self.cpu.r.pc:04X} to ${stop_address:04X}")

        self.nb_cycles_used = 0
        current_bytecode = self.mmu.read(self.cpu.r.pc)
        current_instruction = Instruction.opcodes[current_bytecode]
        current_operand_size = Instruction.operand_sizes[current_instruction[1]]+1
        current_operand = [self.mmu.read(self.cpu.r.pc + 1 + i) for i in range(current_operand_size)]

        while(self.cpu.r.pc < stop_address and current_instruction[0] != 'brk'):
            try:
                if self.cpu.r.pc == cycles_count_start:
                    counting_enabled = True
                    self.logger.info(f"Starting to count cycle at ${self.cpu.r.pc:04X}")
                if self.cpu.r.pc == cycles_count_end:
                    counting_enabled = False
                    self.logger.info(f"Stopping to count cycle at ${self.cpu.r.pc:04X}")

                current_bytecode = self.mmu.read(self.cpu.r.pc)
                current_instruction = Instruction.opcodes[current_bytecode]
                current_operand_size = Instruction.operand_sizes[current_instruction[1]]+1
                current_operand = [self.mmu.read(self.cpu.r.pc+1+i) for i in range(current_operand_size)]

                if counting_enabled:
                    self.nb_cycles_used += self.cpu.cc

                if self.debug_mode or self.cpu.r.pc in self.breakpoints or self.breakpoint_in == 0:
                    print(f"${self.cpu.r.pc:04X}: {current_instruction[0]} [{current_instruction[1]}] (${int.from_bytes(current_operand, 'big'):02X})")
                    print(f"{self.cpu.r}")
                    if self.breakpoints:
                        print(f"Breakpoints: {[f'${bp:04X}' for bp in self.breakpoints]}")

                    inputs = self.get_input(f"${self.cpu.r.pc:04X}")
                    if inputs:
                        self.process_input(inputs, current_instruction, int.from_bytes(current_operand, 'big'), cycles_count_start)
                    else:
                        self.debug_mode = False
                else:
                    if counting_enabled and self.nb_cycles_used % 1000 == 0:
                        self.logger.info(f"Total: {self.nb_cycles_used} R: {self.cpu.r} CC: {self.cpu.cc}")

                    self.cpu.step()

                    if self.breakpoint_in > 0:
                        self.breakpoint_in -= 1

            except Exception as e:
                self.logger.critical(f"Emulation crashed at ${self.cpu.r.pc:04X} (bytecode {current_bytecode:02X}) due to {e.__class__}")
                self.logger.critical(f"{current_instruction} operand: {int.from_bytes(current_operand, 'big'):02X}")
                self.logger.critical(f"Registers: {self.cpu.r}")
                self.logger.critical(traceback.format_exc())
                break

        self.logger.info(f"Emulation stopped at ${self.cpu.r.pc:04X} with last instruction executed: {current_instruction[0]}")

        return self.cpu, self.mmu, self.nb_cycles_used

    def process_input(self, inputs, inst, operand, nb_cycles_start):
        """[summary]

        Args:
            inputs ([type]): [description]
            inst ([type]): [description]
            operand ([type]): [description]
            nb_cycles_start ([type]): [description]
        """
        if inputs['cmd'] == Action.READ_MEMORY:
            vals = [int(x) for x in inputs['args']]

            if len(vals) == 1:
                print(f"${vals[0]:04X}: {self.mmu.read(vals[0])}")
            else:
                delta = vals[1] - vals[0] + 1
                if delta < 1:
                    print(f"-> Memory range cannot be null or negative: ${delta:04X} = ${vals[1]:04X} - ${vals[0]:04X}")
                else:
                    modulo = 1 if delta % 16 != 0 else 0

                    for i in range((delta // 16) + modulo):
                        print(f"${vals[0]+(i*16):04X}: ", end= '')
                        for j in range(min(16, delta - (i*16))):
                            print(f"{self.mmu.read(vals[0]):02X}", end = ' ')
                        print()

        elif inputs['cmd'] == Action.READ_REGISTERS:
            if len(inputs['args']) == 0:
                print(f"Registers: {self.cpu.r}")
            else:
                for r in inputs['args']:
                    print(f"Register {r}: {eval(f'self.cpu.r.{r.lower()}')} | ${eval(f'self.cpu.r.{r.lower()}'):0X} | %{eval(f'self.cpu.r.{r.lower()}'):0b}")

        elif inputs['cmd'] == Action.RUN_NEXT:
            if len(inputs['args']) == 0:
                self.cpu.step()
            else:
                self.debug_mode = False
                self.breakpoint_in = int(inputs['args'][0])
                print(f"-> Program will stop in {self.breakpoint_in} instructions")

        elif inputs['cmd'] == Action.SHOW_INSTRUCTION:
            print(f"${self.cpu.r.pc:04X}: {' '.join(inst)} {operand:02X}")

        elif inputs['cmd'] == Action.SHOW_CYCLES_COUNT:
            if nb_cycles_start:
                print(f"${self.cpu.r.pc:04X}: {self.nb_cycles_used} cycles used since ${nb_cycles_start:04X}")
            else:
                print(f"${self.cpu.r.pc:04X}: {self.nb_cycles_used} cycles used")

        elif inputs['cmd'] == Action.SET_BREAKPOINT:
            if inputs['args']:
                for bp in [int(v) for v in inputs['args']]:
                    self.reset_breakpoint(bp)
                    print(f"-> Breakpoint added at ${bp:04X}")
            else:
                print(f"-> Breakpoints {[f'${bp:04X}' for bp in self.breakpoints]} cleared")
                self.clear_beakpoints()

        else:
            self.logger.warning(f"-> Debugger input {inputs} not managed!")

    def get_input(self, prompt: str):

        def memory_action(cmd_str, cmd_vars, cmd_dict):
            list_loc = cmd_vars.split(' ')
            addresses = []

            if len(list_loc) > 2:
                raise ValueError("too many addresses, should be one or a range")

            for loc in list_loc:
                addresses.append(self._parse_string_address(loc))

            res = f"!{Action.READ_MEMORY} {' '.join(addresses)}"
            return (COMMAND_ACTION_USE_VALUE, res)

        def registers_action(cmd_str, cmd_vars, cmd_dict):
            if cmd_vars:
                list_reg = [reg.upper() for reg in cmd_vars.split(' ')]
                for reg in list_reg:
                    if reg not in ['A', 'Y', 'X', 'P', 'S', 'PC']:
                        raise ValueError(f"Unknown register {reg}")

                res = f"!{Action.READ_REGISTERS} {' '.join(list_reg)}"
                return (COMMAND_ACTION_USE_VALUE, res)
            else:
                res = f"!{Action.READ_REGISTERS}"
                return (COMMAND_ACTION_USE_VALUE, res)

        def next_action(cmd_str, cmd_vars, cmd_dict):
            if cmd_vars:
                cmd_vars = int(cmd_vars, 0)

            res = f"!{Action.RUN_NEXT} {cmd_vars}"
            return (COMMAND_ACTION_USE_VALUE, res)

        def instruction_action(cmd_str, cmd_vars, cmd_dict):
            res = f"!{Action.SHOW_INSTRUCTION}"
            return (COMMAND_ACTION_USE_VALUE, res)

        def cycles_action(cmd_str, cmd_vars, cmd_dict):
            if cmd_vars:
                try:
                    nb = int(cmd_vars)
                except:
                    raise ValueError("Invalid number of instructions")
                res = f"!{Action.SHOW_CYCLES_COUNT} {cmd_vars}"
            else:
                res = f"!{Action.SHOW_CYCLES_COUNT}"

            return (COMMAND_ACTION_USE_VALUE, res)

        def breakpoint_action(cmd_str, cmd_vars, cmd_dict):
            if cmd_vars:
                list_loc = cmd_vars.split(' ')
                adresses = []
                for loc in list_loc:
                    adresses.append(self._parse_string_address(loc))

                res = f"!{Action.SET_BREAKPOINT} {' '.join(adresses)}"
                return (COMMAND_ACTION_USE_VALUE, res)
            else:
                res = f"!{Action.SET_BREAKPOINT}"
                return (COMMAND_ACTION_USE_VALUE, res)


        def cancel_action(cmd_str, cmd_vars, cmd_dict):
            return (COMMAND_ACTION_CANCEL, None)

        def show_help_action(cmd_str, cmd_vars, cmd_dict):
            print('Available commands:')
            print('? - show this message')
            print('e - exit simulator')
            print('n [nb]- run next nb instructions')
            print('m - show memory')
            print('r - show registers')
            print('i - show instruction')
            print('c - show cycles count')
            print('b - set/reset/clear breakpoints')

            return CommandResponse(COMMAND_ACTION_NOP, None)

        cmds = {
            '?': GetInputCommand(show_help_action),
            'e': GetInputCommand(cancel_action),
            'n': GetInputCommand(next_action),
            'm': GetInputCommand(memory_action),
            'r': GetInputCommand(registers_action),
            'i': GetInputCommand(instruction_action),
            'c': GetInputCommand(cycles_action),
            'b': GetInputCommand(breakpoint_action),
        }

        while True:
            try:
                result = ci.get_string(prompt=prompt, commands=cmds)

                if result[0] == '!':

                    res = result[1:].split(' ')
                    return {
                         "cmd": eval(res[0]),
                         "args": res[1:]
                    }
                else:
                    print(f"Unknown command {result}, enter ? for help")
            except ValueError as e:
                print(f"Bad format: {e}")
            except GetInputInterrupt:
                break

    def _parse_string_address(self, adr_string: str) -> str:
        try:
            if "$" in adr_string:
                val = str(int(adr_string[1:], 16))
            elif "0x" in adr_string:
                val = str(int(adr_string[2:], 16))
            else:
                val = str(int(adr_string))
        except Exception as e:
            raise ValueError(f"Cannot convert {adr_string} into address due to: {e}")

        return val