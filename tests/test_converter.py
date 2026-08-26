from pathlib import Path

from rpgmaker2godot.analysis.models import (
    AnalysisResult,
    RPGMakerVersion,
    SheetInfo,
)
from rpgmaker2godot.conversion import SimpleConverter
from rpgmaker2godot.model import SheetType


def make_sheet(
    prefix: str,
    sheet_type: SheetType,
    width: int,
    height: int,
) -> SheetInfo:
    return SheetInfo(
        sheet_type=sheet_type,
        path=Path(f"{prefix}_{sheet_type.value}.png"),
        prefix=prefix,
        width=width,
        height=height,
        tile_width=48,
        tile_height=48,
        columns=width // 48,
        rows=height // 48,
    )


def make_analysis(*sheets: SheetInfo) -> AnalysisResult:
    return AnalysisResult(
        input_directory=Path("tilesets"),
        version=RPGMakerVersion.UNKNOWN,
        tile_width=48,
        tile_height=48,
        sheets=tuple(sheets),
        warnings=(),
    )


def test_converts_single_sheet() -> None:
    analysis = make_analysis(
        make_sheet(
            "Inside",
            SheetType.B,
            768,
            768,
        )
    )

    result = SimpleConverter().convert(analysis)

    assert len(result.tilesets) == 1

    tileset = result.tilesets[0]

    assert tileset.name == "Inside"
    assert len(tileset.sheets) == 1

    sheet = tileset.sheets[0]

    assert sheet.sheet_type == SheetType.B
    assert sheet.columns == 16
    assert sheet.rows == 16
    assert len(sheet.tiles) == 256


def test_creates_correct_tile_coordinates() -> None:
    analysis = make_analysis(
        make_sheet(
            "Inside",
            SheetType.B,
            768,
            768,
        )
    )

    result = SimpleConverter().convert(analysis)

    sheet = result.tilesets[0].sheets[0]

    tile_0 = sheet.tiles[0]
    tile_1 = sheet.tiles[1]
    tile_15 = sheet.tiles[15]
    tile_16 = sheet.tiles[16]
    tile_17 = sheet.tiles[17]

    assert tile_0.ref.tileset == "Inside"
    assert tile_0.ref.sheet_type == SheetType.B
    assert tile_0.ref.index == 0
    assert tile_0.column == 0
    assert tile_0.row == 0
    assert tile_0.x == 0
    assert tile_0.y == 0

    assert tile_1.ref.tileset == "Inside"
    assert tile_1.ref.sheet_type == SheetType.B
    assert tile_1.ref.index == 1
    assert tile_1.column == 1
    assert tile_1.row == 0
    assert tile_1.x == 48
    assert tile_1.y == 0

    assert tile_15.ref.tileset == "Inside"
    assert tile_15.ref.sheet_type == SheetType.B
    assert tile_15.ref.index == 15
    assert tile_15.column == 15
    assert tile_15.row == 0
    assert tile_15.x == 720
    assert tile_15.y == 0

    assert tile_16.ref.tileset == "Inside"
    assert tile_16.ref.sheet_type == SheetType.B
    assert tile_16.ref.index == 16
    assert tile_16.column == 0
    assert tile_16.row == 1
    assert tile_16.x == 0
    assert tile_16.y == 48

    assert tile_17.ref.tileset == "Inside"
    assert tile_17.ref.sheet_type == SheetType.B
    assert tile_17.ref.index == 17
    assert tile_17.column == 1
    assert tile_17.row == 1
    assert tile_17.x == 48
    assert tile_17.y == 48


def test_converts_a5_dimensions() -> None:
    analysis = make_analysis(
        make_sheet(
            "Inside",
            SheetType.A5,
            384,
            768,
        )
    )

    result = SimpleConverter().convert(analysis)

    sheet = result.tilesets[0].sheets[0]

    assert sheet.sheet_type == SheetType.A5
    assert sheet.columns == 8
    assert sheet.rows == 16
    assert len(sheet.tiles) == 128


def test_groups_sheets_into_tilesets() -> None:
    analysis = make_analysis(
        make_sheet("Inside", SheetType.C, 768, 768),
        make_sheet("Inside", SheetType.A5, 384, 768),
        make_sheet("Inside", SheetType.B, 768, 768),
    )

    result = SimpleConverter().convert(analysis)

    assert len(result.tilesets) == 1

    tileset = result.tilesets[0]

    assert tileset.name == "Inside"
    assert len(tileset.sheets) == 3

    assert [
        sheet.sheet_type
        for sheet in tileset.sheets
    ] == [
        SheetType.A5,
        SheetType.B,
        SheetType.C,
    ]


def test_groups_multiple_tilesets() -> None:
    analysis = make_analysis(
        make_sheet("Inside", SheetType.A5, 384, 768),
        make_sheet("Inside", SheetType.B, 768, 768),
        make_sheet("Inside", SheetType.C, 768, 768),
        make_sheet("Outside", SheetType.A5, 384, 768),
        make_sheet("Outside", SheetType.B, 768, 768),
        make_sheet("Outside", SheetType.C, 768, 768),
    )

    result = SimpleConverter().convert(analysis)

    assert len(result.tilesets) == 2

    assert [tileset.name for tileset in result.tilesets] == [
        "Inside",
        "Outside",
    ]

    inside = result.tilesets[0]
    outside = result.tilesets[1]

    assert len(inside.sheets) == 3
    assert len(outside.sheets) == 3

    assert all(
        len(sheet.tiles) == 128
        if sheet.sheet_type == SheetType.A5
        else len(sheet.tiles) == 256
        for sheet in inside.sheets
    )


def test_converts_sheet_without_prefix() -> None:
    analysis = make_analysis(
        make_sheet("", SheetType.B, 768, 768)
    )

    result = SimpleConverter().convert(analysis)

    assert len(result.tilesets) == 1
    assert result.tilesets[0].name == ""


def test_no_merge_keeps_each_sheet_as_its_own_tileset() -> None:
    analysis = make_analysis(
        make_sheet("Inside", SheetType.A5, 384, 768),
        make_sheet("Inside", SheetType.B, 768, 768),
        make_sheet("Inside", SheetType.C, 768, 768),
    )

    result = SimpleConverter(no_merge=True).convert(analysis)

    # The three sheets share a prefix but stay separate.
    assert len(result.tilesets) == 3

    assert [tileset.name for tileset in result.tilesets] == [
        "Inside_A5",
        "Inside_B",
        "Inside_C",
    ]

    for tileset in result.tilesets:
        assert len(tileset.sheets) == 1


def test_no_merge_single_sheet_matches_default() -> None:
    analysis = make_analysis(
        make_sheet("Inside", SheetType.B, 768, 768),
    )

    merged = SimpleConverter().convert(analysis)
    split = SimpleConverter(no_merge=True).convert(analysis)

    assert len(merged.tilesets) == 1
    assert len(split.tilesets) == 1

    # With a single sheet both modes produce one tileset; the only
    # difference is that the tileset is named after the source sheet
    # instead of the prefix.
    assert split.tilesets[0].name == "Inside_B"

    merged_sheet = merged.tilesets[0].sheets[0]
    split_sheet = split.tilesets[0].sheets[0]

    assert len(split_sheet.tiles) == len(merged_sheet.tiles)
    assert split_sheet.columns == merged_sheet.columns
    assert split_sheet.rows == merged_sheet.rows
    assert split_sheet.source_path == merged_sheet.source_path

    # Each entry has the same index and sheet type; only the owning
    # tileset name in the reference differs.
    assert [
        tile.ref.index for tile in split_sheet.tiles
    ] == [
        tile.ref.index for tile in merged_sheet.tiles
    ]


def test_preserves_source_path() -> None:
    source = Path("tilesets/Inside_B.png")

    sheet_info = SheetInfo(
        sheet_type=SheetType.B,
        path=source,
        prefix="Inside",
        width=768,
        height=768,
        tile_width=48,
        tile_height=48,
        columns=16,
        rows=16,
    )

    result = SimpleConverter().convert(
        make_analysis(sheet_info)
    )

    sheet = result.tilesets[0].sheets[0]

    assert sheet.source_path == source