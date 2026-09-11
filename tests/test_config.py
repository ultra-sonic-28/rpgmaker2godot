from pathlib import Path

import pytest
import yaml

from rpgmaker2godot.utils.config import (
    DEFAULT_CONFIG_FILENAME,
    DEFAULT_INPUT_DIRECTORY,
    DEFAULT_OUTPUT_DIRECTORY,
    load_app_config,
    load_document,
    load_section,
    missing_converter_paths,
    read_yaml_document,
    resolve_config_path,
)

SAMPLE = {
    "converter": {
        "path": {
            "input": "./test-data",
            "output": "./output",
        },
    },
    "logger": {
        "enabled": True,
        "level": "DEBUG",
        "file": "run.log",
        "mode": "OVERWRITE",
    },
    "tileset": {"path": "world/tilesets"},
    "character": {
        "path": "entities/player/sprites",
        "idle": {"speed": 3.0, "duration": 1.0, "loop": 1},
        "walk": {"speed": 6.0, "duration": 1.0, "loop": 1},
        "damaged": {"speed": 5.0, "duration": 1.0, "loop": 1},
    },
}


def write_config(
    directory: Path,
    data: dict,
) -> Path:
    config_path = directory / "rpgmaker2godot.yaml"

    config_path.write_text(
        yaml.safe_dump(data),
        encoding="utf-8",
    )

    return config_path


def test_loads_the_full_configuration(tmp_path: Path) -> None:
    config = load_app_config(write_config(tmp_path, SAMPLE))

    assert config.tileset.path == "world/tilesets"
    assert config.character.path == "entities/player/sprites"

    assert config.converter.path.input == "./test-data"
    assert config.converter.path.output == "./output"

    assert config.character.idle.speed == 3.0
    assert config.character.idle.duration == 1.0
    assert config.character.idle.loop is True

    assert config.character.walk.speed == 6.0
    assert config.character.damaged.speed == 5.0
    assert config.character.damaged.loop is True

    assert config.logger.enabled is True
    assert config.logger.level == "DEBUG"
    assert config.logger.file == "run.log"
    assert config.logger.mode == "OVERWRITE"


def test_missing_file_returns_defaults(tmp_path: Path) -> None:
    config = load_app_config(tmp_path / "missing.yaml")

    assert config.tileset.path == ""
    assert config.character.path == ""
    assert config.logger.enabled is False
    assert config.logger.level == "DEBUG"

    # The converter paths fall back to the built-in defaults.
    assert config.converter.path.input == DEFAULT_INPUT_DIRECTORY
    assert config.converter.path.output == DEFAULT_OUTPUT_DIRECTORY

    # Defaults mirror the character layout defaults.
    assert config.character.walk.loop is True
    assert config.character.damaged.loop is False
    assert config.character.damaged.speed == 8.0


def test_missing_converter_section_keeps_defaults(tmp_path: Path) -> None:
    config = load_app_config(write_config(tmp_path, {}))

    assert config.converter.path.input == DEFAULT_INPUT_DIRECTORY
    assert config.converter.path.output == DEFAULT_OUTPUT_DIRECTORY


def test_non_mapping_converter_section_keeps_defaults(tmp_path: Path) -> None:
    config = load_app_config(write_config(tmp_path, {"converter": 42}))

    assert config.converter.path.input == DEFAULT_INPUT_DIRECTORY
    assert config.converter.path.output == DEFAULT_OUTPUT_DIRECTORY


def test_missing_converter_paths_reports_absent_entries(tmp_path: Path) -> None:
    # No file at all: both entries are reported missing.
    assert missing_converter_paths(tmp_path / "missing.yaml") == [
        "input",
        "output",
    ]

    # Only input is set: output alone is reported missing.
    config_path = write_config(
        tmp_path,
        {"converter": {"path": {"input": "./test-data"}}},
    )

    assert missing_converter_paths(config_path) == ["output"]

    # Both entries set: nothing is reported.
    config_path = write_config(
        tmp_path,
        {
            "converter": {
                "path": {
                    "input": "./test-data",
                    "output": "./output",
                },
            },
        },
    )

    assert missing_converter_paths(config_path) == []

    # A malformed converter section reports both entries.
    config_path = write_config(tmp_path, {"converter": 42})

    assert missing_converter_paths(config_path) == ["input", "output"]


def test_godot_paths_are_normalized(tmp_path: Path) -> None:
    config = load_app_config(
        write_config(
            tmp_path,
            {
                "tileset": {"path": "res://world/tilesets/"},
                "character": {"path": r"entities\player\sprites"},
            },
        ),
    )

    assert config.tileset.path == "world/tilesets"
    assert config.character.path == "entities/player/sprites"


@pytest.mark.parametrize(
    "raw,expected",
    [
        (1, True),
        (0, False),
        (True, True),
        (False, False),
        ("true", True),
        ("false", False),
        ("yes", True),
        ("no", False),
    ],
)
def test_loop_values_are_coerced(
    tmp_path: Path,
    raw: object,
    expected: bool,
) -> None:
    config = load_app_config(
        write_config(
            tmp_path,
            {"character": {"walk": {"loop": raw}}},
        ),
    )

    assert config.character.walk.loop is expected


def test_missing_animation_section_keeps_defaults(tmp_path: Path) -> None:
    config = load_app_config(
        write_config(
            tmp_path,
            {"character": {"path": "entities/player/sprites"}},
        ),
    )

    assert config.character.path == "entities/player/sprites"
    assert config.character.idle.speed == 2.0
    assert config.character.walk.speed == 6.0


def test_invalid_yaml_falls_back_to_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "rpgmaker2godot.yaml"
    config_path.write_text("{not yaml", encoding="utf-8")

    config = load_app_config(config_path)

    assert config.tileset.path == ""
    assert config.character.path == ""
    assert config.character.idle.speed == 2.0


def test_read_yaml_document_reports_parse_errors(tmp_path: Path) -> None:
    config_path = tmp_path / "rpgmaker2godot.yaml"
    config_path.write_text("{not yaml", encoding="utf-8")

    document, error = read_yaml_document(config_path)

    assert document == {}
    assert error is not None
    assert "while scanning" in error or "not yaml" in error


def test_read_yaml_document_rejects_a_non_mapping_root(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "rpgmaker2godot.yaml"
    config_path.write_text("- one\n- two\n", encoding="utf-8")

    document, error = read_yaml_document(config_path)

    assert document == {}
    assert error == "the document must be a YAML mapping of sections"


def test_read_yaml_document_accepts_an_empty_file(tmp_path: Path) -> None:
    config_path = tmp_path / "rpgmaker2godot.yaml"
    config_path.write_text("", encoding="utf-8")

    document, error = read_yaml_document(config_path)

    assert document == {}
    assert error is None


def test_read_yaml_document_tolerates_a_leading_bom(
    tmp_path: Path,
) -> None:
    """Editors such as Notepad write a BOM: it must be ignored."""

    config_path = tmp_path / "rpgmaker2godot.yaml"
    config_path.write_text(
        "converter:\n  path:\n    input: ./in\n",
        encoding="utf-8-sig",
    )

    document, error = read_yaml_document(config_path)

    assert error is None
    assert document["converter"]["path"]["input"] == "./in"


def test_read_yaml_document_missing_file_is_not_an_error(
    tmp_path: Path,
) -> None:
    document, error = read_yaml_document(tmp_path / "missing.yaml")

    assert document == {}
    assert error is None


def test_windows_backslash_paths_in_double_quotes_are_reported(
    tmp_path: Path,
) -> None:
    """A common Windows mistake: \\ escapes are invalid in YAML."""

    config_path = tmp_path / "rpgmaker2godot.yaml"
    config_path.write_text(
        'converter:\n  path:\n    input: "C:\\RPG Maker\\img"\n',
        encoding="utf-8",
    )

    _, error = read_yaml_document(config_path)

    assert error is not None
    assert "unknown escape character" in error


def test_load_document_returns_mapping(tmp_path: Path) -> None:
    document = load_document(write_config(tmp_path, SAMPLE))

    assert isinstance(document, dict)
    assert document["tileset"]["path"] == "world/tilesets"


def test_load_section_returns_one_section(tmp_path: Path) -> None:
    section = load_section(write_config(tmp_path, SAMPLE), "character")

    assert section["path"] == "entities/player/sprites"

    assert load_section(write_config(tmp_path, SAMPLE), "ghost") == {}


def test_resolve_config_path_none_uses_the_working_directory() -> None:
    assert (
        resolve_config_path(None)
        == Path.cwd() / DEFAULT_CONFIG_FILENAME
    )


def test_resolve_config_path_appends_the_yaml_extension() -> None:
    resolved = resolve_config_path("custom")

    assert resolved == Path("custom.yaml")


def test_resolve_config_path_keeps_the_yaml_extension() -> None:
    assert resolve_config_path("custom.yaml") == Path("custom.yaml")

    # The check is case-insensitive: an explicit extension is kept
    # exactly as given.
    assert resolve_config_path("custom.YAML") == Path("custom.YAML")


def test_resolve_config_path_keeps_subdirectories() -> None:
    resolved = resolve_config_path("configs/prod")

    assert resolved == Path("configs") / "prod.yaml"


def test_load_app_config_accepts_a_name_without_extension() -> None:
    # The conftest runs every test in a fresh working directory:
    # dropping the custom file there mirrors a real run.
    (Path.cwd() / "custom.yaml").write_text(
        yaml.safe_dump({"tileset": {"path": "world/tilesets"}}),
        encoding="utf-8",
    )

    config = load_app_config("custom")

    assert config.tileset.path == "world/tilesets"