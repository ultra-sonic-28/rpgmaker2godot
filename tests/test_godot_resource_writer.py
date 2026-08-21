from pathlib import Path
import pytest

from rpgmaker2godot.godot.resource.resource_writer import (
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


def test_writes_texture_path_relative_to_resource(
    tmp_path: Path,
) -> None:
    tileset = make_godot_tileset()

    texture_path = tmp_path / "Inside.png"
    resource_path = tmp_path / "Inside.tres"

    writer = GodotResourceWriter()

    writer.write(
        tileset,
        resource_path,
        texture_path,
    )

    content = resource_path.read_text(
        encoding="utf-8",
    )

    assert 'path="res://Inside.png"' in content


def test_writes_nested_texture_path_relative_to_resource(
    tmp_path: Path,
) -> None:
    tileset = make_godot_tileset()

    texture_directory = tmp_path / "textures"
    texture_path = texture_directory / "Inside.png"
    resource_path = tmp_path / "Inside.tres"

    texture_directory.mkdir()

    writer = GodotResourceWriter()

    writer.write(
        tileset,
        resource_path,
        texture_path,
    )

    content = resource_path.read_text(
        encoding="utf-8",
    )

    assert 'path="res://textures/Inside.png"' in content


def test_converts_relative_texture_path_to_godot_path(
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

    assert 'path="res://Inside.png"' in content


def test_preserves_godot_texture_path(
    tmp_path: Path,
) -> None:
    tileset = make_godot_tileset()

    output_path = tmp_path / "Inside.tres"

    GodotResourceWriter().write(
        tileset,
        output_path,
        Path("res://tilesets/Inside.png"),
    )

    content = output_path.read_text(
        encoding="utf-8",
    )

    assert (
        'path="res://tilesets/Inside.png"'
        in content
    )


def test_converts_absolute_texture_path_relative_to_resource(
    tmp_path: Path,
) -> None:
    tileset = make_godot_tileset()

    output_directory = tmp_path / "output"

    output_path = (
        output_directory / "Inside.tres"
    )

    texture_path = (
        output_directory / "Inside.png"
    )

    GodotResourceWriter().write(
        tileset,
        output_path,
        texture_path,
    )

    content = output_path.read_text(
        encoding="utf-8",
    )

    assert 'path="res://Inside.png"' in content


def test_preserves_relative_subdirectory_for_absolute_texture_path(
    tmp_path: Path,
) -> None:
    tileset = make_godot_tileset()

    output_directory = tmp_path / "output"

    output_path = (
        output_directory / "tilesets" / "Inside.tres"
    )

    texture_path = (
        output_directory
        / "tilesets"
        / "images"
        / "Inside.png"
    )

    GodotResourceWriter().write(
        tileset,
        output_path,
        texture_path,
    )

    content = output_path.read_text(
        encoding="utf-8",
    )

    assert (
        'path="res://images/Inside.png"'
        in content
    )


def test_rejects_absolute_texture_path_outside_resource_directory(
    tmp_path: Path,
) -> None:
    tileset = make_godot_tileset()

    output_path = (
        tmp_path
        / "output"
        / "Inside.tres"
    )

    texture_path = (
        tmp_path
        / "other"
        / "Inside.png"
    )

    with pytest.raises(
        ValueError,
        match="Texture path must be located inside",
    ):
        GodotResourceWriter().write(
            tileset,
            output_path,
            texture_path,
        )