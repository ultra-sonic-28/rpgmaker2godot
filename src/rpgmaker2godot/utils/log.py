"""Configurable logging helpers for the CLI pipeline.

Logging is opt-in and file-only: without a configuration file the
whole pipeline stays silent, and activated records are written to
the configured file — never to the console.

Drop a ``logging.json`` file in the working directory (or pass an
explicit path to :func:`configure_logging`) to activate:

.. code-block:: json

    {
        "enabled": true,
        "level": "DEBUG",
        "file": "rpgmaker2godot.log",
        "mode": "OVERWRITE"
    }

* ``enabled``: master switch (absent or false keeps logging off);
* ``level``: minimal severity — DEBUG, INFO, WARNING, ERROR;
* ``file``: required path — the sole destination of the records;
* ``mode``: ``OVERWRITE`` recreates the file at startup while
  ``APPEND`` adds records at its end — absent or unrecognized
  values fall back to ``APPEND``.
"""

import json
import logging
from pathlib import Path

_LOGGER_ROOT = "rpgmaker2godot"
_DEFAULT_CONFIG_FILENAME = "logging.json"

# Default fate of an existing log file when logging activates:
# records keep being added at the end of the file.
_DEFAULT_LOG_MODE = "APPEND"

# Supported values of the "mode" setting, mapped to the open mode
# they translate to for the underlying FileHandler.
_FILE_MODES = {
    "APPEND": "a",
    "OVERWRITE": "w",
}

_SILENT_LEVEL = logging.CRITICAL + 1


def get_logger(
    name: str,
) -> logging.Logger:
    """Return a child logger of the rpgmaker2godot root logger."""

    return logging.getLogger(f"{_LOGGER_ROOT}.{name}")


def configure_logging(
    config_path: Path | None = None,
) -> bool:
    """Configure every rpgmaker2godot logger from a JSON file.

    The call is idempotent: previously installed handlers are removed
    before the new configuration is applied.

    Records are written to the configured file only — never to the
    console. The ``file`` setting is therefore required for anything
    to be captured.

    Args:
        config_path: Explicit path to the configuration file. When
            omitted, ``logging.json`` is looked up in the current
            working directory.

    Returns:
        Whether logging got activated.
    """

    if config_path is None:
        config_path = Path.cwd() / _DEFAULT_CONFIG_FILENAME

    root = logging.getLogger(_LOGGER_ROOT)

    _remove_handlers(root)

    settings = _load_settings(config_path)

    if not settings.get("enabled", False):
        root.setLevel(_SILENT_LEVEL)
        return False

    output_file = settings.get("file")

    if not output_file:
        # File-only logging: without a destination there is nothing
        # to capture, so stay silent.
        root.setLevel(_SILENT_LEVEL)
        return False

    root.setLevel(
        _parse_level(settings.get("level", "DEBUG")),
    )

    file_handler = logging.FileHandler(
        output_file,
        mode=_parse_mode(settings.get("mode", _DEFAULT_LOG_MODE)),
        encoding="utf-8",
    )
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        ),
    )
    root.addHandler(file_handler)

    return True


def _load_settings(
    config_path: Path,
) -> dict:
    """Load the JSON settings, falling back to 'disabled'."""

    if not config_path.is_file():
        return {}

    try:
        settings = json.loads(
            config_path.read_text(encoding="utf-8"),
        )
    except (json.JSONDecodeError, OSError):
        return {}

    if not isinstance(settings, dict):
        return {}

    return settings


def _parse_level(
    raw_level: object,
) -> int:
    """Translate a textual severity into its numeric value."""

    level_name = str(raw_level).upper()

    return getattr(logging, level_name, logging.DEBUG)


def _parse_mode(
    raw_mode: object,
) -> str:
    """Translate a textual log-file mode into its open-mode flag."""

    mode_name = str(raw_mode).upper()

    return _FILE_MODES.get(
        mode_name,
        _FILE_MODES[_DEFAULT_LOG_MODE],
    )


def _remove_handlers(
    logger: logging.Logger,
) -> None:
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()