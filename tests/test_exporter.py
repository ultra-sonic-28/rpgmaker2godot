from pathlib import Path

from PIL import Image

from rpgmaker2godot.analysis.detector import TilesetDetector
from rpgmaker2godot.atlas.builder import AtlasBuilder
from rpgmaker2godot.atlas.writer import AtlasWriter
from rpgmaker2godot.conversion.converter import SimpleConverter
from rpgmaker2godot.godot.export.simple import SimpleExporter
from rpgmaker2godot.model.enums import SheetType
from rpgmaker2godot.model.tileset import ConversionResult
from tests.helpers.atlas import (
    make_sheet,
    make_tileset_with_sheets,
)
from tests.test_cli import create_sheet


class FakeAtlasBuilder:
    def __init__(self) -> None:
        self.tilesets = []

    def build(self, tileset):
        self.tilesets.append(tileset)
        return f"atlas:{tileset.name}"


class FakeAtlasWriter:
    def __init__(self) -> None:
        self.calls = []

    def write(self, atlas, output_path):
        self.calls.append((atlas, output_path))


class FakeGodotAtlasMapper:
    def __init__(self) -> None:
        self.calls = []

    def map(self, atlas):
        self.calls.append(atlas)
        return f"godot-atlas:{atlas}"


class FakeGodotTileSetBuilder:
    def __init__(self) -> None:
        self.calls = []

    def build(self, mapping, texture_path):
        self.calls.append((mapping, texture_path))
        return f"godot-tileset:{mapping}"


class FakeGodotResourceWriter:
    def __init__(self) -> None:
        self.calls = []

    def write(self, tileset, output_path, texture_path):
        self.calls.append(
            (
                tileset,
                output_path,
                texture_path,
            )
        )


def create_source_image(
    path: Path,
    size: tuple[int, int],
    color: tuple[int, int, int, int],
) -> None:
    Image.new(
        "RGBA",
        size,
        color,
    ).save(path)


def test_exports_single_tileset(
    tmp_path: Path,
) -> None:
    create_source_image(
        tmp_path / "Inside_A5.png",
        (96, 96),
        (255, 0, 0, 255),
    )

    create_source_image(
        tmp_path / "Inside_B.png",
        (96, 96),
        (0, 255, 0, 255),
    )

    create_source_image(
        tmp_path / "Inside_C.png",
        (96, 96),
        (0, 0, 255, 255),
    )

    tileset = make_tileset_with_sheets(
        make_sheet(
            SheetType.A5,
            96,
            96,
            source_directory=tmp_path,
        ),
        make_sheet(
            SheetType.B,
            96,
            96,
            source_directory=tmp_path,
        ),
        make_sheet(
            SheetType.C,
            96,
            96,
            source_directory=tmp_path,
        ),
    )

    conversion = ConversionResult(
        tilesets=(tileset,),
    )

    output_directory = tmp_path / "output"

    SimpleExporter().export(
        conversion,
        output_directory,
    )

    output_path = output_directory / "Inside.png"

    assert output_path.exists()

    with Image.open(output_path) as image:
        assert image.size == (96, 288)


def test_exports_correct_sheet_content(
    tmp_path: Path,
) -> None:
    create_source_image(
        tmp_path / "Inside_A5.png",
        (96, 96),
        (255, 0, 0, 255),
    )

    create_source_image(
        tmp_path / "Inside_B.png",
        (96, 96),
        (0, 255, 0, 255),
    )

    create_source_image(
        tmp_path / "Inside_C.png",
        (96, 96),
        (0, 0, 255, 255),
    )

    tileset = make_tileset_with_sheets(
        make_sheet(
            SheetType.A5,
            96,
            96,
            source_directory=tmp_path,
        ),
        make_sheet(
            SheetType.B,
            96,
            96,
            source_directory=tmp_path,
        ),
        make_sheet(
            SheetType.C,
            96,
            96,
            source_directory=tmp_path,
        ),
    )

    conversion = ConversionResult(
        tilesets=(tileset,),
    )

    output_directory = tmp_path / "output"

    SimpleExporter().export(
        conversion,
        output_directory,
    )

    with Image.open(
        output_directory / "Inside.png"
    ) as image:
        assert image.getpixel((24, 24)) == (
            255,
            0,
            0,
            255,
        )

        assert image.getpixel((24, 120)) == (
            0,
            255,
            0,
            255,
        )

        assert image.getpixel((24, 216)) == (
            0,
            0,
            255,
            255,
        )


def test_exports_multiple_tilesets(
    tmp_path: Path,
) -> None:
    for name, color in (
        ("Inside", (255, 0, 0, 255)),
        ("Outside", (0, 255, 0, 255)),
    ):
        create_source_image(
            tmp_path / f"{name}_B.png",
            (96, 96),
            color,
        )

    inside = make_tileset_with_sheets(
        make_sheet(
            SheetType.B,
            source_directory=tmp_path,
            tileset="Inside",
        ),
        name="Inside",
    )

    outside = make_tileset_with_sheets(
        make_sheet(
            SheetType.B,
            source_directory=tmp_path,
            tileset="Outside",
        ),
        name="Outside",
    )

    conversion = ConversionResult(
        tilesets=(inside, outside),
    )

    output_directory = tmp_path / "output"

    SimpleExporter().export(
        conversion,
        output_directory,
    )

    assert (output_directory / "Inside.png").exists()
    assert (output_directory / "Outside.png").exists()


def test_creates_output_directory(
    tmp_path: Path,
) -> None:
    create_source_image(
        tmp_path / "Inside_B.png",
        (96, 96),
        (255, 0, 0, 255),
    )

    tileset = make_tileset_with_sheets(
        make_sheet(
            SheetType.B,
            source_directory=tmp_path,
        ),
    )

    conversion = ConversionResult(
        tilesets=(tileset,),
    )

    output_directory = (
        tmp_path
        / "generated"
        / "atlases"
    )

    assert not output_directory.exists()

    SimpleExporter().export(
        conversion,
        output_directory,
    )

    assert output_directory.is_dir()


def test_exports_each_tileset(
    tmp_path: Path,
) -> None:
    inside = make_tileset_with_sheets(
        make_sheet(
            SheetType.B,
            source_directory=tmp_path,
            tileset="Inside",
        ),
        name="Inside",
    )

    outside = make_tileset_with_sheets(
        make_sheet(
            SheetType.B,
            source_directory=tmp_path,
            tileset="Outside",
        ),
        name="Outside",
    )

    conversion = ConversionResult(
        tilesets=(inside, outside),
    )

    builder = FakeAtlasBuilder()
    writer = FakeAtlasWriter()
    godot_atlas_mapper = FakeGodotAtlasMapper()
    godot_tileset_builder = FakeGodotTileSetBuilder()
    godot_resource_writer = FakeGodotResourceWriter()

    exporter = SimpleExporter(
        atlas_builder=builder,
        atlas_writer=writer,
        godot_atlas_mapper=godot_atlas_mapper,
        godot_tileset_builder=godot_tileset_builder,
        godot_resource_writer=godot_resource_writer,
    )

    output_directory = tmp_path / "output"

    exporter.export(
        conversion,
        output_directory,
    )

    assert builder.tilesets == [
        inside,
        outside,
    ]

    assert writer.calls == [
        (
            "atlas:Inside",
            output_directory / "Inside.png",
        ),
        (
            "atlas:Outside",
            output_directory / "Outside.png",
        ),
    ]


def test_exports_godot_resource(
    tmp_path: Path,
) -> None:
    input_directory = tmp_path / "tilesets"
    output_directory = tmp_path / "output"

    create_sheet(
        input_directory,
        "Inside_A5.png",
    )

    create_sheet(
        input_directory,
        "Inside_B.png",
    )

    create_sheet(
        input_directory,
        "Inside_C.png",
    )

    analysis = TilesetDetector().analyze(
        input_directory,
    )

    conversion = SimpleConverter().convert(
        analysis,
    )

    generated = SimpleExporter().export(
        conversion,
        output_directory,
    )

    assert output_directory / "Inside.png" in generated
    assert output_directory / "Inside.tres" in generated

    assert (output_directory / "Inside.png").exists()
    assert (output_directory / "Inside.tres").exists()


def test_exports_godot_resource_referencing_atlas(
    tmp_path: Path,
) -> None:
    input_directory = tmp_path / "tilesets"
    output_directory = tmp_path / "output"

    create_sheet(
        input_directory,
        "Inside_A5.png",
    )

    create_sheet(
        input_directory,
        "Inside_B.png",
    )

    create_sheet(
        input_directory,
        "Inside_C.png",
    )

    analysis = TilesetDetector().analyze(
        input_directory,
    )

    conversion = SimpleConverter().convert(
        analysis,
    )

    SimpleExporter().export(
        conversion,
        output_directory,
    )

    resource_path = output_directory / "Inside.tres"

    content = resource_path.read_text(
        encoding="utf-8",
    )

    assert "TileSetAtlasSource" in content
    assert "res://Inside.png" in content
    assert "48" in content