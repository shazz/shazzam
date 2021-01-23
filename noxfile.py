import nox
import os
from pathlib import Path
import shutil

module_name = "py64gen"

# set the default acrivated sessions, minimal for CI
nox.options.reuse_existing_virtualenvs = True

version = os.getenv("version_number", "0.0.1")

"""
This session will run the unit tests.
"""
@nox.session(python=["3.8"])
def run(session):
    """Run the component entry point. (not for CI)"""
    session.install("-r", "deployments/requirements_run.txt")
    session.chdir(".") # TODO: replace by the targeted path
    session.run("my command line") # TODO: replace to run the code

@nox.session(python=["3.8"])
def test(session):
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