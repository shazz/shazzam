import logging
from io import BytesIO
import traceback

from py65emu.cpu import CPU
from py65emu.mmu import MMU

from shazzam.Instruction import Instruction


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

                if counting_enabled and nb_cycles_used % 1000 == 0:
                    self.logger.info(f"Total: {nb_cycles_used} R: {cpu.r} CC: {cpu.cc}")

                if debug_mode:
                    self.logger.info(f"Emulating at: ${cpu.r.pc:04X} the bytecode: {current_bytecode:02X}")
                    self.logger.info(f"{current_instruction} operand: {int.from_bytes(current_operand, 'big'):02X}")
                    self.logger.info(f"{cpu.r} CC: {cpu.cc}")
                    input()

                cpu.step()

            except Exception as e:
                self.logger.critical(f"Emulation crashed at ${cpu.r.pc:04X} (bytecode {current_bytecode:02X}) due to {e.__class__}")
                self.logger.critical(f"{current_instruction} operand: {int.from_bytes(current_operand, 'big'):02X}")
                self.logger.critical(f"Registers: {cpu.r}")
                self.logger.critical(traceback.format_exc())
                break

        self.logger.info(f"Emulation stopped at ${cpu.r.pc:04X} with last instruction {current_instruction[0]}")
        # exit()

        return cpu, mmu, nb_cycles_used
