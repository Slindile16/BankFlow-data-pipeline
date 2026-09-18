"""Keep temporary test files isolated between terminal and automated runs."""

from pathlib import Path
from tempfile import TemporaryDirectory


def pytest_configure(config):
    """Avoid reusing pytest folders created under a different Windows identity."""
    if config.option.basetemp is not None:
        return

    # Each process owns a fresh directory, so earlier runs cannot leave behind
    # inaccessible files. Pytest manages only the child directory; Python cleans
    # up the enclosing temporary directory when this run ends.
    temporary_directory = TemporaryDirectory(prefix="bankflow-tests-")
    config.add_cleanup(temporary_directory.cleanup)
    config.option.basetemp = str(Path(temporary_directory.name) / "pytest")
