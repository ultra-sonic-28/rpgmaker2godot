"""Typed access to the ``rpgmaker2godot.yaml`` configuration.

The configuration file stores independent sections:

* ``logger`` — opt-in file logging (read by
  :func:`rpgmaker2godot.utils.log.configure_logging`);
* ``tileset`` — the Godot output directory (relative to ``res://``)
  in which the tileset atlases referenced by the generated ``.tres``
  live;
* ``character`` — the Godot output directory (relative to
  ``res://``) for character spritesheets, plus the playback settings
  (speed, duration, loop) applied to the idle, walk and damaged
  animations.
"""

from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_CONFIG_FILENAME = "rpgmaker2godot.yaml"


@dataclass(frozen=True)
class AnimationConfig:
    """Playback settings of one character animation family."""

    speed: float = 6.0
    duration: float = 1.0
    loop: bool = True


@dataclass(frozen=True)
class CharacterConfig:
    """Character section: Godot output path and animation settings."""

    path: str = ""
    idle: AnimationConfig = AnimationConfig(speed=2.0)
    walk: AnimationConfig = AnimationConfig(speed=6.0)
    damaged: AnimationConfig = AnimationConfig(speed=8.0, loop=False)


@dataclass(frozen=True)
class TilesetConfig:
    """Tileset section: Godot output directory (relative to res://)."""

    path: str = ""


@dataclass(frozen=True)
class LoggerConfig:
    """Logger section, mirroring what ``configure_logging`` consumes."""

    enabled: bool = False
    level: str = "DEBUG"
    file: str = ""
    mode: str = "APPEND"


@dataclass(frozen=True)
class AppConfig:
    """The full typed configuration."""

    logger: LoggerConfig = LoggerConfig()
    tileset: TilesetConfig = TilesetConfig()
    character: CharacterConfig = CharacterConfig()


def load_document(config_path: Path | None = None) -> dict:
    """Read the whole YAML document, or {} when missing or invalid."""

    if config_path is None:
        config_path = Path.cwd() / DEFAULT_CONFIG_FILENAME

    if not config_path.is_file():
        return {}

    try:
        document = yaml.safe_load(
            config_path.read_text(encoding="utf-8"),
        )
    except (yaml.YAMLError, OSError):
        return {}

    if not isinstance(document, dict):
        return {}

    return document


def load_section(
    config_path: Path | None,
    section: str,
) -> dict:
    """Read one top-level section, or {} when missing or malformed."""

    document = load_document(config_path)
    value = document.get(section)

    if not isinstance(value, dict):
        return {}

    return value


def load_app_config(config_path: Path | None = None) -> AppConfig:
    """Load and validate the full configuration tree."""

    document = load_document(config_path)

    return AppConfig(
        logger=_build_logger(document.get("logger")),
        tileset=_build_tileset(document.get("tileset")),
        character=_build_character(document.get("character")),
    )


def _build_logger(raw: object) -> LoggerConfig:
    defaults = LoggerConfig()

    if not isinstance(raw, dict):
        return defaults

    return LoggerConfig(
        enabled=_as_bool(raw, "enabled", defaults.enabled),
        level=_as_str(raw, "level", defaults.level),
        file=_as_str(raw, "file", defaults.file),
        mode=_as_str(raw, "mode", defaults.mode),
    )


def _build_tileset(raw: object) -> TilesetConfig:
    if not isinstance(raw, dict):
        return TilesetConfig()

    return TilesetConfig(
        path=_as_godot_path(raw.get("path")),
    )


def _build_character(raw: object) -> CharacterConfig:
    if not isinstance(raw, dict):
        return CharacterConfig()

    defaults = CharacterConfig()

    return CharacterConfig(
        path=_as_godot_path(raw.get("path")),
        idle=_build_animation(raw.get("idle"), defaults.idle),
        walk=_build_animation(raw.get("walk"), defaults.walk),
        damaged=_build_animation(raw.get("damaged"), defaults.damaged),
    )


def _build_animation(
    raw: object,
    default: AnimationConfig,
) -> AnimationConfig:
    if not isinstance(raw, dict):
        return default

    return AnimationConfig(
        speed=_as_float(raw, "speed", default.speed),
        duration=_as_float(raw, "duration", default.duration),
        loop=_as_bool(raw, "loop", default.loop),
    )


def _as_str(section: dict, key: str, default: str) -> str:
    value = section.get(key, default)
    return value if isinstance(value, str) else default


def _as_float(section: dict, key: str, default: float) -> float:
    value = section.get(key, default)

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_bool(section: dict, key: str, default: bool) -> bool:
    value = section.get(key, default)

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value != 0

    if isinstance(value, float):
        return value != 0.0

    if isinstance(value, str):
        normalized = value.strip().lower()

        if normalized in ("1", "true", "yes", "on"):
            return True

        if normalized in ("0", "false", "no", "off"):
            return False

    return default


def _as_godot_path(raw: object) -> str:
    """Normalize a res://-relative directory into its plain form.

    Accepts "world/tilesets", "/world/tilesets" and even a full
    "res://world/tilesets" value (forward and backslashes alike);
    returns "" for anything else.
    """

    if not isinstance(raw, str):
        return ""

    path = raw.strip().replace("\\", "/").strip("/")

    lowered = path.lower()

    if lowered.startswith("res://"):
        path = path[len("res://"):].lstrip("/")
    elif lowered.startswith("res:/"):
        path = path[len("res:/"):].lstrip("/")

    return path


__all__ = [
    "DEFAULT_CONFIG_FILENAME",
    "AnimationConfig",
    "AppConfig",
    "CharacterConfig",
    "LoggerConfig",
    "TilesetConfig",
    "load_app_config",
    "load_document",
    "load_section",
]