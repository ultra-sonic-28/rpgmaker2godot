import logging
from pathlib import Path

import pytest
import yaml

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
    config_path = directory / "rpgmaker2godot.yaml"

    config_path.write_text(
        yaml.safe_dump({"logger": settings}),
        encoding="utf-8",
    )

    return config_path


def test_stays_silent_without_configuration_file(
    tmp_path: Path,
    capsys,
) -> None:
    activated = configure_logging(tmp_path / "missing.yaml")

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


def test_invalid_yaml_falls_back_to_silent(tmp_path: Path) -> None:
    config_path = tmp_path / "rpgmaker2godot.yaml"
    config_path.write_text("{not yaml", encoding="utf-8")

    assert configure_logging(config_path) is False


def test_missing_logger_section_stays_silent(tmp_path: Path) -> None:
    config_path = tmp_path / "rpgmaker2godot.yaml"
    config_path.write_text("enabled: true\n", encoding="utf-8")

    assert configure_logging(config_path) is False


def test_non_mapping_logger_section_stays_silent(tmp_path: Path) -> None:
    config_path = tmp_path / "rpgmaker2godot.yaml"
    config_path.write_text("logger: 42\n", encoding="utf-8")

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


def test_overwrite_mode_recreates_the_file(tmp_path: Path) -> None:
    log_file = tmp_path / "run.log"
    log_file.write_text(
        "stale records from a previous run\n",
        encoding="utf-8",
    )

    configure_logging(
        write_config(
            tmp_path,
            {
                "enabled": True,
                "level": "DEBUG",
                "file": str(log_file),
                "mode": "OVERWRITE",
            },
        ),
    )

    logger = get_logger(LOGGER_NAME)
    logger.info("fresh start")

    logging.shutdown()

    content = log_file.read_text(encoding="utf-8")

    assert "previous run" not in content
    assert "fresh start" in content


def test_mode_matching_is_case_insensitive(tmp_path: Path) -> None:
    log_file = tmp_path / "run.log"
    log_file.write_text("to be wiped\n", encoding="utf-8")

    configure_logging(
        write_config(
            tmp_path,
            {
                "enabled": True,
                "file": str(log_file),
                "mode": "overwrite",
            },
        ),
    )

    get_logger(LOGGER_NAME).info("only this survives")
    logging.shutdown()

    content = log_file.read_text(encoding="utf-8")

    assert "to be wiped" not in content
    assert "only this survives" in content


def test_append_mode_keeps_previous_records(tmp_path: Path) -> None:
    log_file = tmp_path / "run.log"
    log_file.write_text(
        "records from a previous run\n",
        encoding="utf-8",
    )

    configure_logging(
        write_config(
            tmp_path,
            {
                "enabled": True,
                "level": "DEBUG",
                "file": str(log_file),
                "mode": "APPEND",
            },
        ),
    )

    logger = get_logger(LOGGER_NAME)
    logger.info("appended record")

    logging.shutdown()

    content = log_file.read_text(encoding="utf-8")

    assert "records from a previous run" in content
    assert "appended record" in content


def test_absent_mode_defaults_to_appending(tmp_path: Path) -> None:
    log_file = tmp_path / "run.log"
    log_file.write_text(
        "kept without any mode setting\n",
        encoding="utf-8",
    )

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
    logger.info("newest record")

    logging.shutdown()

    content = log_file.read_text(encoding="utf-8")

    assert "kept without any mode setting" in content
    assert "newest record" in content


@pytest.mark.parametrize("raw_mode", ["ROTATE", "", 42, None])
def test_unrecognized_mode_falls_back_to_appending(
    tmp_path: Path,
    raw_mode: object,
) -> None:
    log_file = tmp_path / "run.log"
    log_file.write_text(
        "survives bogus modes\n",
        encoding="utf-8",
    )

    configure_logging(
        write_config(
            tmp_path,
            {
                "enabled": True,
                "file": str(log_file),
                "mode": raw_mode,
            },
        ),
    )

    logger = get_logger(LOGGER_NAME)
    logger.warning("still appended")

    logging.shutdown()

    content = log_file.read_text(encoding="utf-8")

    assert "survives bogus modes" in content
    assert "still appended" in content