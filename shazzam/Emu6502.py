import logging
from io import BytesIO

from py65emu.cpu import CPU
from py65emu.mmu import MMU

from shazzam.Instruction import Instruction


class Emu6502():

    def __init__(self):
        self.logger = logging.getLogger("shazzam")

    def load_and_run(self, bytecode: BytesIO, seg_start_address: int, seg_stop_address: int, seg_entry_address) -> CPU:
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

        low_ram = (0x00, seg_start_address-1)
        hi_ram = (seg_stop_address, 0xffff)

        mmu = MMU([
            low_ram,
            (seg_start_address, seg_stop_address -
             seg_start_address, False, bytecode),
            hi_ram
        ])

        cpu = CPU(mmu, seg_entry_address)

        # for i in range(seg_stop_address - seg_start_address):
        #     self.logger.debug(hex(mmu.read(seg_start_address+i)))

        # for i in range(seg_stop_address - seg_start_address):
        #     self.logger.debug(f"{seg_start_address+i:04X}: {mmu.read(seg_start_address+i):02X}")

        self.logger.debug(f"Emulating from ${cpu.r.pc:04X} to ${seg_stop_address:04X}")

        current_bytecode = debug_bytecode[cpu.r.pc-seg_start_address]
        current_instruction = Instruction.opcodes[debug_bytecode[cpu.r.pc-seg_start_address]]
        current_operand_size = Instruction.operand_sizes[current_instruction[1]]+1
        current_operand = debug_bytecode[cpu.r.pc-seg_start_address+1:cpu.r.pc-seg_start_address+current_operand_size]
        self.logger.debug(f"Emulating at: ${cpu.r.pc:04X} the bytecode: {current_bytecode:02X}")
        self.logger.debug(f"{current_instruction} operand: {hex(int.from_bytes(current_operand, 'big'))}")
        self.logger.debug(cpu.r)

        while(cpu.r.pc < seg_stop_address and current_instruction[0] != 'brk'):
            try:
                cpu.step()
                # input()

                current_bytecode = debug_bytecode[cpu.r.pc-seg_start_address]
                current_instruction = Instruction.opcodes[debug_bytecode[cpu.r.pc-seg_start_address]]
                current_operand_size = Instruction.operand_sizes[current_instruction[1]]+1
                current_operand = debug_bytecode[cpu.r.pc-seg_start_address + 1:cpu.r.pc-seg_start_address+current_operand_size]
                self.logger.debug(f"Emulating at: ${cpu.r.pc:04X} the bytecode: {current_bytecode:02X}")
                self.logger.debug(f"{current_instruction} operand: {hex(int.from_bytes(current_operand, 'big'))}")
                self.logger.debug(cpu.r)

            except Exception as e:
                self.logger.critical(
                    f"Emulation crashed at ${cpu.r.pc:04X} due to {e.__class__}")
                # self.logger.debug(traceback.format_exc())
                break

        return cpu, mmu
