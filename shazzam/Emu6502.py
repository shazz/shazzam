from io import BytesIO
import traceback

import logging

from shazzam.Instruction import Instruction

from py65emu.cpu import CPU
from py65emu.mmu import MMU

class Emu6502():

    def __init__(self):
        self.logger = logging.getLogger("shazzam")

    def load_and_run(self, bytecode: BytesIO, seg_start_address: int, seg_stop_address: int, seg_entry_address) -> CPU:

        self.logger.info(f"Loading code from {seg_start_address:04X} to {seg_stop_address:04X}")
        self.logger.info(f"Set PC at {seg_entry_address:04X}")

        # bytecode copy for debugging as read() advances the buffer
        from copy import deepcopy
        debug_bytecode = deepcopy(bytecode).read()

        low_ram = (0x00, seg_start_address-1)
        hi_ram = (seg_stop_address, 0xffff)

        # 0x0000 - 0x0200: zp and stack
        # Segment
        # mmu = MMU([
        #     (0x00, 0x200),
        #     (0xD000, 0x1000),
        #     (seg_start_address, seg_stop_address - seg_start_address, True, bytecode)
        # ])

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
                input()

                current_bytecode = debug_bytecode[cpu.r.pc-seg_start_address]
                current_instruction = Instruction.opcodes[debug_bytecode[cpu.r.pc-seg_start_address]]
                current_operand_size = Instruction.operand_sizes[current_instruction[1]]+1
                current_operand = debug_bytecode[cpu.r.pc-seg_start_address+1:cpu.r.pc-seg_start_address+current_operand_size]
                self.logger.debug(f"Emulating at: ${cpu.r.pc:04X} the bytecode: {current_bytecode:02X}")
                self.logger.debug(f"{current_instruction} operand: {hex(int.from_bytes(current_operand, 'big'))}")
                self.logger.debug(cpu.r)

            except Exception as e:
                self.logger.critical(f"Emulation crashed at ${cpu.r.pc:04X} due to {e.__class__}")
                # self.logger.debug(traceback.format_exc())
                break

        return cpu, mmu

        # define your blocks of memory.  Each tuple is
        # (start_address, length, readOnly=True, value=None, valueOffset=0)
        # m = MMU([
        #         (0x00, 0x200), # Create RAM with 512 bytes
        #         (0x1000, 0x4000, True, f) # Create ROM starting at 0x1000 with your program.
        # ])

        # # Create the CPU with the MMU and the starting program counter address
        # # You can also optionally pass in a value for stack_page, which defaults
        # # to 1, meaning the stack will be from 0x100-0x1ff.  As far as I know this
        # # is true for all 6502s, but for instance in the 6507 used by the Atari
        # # 2600 it is in the zero page, stack_page=0.
        # c = CPU(mmu, 0x1000)

        # # Do this to execute one instruction
        # c.step()

        # # You can check the registers and memory values to determine what has changed
        # logger.debug(c.r.a)     # A register
        # logger.debug(c.r.x)     # X register
        # logger.debug(c.r.y)     # Y register
        # logger.debug(c.r.s)     # Stack Pointer
        # logger.debug(c.r.pc)    # Program Counter

        # logger.debug(c.r.getFlag('C')) # Get the value of a flag from the flag register.

        # logger.debug(mmu.read(0xff)) # Read a value from memory