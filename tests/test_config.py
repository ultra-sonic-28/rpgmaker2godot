from pathlib import Path

import pytest
import yaml

from rpgmaker2godot.utils.config import (
    load_app_config,
    load_document,
    load_section,
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