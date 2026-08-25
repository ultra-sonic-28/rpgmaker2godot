import json
import logging
from pathlib import Path

import pytest

from rpgmaker2godot.utils.log import (
    configure_logging,
    get_logger,
)

LOGGER_NAME = "rpgmaker2godot.test"


@pytest.fixture(autouse=True)
def _restore_logging_state():
    """Leave the global logging state exactly as found."""

    yield

    root = logging.getLogger("rpgmaker2godot")

    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()

    root.setLevel(logging.NOTSET)


def write_config(
    directory: Path,
    settings: dict,
) -> Path:
    config_path = directory / "logging.json"

    config_path.write_text(
        json.dumps(settings),
        encoding="utf-8",
    )

    return config_path


def test_stays_silent_without_configuration_file(
    tmp_path: Path,
    capsys,
) -> None:
    activated = configure_logging(tmp_path / "missing.json")

    logger = get_logger(LOGGER_NAME)

    assert activated is False

    logger.warning("should not appear")
    logger.debug("neither should this")

    captured = capsys.readouterr()

    assert captured.out == ""
    assert captured.err == ""


def test_activates_from_config_file(tmp_path: Path, capsys) -> None:
    log_file = tmp_path / "run.log"

    configure_logging(
        write_config(
            tmp_path,
            {
                "enabled": True,
                "level": "DEBUG",
                "file": str(log_file),
            },
        ),
    )

    logger = get_logger(LOGGER_NAME)
    logger.debug("hello %s", "world")

    logging.shutdown()

    captured = capsys.readouterr()

    # File-only logging: nothing reaches the console.
    assert captured.out == ""
    assert captured.err == ""
    assert "hello world" in log_file.read_text(encoding="utf-8")


def test_respects_configured_level(tmp_path: Path) -> None:
    log_file = tmp_path / "run.log"

    configure_logging(
        write_config(
            tmp_path,
            {
                "enabled": True,
                "level": "WARNING",
                "file": str(log_file),
            },
        ),
    )

    logger = get_logger(LOGGER_NAME)
    logger.debug("filtered out")
    logger.warning("kept")

    logging.shutdown()

    records = log_file.read_text(encoding="utf-8")

    assert "filtered out" not in records
    assert "kept" in records


def test_writes_records_to_configured_file(tmp_path: Path) -> None:
    log_file = tmp_path / "run.log"

    configure_logging(
        write_config(
            tmp_path,
            {
                "enabled": True,
                "level": "INFO",
                "file": str(log_file),
            },
        ),
    )

    logger = get_logger(LOGGER_NAME)
    logger.info("file record %d", 42)

    logging.shutdown()

    assert "file record 42" in log_file.read_text(encoding="utf-8")


def test_enabled_without_file_stays_silent(tmp_path: Path, capsys) -> None:
    assert (
        configure_logging(
            write_config(tmp_path, {"enabled": True}),
        )
        is False
    )

    logger = get_logger(LOGGER_NAME)
    logger.warning("nowhere to go")

    captured = capsys.readouterr()

    assert captured.out == ""
    assert captured.err == ""


def test_invalid_json_falls_back_to_silent(tmp_path: Path) -> None:
    config_path = tmp_path / "logging.json"
    config_path.write_text("{not json", encoding="utf-8")

    assert configure_logging(config_path) is False


def test_disabling_flag_keeps_logging_off(tmp_path: Path) -> None:
    assert (
        configure_logging(
            write_config(tmp_path, {"enabled": False}),
        )
        is False
    )


def test_reconfiguration_replaces_handlers(tmp_path: Path) -> None:
    root = logging.getLogger("rpgmaker2godot")

    first_log = tmp_path / "first.log"
    second_log = tmp_path / "second.log"

    first = write_config(
        tmp_path,
        {"enabled": True, "file": str(first_log)},
    )
    second = write_config(
        tmp_path,
        {"enabled": True, "file": str(second_log)},
    )

    configure_logging(first)
    handlers_after_first = len(root.handlers)

    assert handlers_after_first == 1

    configure_logging(second)

    # Reconfiguring must not stack handlers.
    assert len(root.handlers) == handlers_after_first