import pytest
from pytest_cases import case, parametrize

class CrunchersPrgCases:

    @parametrize("driver, cruncher_path, extra_params",
                 [("shazzam.drivers.crunchers.Exomizer", "/home/shazz/projects/c64/bin/exomizer", None),
                  ("shazzam.drivers.crunchers.Exomizer", "/home/shazz/projects/c64/bin/exomizer", ["-v"]),
                  ("shazzam.drivers.crunchers.Apultra", "/home/shazz/projects/c64/bin/apultra", None),
                 ])

    def cruncher_prg_drivers(self, driver, cruncher_path, extra_params):

        return driver, cruncher_path, extra_params