import nox
import os
from pathlib import Path
import shutil

module_name = "shazzam"
nox.options.reuse_existing_virtualenvs = True

version = os.getenv("version_number", "0.0.1")

"""
This session will run the unit tests.
"""
@nox.session(python=["3.8"])
def tests(session):
    """Launchs the tests and coverage."""
    session.install("-r", "deployments/requirements_run.txt")
    session.install("-r", "deployments/requirements_test.txt")
    session.run("pytest", "-rs", "tests/test_opcodes.py")

    # coverage_run_params = [
    #     "run", "-m", "pytest", '-W', 'ignore::UserWarning', "--html", "docs/reports/pytest/pytest.html", "-s"
    # ]
    # session.run("coverage", "report")
    # session.run("coverage", "html", "-d", "docs/reports/coverage")

@nox.session(python=["3.8"])
def docs(session):
    """Generate the docs."""
    session.install("-r", "deployments/requirements_run.txt")
    session.install("-r", "deployments/requirements_docs.txt")

    shutil.rmtree('docs/html', ignore_errors=True)
    session.run("pdoc3", "-o", "docs/html", "--html", "shazzam", "examples")

@nox.session(python=False)
def install_3rd_party(session):

    # check deps
    session.run("make", "--version")
    session.run("cargo", "--version")
    session.run("wget", "--version")
    session.run("tar", "--version")
    session.run("unzip", "--version")

    shutil.rmtree('third_party', ignore_errors=True)

    os.makedirs("third_party", exist_ok = True)
    session.cd("third_party")

    # cc65
    session.run("git", "clone", "https://github.com/cc65/cc65.git")
    session.cd("cc65")
    session.run("make", "all")

    # exomizer
    session.cd("..")
    os.makedirs("exomizer", exist_ok = True)
    session.cd("exomizer")
    session.run("wget", "https://bitbucket.org/magli143/exomizer/wiki/downloads/exomizer-3.1.0.zip")
    session.run("unzip", "exomizer-3.1.0.zip")

    # apultra
    session.cd("..")
    session.run("git", "clone", "https://github.com/emmanuel-marty/apultra.git")
    session.cd("apultra")
    session.run("make", "all")

    # apultra
    session.cd("..")
    session.run("git", "clone", "https://github.com/emmanuel-marty/lzsa.git")
    session.cd("lzsa")
    session.run("make", "all")

    # pucrunch
    session.cd("..")
    session.run("git", "clone", "https://github.com/mist64/pucrunch.git")
    session.cd("pucrunch")
    session.run("make", "all")

    # nucrunch
    session.cd("..")
    session.run("wget", "https://csdb.dk/release/download.php?id=206619", "-O", "nucrunch.tgz")
    session.run("tar", "-xvzf", "nucrunch.tgz")
    session.run("mv", "nucrunch-1.0.1", "nucrunch")
    session.cd("nucrunch")
    session.run("make")



