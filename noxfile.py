import nox
import os
from pathlib import Path
import shutil

module_name = "shazzam"
nox.options.reuse_existing_virtualenvs = True

version = os.getenv("version_number", "0.0.1")

"""
This session will install the library
"""
@nox.session(python=False)
def install(session):
    """Install the library."""
    session.run("pip", "install", ".")

"""
This session will run the unit tests.
"""
@nox.session(python=["3.8"])
def tests(session):
    """Run the tests and coverage."""
    session.install("-r", "deployments/requirements_run.txt")
    session.install("-r", "deployments/requirements_test.txt")
    session.run("pytest", "-rs", "tests/")

    coverage_run_params = [
        "run", "-m", "pytest", '-W', 'ignore::UserWarning', "--html", "docs/reports/pytest/pytest.html", "-s"
    ]
    session.run("coverage", "report")
    session.run("coverage", "html", "-d", "docs/reports/coverage")

"""
This session will generate the docs.
"""
@nox.session(python=["3.8"])
def docs(session):
    """Generate the docs."""
    session.install("-r", "deployments/requirements_run.txt")
    session.install("-r", "deployments/requirements_docs.txt")

    shutil.rmtree('docs/html', ignore_errors=True)
    session.run("pdoc3", "-o", "docs/html", "--html", "shazzam", "examples")

"""
This session will install the 3rd party tools.
"""
@nox.session(python=False)
def install_3rd_party(session):

    # check deps
    session.run("make", "--version")
    session.run("cargo", "--version")
    session.run("wget", "--version")
    session.run("tar", "--version")
    session.run("unzip", "-h")
    session.run("gcc", "--version")

    shutil.rmtree('third_party', ignore_errors=True)

    os.makedirs("third_party", exist_ok = True)
    session.cd("third_party")

    # exomizer
    os.makedirs("exomizer", exist_ok = True)
    session.cd("exomizer")
    session.run("wget", "https://bitbucket.org/magli143/exomizer/wiki/downloads/exomizer-3.1.0.zip")
    session.run("unzip", "exomizer-3.1.0.zip")
    session.cd("src")
    session.run("make")
    session.run("cp", "exomizer", "..")
    session.cd("..")
    session.run("rm", "exomizer-3.1.0.zip")
    session.cd("..")

    # apultra
    session.run("git", "clone", "https://github.com/emmanuel-marty/apultra.git")
    session.cd("apultra")
    session.run("make", "all")
    session.cd("..")

    # lzsa
    session.run("git", "clone", "https://github.com/emmanuel-marty/lzsa.git")
    session.cd("lzsa")
    session.run("make", "all")
    session.cd("..")

    # pucrunch
    session.run("git", "clone", "https://github.com/mist64/pucrunch.git")
    session.cd("pucrunch")
    session.run("make", "all")
    session.cd("..")

    # nucrunch
    session.run("wget", "https://csdb.dk/release/download.php?id=206619", "-O", "nucrunch.tgz")
    session.run("tar", "-xvzf", "nucrunch.tgz")
    session.run("mv", "nucrunch-1.0.1", "nucrunch")
    session.cd("nucrunch")
    session.run("make")
    session.run("cp", "target/release/nucrunch", ".")
    session.cd("..")
    session.run("rm", "nucrunch.tgz")

    # doynamite
    session.run("wget", "https://csdb.dk/release/download.php?id=160764", "-O", "doynamite.tar.gz")
    session.run("tar", "-xvzf", "doynamite.tar.gz")
    session.run("mv", "doynamite1.1", "doynamite")
    session.cd("doynamite")
    session.run("gcc", "lz.c", "-o", "lz")
    session.cd("..")
    session.run("rm", "doynamite.tar.gz")

    # Sparkle
    session.run("wget", "https://csdb.dk/release/download.php?id=241780", "-O", "sparkle.zip")
    session.run("unzip", "sparkle.zip", "-d", "sparkle")
    session.run("rm", "sparkle.zip")

    # cc65
    session.run("git", "clone", "https://github.com/cc65/cc65.git")
    session.cd("cc65")
    session.run("make", "all")
    session.cd("..")