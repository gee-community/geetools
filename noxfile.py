"""All the process that can be run using nox.

The nox run are build in isolated environment that will be stored in .nox. to force the venv update, remove the .nox/xxx folder.
"""

import nox

nox.options.sessions = ["lint", "test", "docs", "mypy"]


@nox.session(reuse_venv=True)
def lint(session):
    """Apply the pre-commits."""
    session.install("pre-commit")
    session.run("pre-commit", "run", "--all-files", *session.posargs)


@nox.session(reuse_venv=True)
def test(session):
    """Run all the test using the environment variable of the running machine."""
    session.install(".[test]")
    test_files = session.posargs or ["tests"]
    session.run(
        "pytest",
        "--color=yes",
        "--cov",
        "--cov-report=xml",
        *test_files,
    )


@nox.session(reuse_venv=True, name="dead-fixtures")
def dead_fixtures(session):
    """Check for dead fixtures within the tests."""
    session.install(".[test]")
    session.run("pytest", "--dead-fixtures")


@nox.session(reuse_venv=True)
def docs(session):
    """Build the documentation."""
    build = session.posargs.pop() if session.posargs else "html"
    session.install(".[doc]")
    dst, warn = f"docs/_build/{build}", "warnings.txt"
    session.run("sphinx-build", "-v", "-b", build, "docs", dst, "-w", warn)


@nox.session(name="mypy", reuse_venv=True)
def mypy(session):
    """Run a mypy check of the lib."""
    session.install("mypy")
    test_files = session.posargs or ["geetools"]
    session.run("mypy", *test_files)


@nox.session(reuse_venv=True)
def stubgen(session):
    """Generate stub files for the lib but requires human attention before merge."""
    session.install("mypy")
    package = session.posargs or ["geetools"]
    session.run("stubgen", "-p", package[0], "-o", "stubs", "--include-private")
