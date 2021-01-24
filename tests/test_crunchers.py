import sys
sys.path.append(".")
from shazzam.py64gen import *

import importlib
import pytest
from pytest_cases import parametrize_with_cases
from tests.cases_crunchers import CrunchersPrgCases

@parametrize_with_cases('driver, cruncher_path, extra_params', cases=CrunchersPrgCases, prefix='cruncher')
def test_cruncher_prg_drivers(driver, cruncher_path, extra_params):

    test_file = "tests/cases/crunchers/demo2.prg"

    module = importlib.import_module(driver)
    class_ = getattr(module, driver.split('.')[-1])
    cruncher = class_(cruncher_path)

    print(f"calling driver {cruncher}")
    cruncher.crunch_prg(filename=test_file, extra_params=extra_params)
