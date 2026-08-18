from pathlib import Path
import pytest

from rpgmaker2godot.godot.resource_writer import (
    GodotResourceWriter,
)

from tests.helpers.godot_tileset import (
    make_godot_tileset, 
    make_godot_tileset_with_multiple_sources,
)


def test_writes_tileset_resource(tmp_path: Path) -> None:
    tileset = make_godot_tileset()

    output_path = tmp_path / "Inside.tres"

    GodotResourceWriter().write(
        tileset,
        output_path,
        Path("Inside.png"),
    )

    assert output_path.exists()


def test_writes_serialized_resource(
    tmp_path: Path,
) -> None:
    tileset = make_godot_tileset()

    output_path = tmp_path / "Inside.tres"

    GodotResourceWriter().write(
        tileset,
        output_path,
        Path("Inside.png"),
    )

    content = output_path.read_text(
        encoding="utf-8",
    )

    assert '[gd_resource type="TileSet"' in content
    assert 'path="res://Inside.png"' in content
    assert "TileSetAtlasSource" in content


def test_creates_output_directory(
    tmp_path: Path,
) -> None:
    tileset = make_godot_tileset()

    output_path = (
        tmp_path
        / "nested"
        / "output"
        / "Inside.tres"
    )

    GodotResourceWriter().write(
        tileset,
        output_path,
        Path("Inside.png"),
    )

    assert output_path.exists()


def test_writes_atlas_cells(
    tmp_path: Path,
) -> None:
    tileset = make_godot_tileset()

    output_path = tmp_path / "Inside.tres"

    GodotResourceWriter().write(
        tileset,
        output_path,
        Path("Inside.png"),
    )

    content = output_path.read_text(
        encoding="utf-8",
    )

    assert "0:0/0 = 0" in content
    assert "1:0/0 = 0" in content
    assert "0:1/0 = 0" in content
    assert "1:1/0 = 0" in content


def test_rejects_multiple_atlas_sources(
    tmp_path: Path,
) -> None:
    tileset = make_godot_tileset_with_multiple_sources()

    with pytest.raises(
        ValueError,
        match="exactly one atlas source",
    ):
        GodotResourceWriter().write(
            tileset,
            tmp_path / "Inside.tres",
            Path("Inside.png"),
        )