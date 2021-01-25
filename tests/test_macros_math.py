import sys
sys.path.append(".")

from shazzam.py64gen import *
import shazzam.macros.macros_math as m

def test_add16():

    for n1 in range(300):
        for n2 in range(250, 260):

            with segment(0x0801, "test_add16", check_address_dups=False) as s:
                m.add16("n1", "n2", "res")
                brk()

                label(name="n1")
                byte(n1 & 0xff)
                byte(n1 >> 8)

                label(name="n2")
                byte(n2 & 0xff)
                byte(n2 >> 8)

                label(name="res")
                byte(0)
                byte(0)
                cpu, mmu = s.emulate()
                assert ((mmu.read(get_current_address()-1)*256) + mmu.read(get_current_address()-2)) == n1+n2, f"add16 should be {n1+n2}"

def test_add8_to_16():

    for i in range(256):
        for r in range(240, 260):

            with segment(0x0, "test_add8_to_16", check_address_dups=False) as s:
                m.add8_to_16(i, "res")
                brk()

                label(name="res")
                byte(r & 0xff)
                byte(r >> 8)

                cpu, mmu = s.emulate()
                assert ((mmu.read(get_current_address()-1)*256) + mmu.read(get_current_address()-2)) == (i+r) & 0xffff, f"add8_to_16 should be {(i+r) & 0xffff}"

def test_sub8_to_16():

    for i in range(230, 256):
        for r in range(240, 260):

            with segment(0x0, "test_sub8_to_16", check_address_dups=False) as s:
                m.sub8_to_16(i, "res")
                brk()

                label(name="res")
                byte(r & 0xff)
                byte(r >> 8)

                cpu, mmu = s.emulate()
                result = (mmu.read(get_current_address()-1)*256) + mmu.read(get_current_address()-2)
                assert  result == (r-i) & 0xffff , f"sub8_to_16 should be {(r-i) & 0xffff} and not {result}"

def test_inc16():

    for r in range(200, 300):

        with segment(0x0, "test_inc16", check_address_dups=False) as s:
            m.inc16("res")
            brk()

            label(name="res")
            byte(r & 0xff)
            byte(r >> 8)

            cpu, mmu = s.emulate()
            result = (mmu.read(get_current_address()-1)*256) + mmu.read(get_current_address()-2)
            assert  result == (r+1) & 0xffff , f"inc16 should be {(r+1) & 0xffff} and not {result}"

def test_dec16():

    for r in range(200, 300):

        with segment(0x0, "test_dec16", check_address_dups=False) as s:
            m.dec16("res")
            brk()

            label(name="res")
            byte(r & 0xff)
            byte(r >> 8)

            cpu, mmu = s.emulate()
            result = (mmu.read(get_current_address()-1)*256) + mmu.read(get_current_address()-2)
            assert  result == (r-1) & 0xffff , f"Dec16 should be {(r-1) & 0xffff} and not {result}"

def test_sub16():

    for n1 in range(240, 260):

        for n2 in range(240, 260):

            with segment(0x0, "test_sub16", check_address_dups=False) as s:
                m.sub16("n1", "n2", "res")
                brk()

                label(name="n1")
                byte(n1 & 0xff)
                byte(n1 >> 8)

                label(name="n2")
                byte(n2 & 0xff)
                byte(n2 >> 8)

                label(name="res")
                byte(0)
                byte(0)

                cpu, mmu = s.emulate()
                result = (mmu.read(get_current_address()-1)*256) + mmu.read(get_current_address()-2)
                assert  result == (n1-n2) & 0xffff , f"sub16 should be {(n1-n2) & 0xffff} and not {result}"
