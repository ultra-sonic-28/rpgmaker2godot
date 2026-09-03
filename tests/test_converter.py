import math
from dataclasses import replace
from pathlib import Path

import pytest
from PIL import Image

from rpgmaker2godot.analysis.models import (
    AnalysisResult,
    RPGMakerVersion,
    SheetInfo,
)
from rpgmaker2godot.conversion import SimpleConverter
from rpgmaker2godot.model import SheetType
from rpgmaker2godot.model.tile import Tile
from rpgmaker2godot.model.tile_collision import TileCollision
from rpgmaker2godot.tileset.model import TileProperties
from rpgmaker2godot.tileset.tile_id import tile_to_tile_id


def make_sheet(
    prefix: str,
    sheet_type: SheetType,
    width: int,
    height: int,
    path: Path | None = None,
) -> SheetInfo:
    return SheetInfo(
        sheet_type=sheet_type,
        path=(
            path
            if path is not None
            else Path(f"{prefix}_{sheet_type.value}.png")
        ),
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


def write_a4_sheet(
    path: Path,
    *,
    uniform_band: tuple[int, int] | None = None,
) -> None:
    """Write a canonical 768x720 A4 sheet with injective quarters.

    Every 24x24 quarter receives a colour derived from its (qx, qy)
    position; the mapping is injective over the whole sheet, so no two
    compositions can render identically and the pixel-level
    deduplication behaves exactly like the composition-level one
    (1536 tiles). ``uniform_band`` optionally paints the pixel rows
    ``[start, end)`` with one flat colour: every autotile whose source
    lies inside that band then composes identical tiles, which the
    converter must merge.
    """

    path.parent.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGBA", (768, 720))

    for y in range(0, 720, 24):
        for x in range(0, 768, 24):
            qx, qy = x // 24, y // 24

            if (
                uniform_band is not None
                and uniform_band[0] <= y < uniform_band[1]
            ):
                color = (200, 200, 200, 255)
            else:
                color = (
                    (qx * 37) % 256,
                    (qy * 61) % 256,
                    (qx + qy * 3) % 256,
                    255,
                )

            image.paste(color, (x, y, x + 24, y + 24))

    image.save(path)
    image.close()


def write_a3_sheet(
    path: Path,
    *,
    uniform_band: tuple[int, int] | None = None,
) -> None:
    """Write a canonical 768x384 A3 sheet with injective quarters.

    Every 24x24 quarter receives a colour derived from its (qx, qy)
    position; the mapping is injective over the whole sheet, so no two
    compositions can render identically and the pixel-level
    deduplication behaves exactly like the composition-level one
    (512 tiles). ``uniform_band`` optionally paints the pixel rows
    ``[start, end)`` with one flat colour: every autotile whose source
    lies inside that band then composes identical tiles, which the
    converter must merge.
    """

    path.parent.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGBA", (768, 384))

    for y in range(0, 384, 24):
        for x in range(0, 768, 24):
            qx, qy = x // 24, y // 24

            if (
                uniform_band is not None
                and uniform_band[0] <= y < uniform_band[1]
            ):
                color = (200, 200, 200, 255)
            else:
                color = (
                    (qx * 37) % 256,
                    (qy * 61) % 256,
                    (qx + qy * 3) % 256,
                    255,
                )

            image.paste(color, (x, y, x + 24, y + 24))

    image.save(path)
    image.close()


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


def test_converts_a4_dimensions(tmp_path: Path) -> None:
    source_path = tmp_path / "Inside_A4.png"

    write_a4_sheet(source_path)

    analysis = make_analysis(
        make_sheet(
            "Inside",
            SheetType.A4,
            768,
            720,
            path=source_path,
        )
    )

    result = SimpleConverter().convert(analysis)

    sheet = result.tilesets[0].sheets[0]

    # The A4 sheet (768x720) unfolds its 48 autotiles into 2304 raw
    # shape variants, but the Wall Side table only holds 16 distinct
    # shapes: the duplicates are dropped, leaving 1536 unique tiles
    # (24 Wall Tops x 48 + 24 Wall Sides x 16).
    assert len(sheet.tiles) == 24 * 48 + 24 * 16

    # The conversion metadata describes the packed atlas region.
    assert sheet.columns == 16
    assert sheet.rows == 96
    assert sheet.width == 16 * 48
    assert sheet.height == 96 * 48

    # Every tile is a 48x48 ready-to-place autotile variant.
    assert all(tile.width == 48 and tile.height == 48 for tile in sheet.tiles)


def test_a4_deduplicates_wall_side_shape_ids(tmp_path: Path) -> None:
    """Wall Side shape IDs 16..47 repeat shapes 0..15 and are dropped.

    RPG Maker reserves 48 shape IDs per autotile kind but the Wall Side
    table cycles over 16 shapes: the duplicated variants compose the
    exact same tile. The converter keeps the first occurrence (with its
    engine ID) and packs the survivors sequentially on the 16-per-row
    grid.
    """

    source_path = tmp_path / "Inside_A4.png"

    write_a4_sheet(source_path)

    analysis = make_analysis(
        make_sheet("Inside", SheetType.A4, 768, 720, path=source_path)
    )

    sheet = SimpleConverter().convert(analysis).tilesets[0].sheets[0]

    indexes = [tile.ref.index for tile in sheet.tiles]

    # Kinds 0..7 are Wall Tops: their 48 shape IDs are all distinct.
    first_side_start = 8 * 48
    assert indexes[:first_side_start] == list(range(first_side_start))

    # Kind 8 is a Wall Side: only its first 16 shape IDs are distinct,
    # shape 16 composes the same tile as shape 0 and is dropped.
    assert indexes[first_side_start : first_side_start + 16] == list(
        range(first_side_start, first_side_start + 16)
    )
    assert first_side_start + 16 not in indexes

    # Total: 24 Wall Tops x 48 + 24 Wall Sides x 16 unique shapes.
    assert len(indexes) == 24 * 48 + 24 * 16

    # Survivors occupy sequential packed slots (16 per row).
    slots = {(tile.x // 48, tile.y // 48) for tile in sheet.tiles}
    assert slots == {(slot % 16, slot // 16) for slot in range(len(indexes))}

    # The engine autotile kind stays readable through column/row.
    last = sheet.tiles[-1]
    assert last.ref.index == 47 * 48 + 15
    assert (last.column, last.row) == (47 % 8, 47 // 8)


def test_a4_tile_ids_map_to_engine_ids(tmp_path: Path) -> None:
    """index = local_kind*48 + shape; ID = base(A4=5888) + index."""

    source_path = tmp_path / "Inside_A4.png"

    write_a4_sheet(source_path)

    analysis = make_analysis(
        make_sheet("Inside", SheetType.A4, 768, 720, path=source_path)
    )

    sheet = SimpleConverter().convert(analysis).tilesets[0].sheets[0]

    first = sheet.tiles[0]
    assert first.ref.index == 0
    assert tile_to_tile_id(first) == 5888 + 0

    # Autotile 1 = local_kind 0, shape 1.
    assert tile_to_tile_id(sheet.tiles[1]) == 5888 + 1

    # Shape 9 of kind 0, and the start of kind 1 (index 48).
    assert tile_to_tile_id(sheet.tiles[9]) == 5888 + 9
    assert sheet.tiles[48].ref.index == 48
    assert tile_to_tile_id(sheet.tiles[48]) == 5888 + 48


def test_a4_rejects_non_canonical_dimensions() -> None:
    analysis = make_analysis(
        make_sheet(
            "Inside",
            SheetType.A4,
            768,
            768,
        )
    )

    with pytest.raises(ValueError):
        SimpleConverter().convert(analysis)


def test_a4_deduplicates_graphically_identical_tiles(
    tmp_path: Path,
) -> None:
    """Tiles that render identically are packed only once.

    A fully uniform A4 sheet makes every quarter identical: all 2304
    raw shape variants compose the exact same 48x48 tile, so the whole
    sheet collapses to a single packed tile (the first engine ID).
    """

    source_path = tmp_path / "Inside_A4.png"

    write_a4_sheet(source_path, uniform_band=(0, 720))

    sheet = (
        SimpleConverter()
        .convert(
            make_analysis(
                make_sheet(
                    "Inside",
                    SheetType.A4,
                    768,
                    720,
                    path=source_path,
                )
            )
        )
        .tilesets[0]
        .sheets[0]
    )

    assert len(sheet.tiles) == 1

    only = sheet.tiles[0]

    assert only.ref.index == 0
    assert (only.x, only.y) == (0, 0)

    assert sheet.rows == 1
    assert sheet.height == 48


def test_a4_pixel_dedup_merges_across_autotile_kinds(
    tmp_path: Path,
) -> None:
    """Graphically identical tiles merge even across autotile kinds.

    Kinds 8-15 are the Wall Sides of the first band (source rows
    y=144..240). Painting that pixel band with one flat colour makes
    every composition of those eight kinds render identically, so they
    collapse to a single packed tile while all other autotiles keep
    their full set of distinct shapes:

        24 Wall Tops x 48 + 16 Wall Sides x 16 + 1 merged tile = 1409.
    """

    source_path = tmp_path / "Inside_A4.png"

    write_a4_sheet(source_path, uniform_band=(144, 240))

    sheet = (
        SimpleConverter()
        .convert(
            make_analysis(
                make_sheet(
                    "Inside",
                    SheetType.A4,
                    768,
                    720,
                    path=source_path,
                )
            )
        )
        .tilesets[0]
        .sheets[0]
    )

    indexes = [tile.ref.index for tile in sheet.tiles]

    assert len(indexes) == 24 * 48 + 16 * 16 + 1

    # The merged tile is the first Wall Side engine ID (kind 8, shape 0).
    assert 8 * 48 in indexes

    # No other Wall Side of the first band survives: every shape of
    # kinds 8..15 rendered identically to (kind 8, shape 0).
    assert 8 * 48 + 1 not in indexes
    assert 15 * 48 + 15 not in indexes

    # The Wall Sides of the other bands are untouched.
    assert 24 * 48 + 15 in indexes
    assert 40 * 48 + 15 in indexes

    # Survivors still occupy sequential packed slots (16 per row).
    slots = {(tile.x // 48, tile.y // 48) for tile in sheet.tiles}
    assert slots == {(slot % 16, slot // 16) for slot in range(len(indexes))}

    assert sheet.rows == math.ceil(len(indexes) / 16)


def test_a4_pixel_tolerance_merges_noisy_tiles(tmp_path: Path) -> None:
    """Tolerance dedup: tiles differing by a few stray pixels merge.

    A uniform sheet with one stray pixel yields exactly two
    exact-unique tiles (the second differs by a single pixel and is
    picked by kind 0 shape 47 only). The default converter keeps both;
    a tolerance of 1 merges them into the first occurrence.
    """

    source_path = tmp_path / "Inside_A4.png"

    write_a4_sheet(source_path, uniform_band=(0, 720))

    with Image.open(source_path) as image:
        sheet = image.convert("RGBA")

    sheet.putpixel((5, 5), (255, 0, 0, 255))
    sheet.save(source_path)
    sheet.close()

    analysis = make_analysis(
        make_sheet("Inside", SheetType.A4, 768, 720, path=source_path)
    )

    exact_sheet = (
        SimpleConverter().convert(analysis).tilesets[0].sheets[0]
    )

    assert [tile.ref.index for tile in exact_sheet.tiles] == [0, 47]

    tolerant_sheet = (
        SimpleConverter(autotile_pixel_tolerance=1)
        .convert(analysis)
        .tilesets[0]
        .sheets[0]
    )

    assert len(tolerant_sheet.tiles) == 1
    assert tolerant_sheet.tiles[0].ref.index == 0
    assert tolerant_sheet.rows == 1


def test_a4_pixel_tolerance_respects_collision(tmp_path: Path) -> None:
    """Tiles within tolerance stay separate when collisions differ."""

    source_path = tmp_path / "Inside_A4.png"

    write_a4_sheet(source_path, uniform_band=(0, 720))

    with Image.open(source_path) as image:
        sheet = image.convert("RGBA")

    sheet.putpixel((5, 5), (255, 0, 0, 255))
    sheet.save(source_path)
    sheet.close()

    class StubResolver:
        """Blocked everywhere except for the noisy shape 47."""

        def resolve(self, tile: Tile) -> TileProperties:
            blocked = TileProperties(
                can_pass_down=False,
                can_pass_left=False,
                can_pass_right=False,
                can_pass_up=False,
                is_star=False,
                is_ladder=False,
                is_bush=False,
                is_counter=False,
                is_damage_floor=False,
                terrain_tag=0,
            )

            if tile.ref.index == 47:
                return replace(blocked, can_pass_down=True)

            return blocked

    tolerant_sheet = (
        SimpleConverter(
            tile_properties_resolver=StubResolver(),
            autotile_pixel_tolerance=1,
        )
        .convert(
            make_analysis(
                make_sheet(
                    "Inside",
                    SheetType.A4,
                    768,
                    720,
                    path=source_path,
                )
            )
        )
        .tilesets[0]
        .sheets[0]
    )

    assert len(tolerant_sheet.tiles) == 2

    collisions = {
        tile.ref.index: tile.collision for tile in tolerant_sheet.tiles
    }

    assert collisions[0] == TileCollision(
        block_down=True,
        block_left=True,
        block_right=True,
        block_up=True,
    )

    assert collisions[47] == TileCollision(
        block_down=False,
        block_left=True,
        block_right=True,
        block_up=True,
    )


def test_groups_a4_into_a_separate_autotile_tileset(
    tmp_path: Path,
) -> None:
    """Merge mode splits a prefix into autotile and normal tilesets.

    The autotile sheets (A1-A4; only A4 is handled today) stack into
    their own ``<prefix>_Autotile`` output, exported before the normal
    sheets (A5, B-E) which keep the plain ``<prefix>`` name — autotiles
    render beneath the other layers.
    """

    a4_path = tmp_path / "Inside_A4.png"

    write_a4_sheet(a4_path)

    analysis = make_analysis(
        make_sheet("Inside", SheetType.A5, 384, 768),
        make_sheet("Inside", SheetType.A4, 768, 720, path=a4_path),
        make_sheet("Inside", SheetType.B, 768, 768),
    )

    result = SimpleConverter().convert(analysis)

    assert [tileset.name for tileset in result.tilesets] == [
        "Inside_Autotile",
        "Inside",
    ]

    autotile_tileset, normal_tileset = result.tilesets

    assert [
        sheet.sheet_type for sheet in autotile_tileset.sheets
    ] == [SheetType.A4]

    assert [
        sheet.sheet_type for sheet in normal_tileset.sheets
    ] == [
        SheetType.A5,
        SheetType.B,
    ]

    # Every tile still references the RPG tileset named after the
    # prefix, so collision lookup against Tilesets.json keeps working
    # even though the output tileset carries the _Autotile suffix.
    for tileset in result.tilesets:
        for sheet in tileset.sheets:
            for tile in sheet.tiles:
                assert tile.ref.tileset == "Inside"


def test_merge_names_the_autotile_tileset_after_the_prefix(
    tmp_path: Path,
) -> None:
    """A prefix whose only sheet is A4 exports Inside_Autotile alone."""

    a4_path = tmp_path / "Inside_A4.png"

    write_a4_sheet(a4_path)

    analysis = make_analysis(
        make_sheet("Inside", SheetType.A4, 768, 720, path=a4_path),
    )

    result = SimpleConverter().convert(analysis)

    assert len(result.tilesets) == 1

    tileset = result.tilesets[0]

    assert tileset.name == "Inside_Autotile"
    assert tileset.sheets[0].sheet_type == SheetType.A4


def test_merge_without_prefix_names_the_autotile_tileset_autotile(
    tmp_path: Path,
) -> None:
    """A prefix-less A4 sheet exports an ``Autotile`` tileset."""

    a4_path = tmp_path / "A4.png"

    write_a4_sheet(a4_path)

    analysis = make_analysis(
        make_sheet("", SheetType.A4, 768, 720, path=a4_path),
    )

    result = SimpleConverter().convert(analysis)

    assert [tileset.name for tileset in result.tilesets] == ["Autotile"]


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

    # With a single sheet both modes produce the same tiles; the only
    # difference is that the output tileset is named after the source
    # sheet instead of the prefix.
    assert split.tilesets[0].name == "Inside_B"
    assert split.tilesets[0].sheets == merged.tilesets[0].sheets


def test_no_merge_keeps_ref_tileset_equal_to_prefix() -> None:
    """--no-merge must not change the RPG tileset name used for lookup.

    TileRef.tileset stays the prefix so that collision resolution
    against Tilesets.json (which names tilesets by prefix) keeps
    working in no-merge mode.
    """
    analysis = make_analysis(
        make_sheet("Inside", SheetType.B, 768, 768),
        make_sheet("Inside", SheetType.C, 768, 768),
    )

    result = SimpleConverter(no_merge=True).convert(analysis)

    assert [tileset.name for tileset in result.tilesets] == [
        "Inside_B",
        "Inside_C",
    ]

    # Each tile still belongs to the RPG tileset named after the prefix,
    # exactly as it would in merge mode.
    for tileset in result.tilesets:
        for tile in tileset.sheets[0].tiles:
            assert tile.ref.tileset == "Inside"


def test_no_merge_keeps_a4_sheet_split(tmp_path: Path) -> None:
    """--no-merge never creates the merged ``_Autotile`` output."""

    a4_path = tmp_path / "Inside_A4.png"

    write_a4_sheet(a4_path)

    analysis = make_analysis(
        make_sheet("Inside", SheetType.A4, 768, 720, path=a4_path),
        make_sheet("Inside", SheetType.B, 768, 768),
    )

    result = SimpleConverter(no_merge=True).convert(analysis)

    assert [tileset.name for tileset in result.tilesets] == [
        "Inside_A4",
        "Inside_B",
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


def test_a3_unfolds_unique_tiles(tmp_path: Path) -> None:
    """An A3 sheet unfolds to its 512 compositions, packed 16 per row."""

    source_path = tmp_path / "Inside_A3.png"

    write_a3_sheet(source_path)

    sheet = (
        SimpleConverter()
        .convert(
            make_analysis(
                make_sheet("Inside", SheetType.A3, 768, 384, path=source_path),
            )
        )
        .tilesets[0]
        .sheets[0]
    )

    assert sheet.sheet_type == SheetType.A3
    assert len(sheet.tiles) == 512

    # 512 tiles pack on a 16-per-row grid: 32 rows of 48px.
    assert sheet.width == 768
    assert sheet.height == 32 * 48
    assert sheet.columns == 16
    assert sheet.rows == 32

    # First tile: kind 0, shape 0, packed at the region's origin.
    first = sheet.tiles[0]

    assert first.ref.index == 0
    assert (first.x, first.y) == (0, 0)
    assert (first.column, first.row) == (0, 0)

    # Kind 0 keeps its first 16 shapes only (48 IDs cycle 16 shapes):
    # kind 1 starts right after.
    assert sheet.tiles[15].ref.index == 15
    assert sheet.tiles[16].ref.index == 48
    assert (sheet.tiles[16].column, sheet.tiles[16].row) == (1, 0)


def test_a3_rejects_non_canonical_dimensions(tmp_path: Path) -> None:
    analysis = make_analysis(
        make_sheet(
            "Inside",
            SheetType.A3,
            768,
            576,
        )
    )

    with pytest.raises(ValueError):
        SimpleConverter().convert(analysis)


def test_a3_deduplicates_graphically_identical_tiles(
    tmp_path: Path,
) -> None:
    """Tiles that render identically are packed only once.

    A fully uniform A3 sheet makes every quarter identical: all 1536
    raw shape variants compose the exact same 48x48 tile, so the whole
    sheet collapses to a single packed tile (the first engine ID).
    """

    source_path = tmp_path / "Inside_A3.png"

    write_a3_sheet(source_path, uniform_band=(0, 384))

    sheet = (
        SimpleConverter()
        .convert(
            make_analysis(
                make_sheet(
                    "Inside",
                    SheetType.A3,
                    768,
                    384,
                    path=source_path,
                )
            )
        )
        .tilesets[0]
        .sheets[0]
    )

    assert len(sheet.tiles) == 1

    only = sheet.tiles[0]

    assert only.ref.index == 0
    assert (only.x, only.y) == (0, 0)

    assert sheet.rows == 1
    assert sheet.height == 48


def test_a3_pixel_dedup_merges_across_autotile_kinds(
    tmp_path: Path,
) -> None:
    """Graphically identical tiles merge even across autotile kinds.

    Kinds 0-7 are the Roof row of the first band (source rows
    y=0..96). Painting that pixel band with one flat colour makes
    every composition of those eight kinds render identically, so they
    collapse to a single packed tile while all other autotiles keep
    their full set of distinct shapes:

        1 merged tile + 24 kinds x 16 shapes = 385.
    """

    source_path = tmp_path / "Inside_A3.png"

    write_a3_sheet(source_path, uniform_band=(0, 96))

    sheet = (
        SimpleConverter()
        .convert(
            make_analysis(
                make_sheet(
                    "Inside",
                    SheetType.A3,
                    768,
                    384,
                    path=source_path,
                )
            )
        )
        .tilesets[0]
        .sheets[0]
    )

    indexes = [tile.ref.index for tile in sheet.tiles]

    assert len(indexes) == 1 + 24 * 16

    # The merged tile is the first Roof engine ID (kind 0, shape 0).
    assert 0 in indexes

    # No other kind of the first band survives: every shape of
    # kinds 0..7 rendered identically to (kind 0, shape 0).
    assert 48 not in indexes
    assert 7 * 48 + 15 not in indexes

    # The second band's kinds are untouched.
    assert 16 * 48 + 15 in indexes
    assert 31 * 48 + 15 in indexes

    # Survivors still occupy sequential packed slots (16 per row).
    slots = {(tile.x // 48, tile.y // 48) for tile in sheet.tiles}
    assert slots == {(slot % 16, slot // 16) for slot in range(len(indexes))}

    assert sheet.rows == math.ceil(len(indexes) / 16)


def test_a3_tile_ids_map_to_engine_ids(tmp_path: Path) -> None:
    """Unfolded A3 tiles map to ID = TILE_ID_A3 + kind*48 + shape."""

    source_path = tmp_path / "Inside_A3.png"

    write_a3_sheet(source_path)

    sheet = (
        SimpleConverter()
        .convert(
            make_analysis(
                make_sheet("Inside", SheetType.A3, 768, 384, path=source_path),
            )
        )
        .tilesets[0]
        .sheets[0]
    )

    first = sheet.tiles[0]

    assert first.ref.index == 0
    assert tile_to_tile_id(first) == 4352 + 0

    # Autotile 1 = local_kind 0, shape 1.
    assert tile_to_tile_id(sheet.tiles[1]) == 4352 + 1

    # Shape 9 of kind 0, the start of kind 1 (index 48) and the start
    # of kind 3 (index 144 — the 49th tile, since every kind keeps its
    # first 16 shapes only).
    assert tile_to_tile_id(sheet.tiles[9]) == 4352 + 9
    assert sheet.tiles[16].ref.index == 48
    assert tile_to_tile_id(sheet.tiles[16]) == 4352 + 48
    assert sheet.tiles[48].ref.index == 144
    assert tile_to_tile_id(sheet.tiles[48]) == 4352 + 144


def test_merge_groups_a3_and_a4_into_the_autotile_output(
    tmp_path: Path,
) -> None:
    """A3 and A4 sheets of one prefix stack into ``<prefix>_Autotile``."""

    a3_path = tmp_path / "Inside_A3.png"
    a4_path = tmp_path / "Inside_A4.png"

    write_a3_sheet(a3_path)
    write_a4_sheet(a4_path)

    analysis = make_analysis(
        make_sheet("Inside", SheetType.A3, 768, 384, path=a3_path),
        make_sheet("Inside", SheetType.A4, 768, 720, path=a4_path),
        make_sheet("Inside", SheetType.B, 768, 768),
    )

    result = SimpleConverter().convert(analysis)

    assert [tileset.name for tileset in result.tilesets] == [
        "Inside_Autotile",
        "Inside",
    ]

    autotile_tileset = result.tilesets[0]

    # Canonical stacking order: the A3 buildings under the A4 walls.
    assert [
        sheet.sheet_type for sheet in autotile_tileset.sheets
    ] == [SheetType.A3, SheetType.A4]

    assert len(autotile_tileset.sheets[0].tiles) == 512
    assert len(autotile_tileset.sheets[1].tiles) == 1536


def test_no_merge_keeps_a3_sheet_split(tmp_path: Path) -> None:
    """--no-merge never creates the merged ``_Autotile`` output."""

    a3_path = tmp_path / "Inside_A3.png"

    write_a3_sheet(a3_path)

    analysis = make_analysis(
        make_sheet("Inside", SheetType.A3, 768, 384, path=a3_path),
        make_sheet("Inside", SheetType.B, 768, 768),
    )

    result = SimpleConverter(no_merge=True).convert(analysis)

    assert [tileset.name for tileset in result.tilesets] == [
        "Inside_A3",
        "Inside_B",
    ]