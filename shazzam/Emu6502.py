import logging
from io import BytesIO
import traceback
from enum import Enum, auto

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

class Emu6502():

    def __init__(self):
        self.logger = logging.getLogger("shazzam")

    def load_and_run(self, bytecode: BytesIO, seg_start_address: int, seg_stop_address: int, seg_entry_address: int, cycles_count_start: int = None, cycles_count_end: int = None, debug_mode: bool = False) -> CPU:
        """[summary]

        Args:
            bytecode (BytesIO): [description]
            seg_start_address (int): [description]
            seg_stop_address (int): [description]
            seg_entry_address ([type]): [description]

        Returns:
            CPU: [description]
        """
        self.logger.info(f"Loading code from {seg_start_address:04X} to {seg_stop_address:04X}")
        self.logger.debug(f"Set PC at {seg_entry_address:04X}")

        # bytecode copy for debugging as read() advances the buffer
        from copy import deepcopy
        debug_bytecode = deepcopy(bytecode).read()

        low_ram = (0x00, seg_start_address, False)
        hi_ram = (seg_stop_address, 0xffff, False)

        mmu = MMU([
            low_ram,
            (seg_start_address, seg_stop_address - seg_start_address, False, bytecode),
            hi_ram
        ])

        cpu = CPU(mmu, seg_entry_address)

        # for i in range(seg_stop_address - seg_start_address):
        #     self.logger.debug(hex(mmu.read(seg_start_address+i)))

        # for i in range(seg_stop_address - seg_start_address):
        #     self.logger.debug(f"{seg_start_address+i:04X}: {mmu.read(seg_start_address+i):02X}")


        counting_enabled = False if cycles_count_start is not None else True
        self.logger.debug(f"Emulating from ${cpu.r.pc:04X} to ${seg_stop_address:04X}")

        nb_cycles_used = 0
        current_bytecode = debug_bytecode[cpu.r.pc-seg_start_address]
        current_instruction = Instruction.opcodes[debug_bytecode[cpu.r.pc-seg_start_address]]
        while(cpu.r.pc < seg_stop_address and current_instruction[0] != 'brk'):
            try:
                if cpu.r.pc == cycles_count_start:
                    counting_enabled = True
                    self.logger.info(f"Starting to count cycle at ${cpu.r.pc:04X}")
                if cpu.r.pc == cycles_count_end:
                    counting_enabled = False
                    self.logger.info(f"Stopping to count cycle at ${cpu.r.pc:04X}")

                current_bytecode = debug_bytecode[cpu.r.pc-seg_start_address]
                current_instruction = Instruction.opcodes[debug_bytecode[cpu.r.pc-seg_start_address]]
                current_operand_size = Instruction.operand_sizes[current_instruction[1]]+1
                current_operand = debug_bytecode[cpu.r.pc-seg_start_address + 1:cpu.r.pc-seg_start_address+current_operand_size]

                if counting_enabled:
                    nb_cycles_used += cpu.cc

                if debug_mode:
                    # self.logger.info(f"Emulating at: ${cpu.r.pc:04X} the bytecode: {current_bytecode:02X}")
                    # self.logger.info(f"{current_instruction} operand: {int.from_bytes(current_operand, 'big'):02X}")
                    # self.logger.info(f"{cpu.r} CC: {cpu.cc}")
                    inputs = self.get_input(f"${cpu.r.pc:04X}")
                    if inputs:
                        self.process_input(inputs, cpu, mmu, current_instruction, int.from_bytes(current_operand, 'big'), nb_cycles_used, cycles_count_start)
                    else:
                        debug_mode = False
                else:
                    if counting_enabled and nb_cycles_used % 1000 == 0:
                        self.logger.info(f"Total: {nb_cycles_used} R: {cpu.r} CC: {cpu.cc}")
                    cpu.step()

            except Exception as e:
                self.logger.critical(f"Emulation crashed at ${cpu.r.pc:04X} (bytecode {current_bytecode:02X}) due to {e.__class__}")
                self.logger.critical(f"{current_instruction} operand: {int.from_bytes(current_operand, 'big'):02X}")
                self.logger.critical(f"Registers: {cpu.r}")
                self.logger.critical(traceback.format_exc())
                break

        self.logger.info(f"Emulation stopped at ${cpu.r.pc:04X} with last instruction {current_instruction[0]}")

        return cpu, mmu, nb_cycles_used

    def process_input(self, inputs, cpu, mmu, inst, operand, nb_cycles_used, nb_cycles_start):

        if inputs['cmd'] == Action.READ_MEMORY:
            vals = [int(x) for x in inputs['args']]

            if len(vals) == 1:
                print(f"${vals[0]:04X}: {mmu.read(vals[0])}")
            else:
                delta = vals[1] - vals[0]
                modulo = 1 if delta % 16 != 0 else 0

                for i in range((delta // 16) + modulo):
                    print(f"${vals[0]+(i*16):04X}: ", end= '')
                    for j in range(min(16, delta - (i*16))):
                        print(f"{mmu.read(vals[0]):02X}", end = ' ')
                    print()

        elif inputs['cmd'] == Action.READ_REGISTERS:
            if len(inputs['args']) == 0:
                print(f"Registers: {cpu.r}")
            else:
                for r in inputs['args']:
                    print(f"Register {r}: {eval(f'cpu.r.{r.lower()}')} | ${eval(f'cpu.r.{r.lower()}'):0X} | %{eval(f'cpu.r.{r.lower()}'):0b}")

        elif inputs['cmd'] == Action.RUN_NEXT:
            if len(inputs['args']) == 0:
                print(f"${cpu.r.pc:04X}: {' '.join(inst)} {operand:02X}")
                cpu.step()

        elif inputs['cmd'] == Action.SHOW_INSTRUCTION:
            print(f"${cpu.r.pc:04X}: {' '.join(inst)} {operand:02X}")

        elif inputs['cmd'] == Action.SHOW_CYCLES_COUNT:
            if nb_cycles_start:
                print(f"${cpu.r.pc:04X}: {nb_cycles_used} cycles used since ${nb_cycles_start:04X}")
            else:
                print(f"${cpu.r.pc:04X}: {nb_cycles_used} cycles used")

    def get_input(self, prompt: str):

        def memory_action(cmd_str, cmd_vars, cmd_dict):
            list_loc = cmd_vars.split(' ')
            if len(list_loc) > 2:
                raise ValueError("too many locations")

            # check hex
            vals = [int(x, 0) for x in list_loc]
            if len(vals) == 2:
                if vals[1] - vals[0] < 0:
                   raise ValueError("negative memory range")

            res = f"!{Action.READ_MEMORY} {' '.join(list_loc)}"
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
            res = f"!{Action.SHOW_CYCLES_COUNT}"
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
            return CommandResponse(COMMAND_ACTION_NOP, None)

        cmds = {
            '?': GetInputCommand(show_help_action),
            'e': GetInputCommand(cancel_action),
            'n': GetInputCommand(next_action),
            'm': GetInputCommand(memory_action),
            'r': GetInputCommand(registers_action),
            'i': GetInputCommand(instruction_action),
            'c': GetInputCommand(cycles_action),
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
