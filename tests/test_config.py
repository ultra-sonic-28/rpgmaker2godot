from pathlib import Path

import pytest
import yaml

from rpgmaker2godot.utils.config import (
    DEFAULT_CONFIG_FILENAME,
    load_app_config,
    load_document,
    load_section,
    resolve_config_path,
)

SAMPLE = {
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

    # Defaults mirror the character layout defaults.
    assert config.character.walk.loop is True
    assert config.character.damaged.loop is False
    assert config.character.damaged.speed == 8.0


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