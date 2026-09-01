"""Shared pytest configuration for the whole test-suite.

Running the tests must NEVER write to a developer's
``rpgmaker2godot.log``. Two structural guards enforce it:

* every test executes inside a fresh, empty working directory, so the
  default ``rpgmaker2godot.yaml`` lookup performed by
  ``configure_logging()`` cannot discover an ambient configuration
  left next to the sources;
* the ``rpgmaker2godot`` root logger is scrubbed before AND after each
  test, so no ``FileHandler`` can ever leak between tests.
"""

import logging

import pytest

LOGGER_ROOT = "rpgmaker2godot"


@pytest.fixture(autouse=True)
def _keep_tests_away_from_file_logging(
    monkeypatch,
    tmp_path,
):
    """Isolate every test from ambient file logging."""

    root_logger = logging.getLogger(LOGGER_ROOT)

    def _scrub_handlers() -> None:
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)
            handler.close()
        root_logger.setLevel(logging.NOTSET)

    _scrub_handlers()
    monkeypatch.chdir(tmp_path)

    yield

    _scrub_handlers()