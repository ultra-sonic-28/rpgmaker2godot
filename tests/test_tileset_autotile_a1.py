from pathlib import Path

import pytest
from PIL import Image

from rpgmaker2godot.analysis.models import (
    AnalysisResult,
    RPGMakerVersion,
    SheetInfo,
)
from rpgmaker2godot.conversion import SimpleConverter
from rpgmaker2godot.godot.atlas.atlas_mapper import GodotAtlasMapper
from rpgmaker2godot.godot.terrain.terrain_builder import (
    TERRAIN_MATCH_CORNERS_AND_SIDES,
    TERRAIN_MATCH_SIDES,
    GodotTerrainBuilder,
)
from rpgmaker2godot.godot.tileset.tileset_builder import GodotTileSetBuilder
from rpgmaker2godot.model import SheetType
from rpgmaker2godot.tileset.autotile.a1 import (
    A1_UNIQUE_COMPOSITION_COUNT,
    a1_animation_durations,
    a1_animation_id,
    a1_composition_quarters,
    a1_is_waterfall,
    a1_kind_frames,
    a1_kind_region,
    a1_quarters_from_index,
    a1_shape_quarters,
    a1_source_region,
    a1_unique_compositions,
    a1_unique_tiles,
)
from rpgmaker2godot.tileset.autotile.composer import compose_quarters
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


def write_a1_sheet(path: Path) -> None:
    """Write a canonical 768x576 A1 sheet with injective quarters.

    Every 24x24 quarter receives a colour derived from its (qx, qy)
    position; the mapping is injective over the whole sheet, so no two
    compositions can render identically and the pixel-level
    deduplication behaves exactly like the composition-level one.
    """

    path.parent.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGBA", (768, 576))

    for y in range(0, 576, 24):
        for x in range(0, 768, 24):
            qx, qy = x // 24, y // 24

            color = (
                (qx * 37) % 256,
                (qy * 61) % 256,
                (qx + qy * 3) % 256,
                255,
            )

            image.paste(color, (x, y, x + 24, y + 24))

    image.save(path)
    image.close()


def write_uniform_a1_sheet(path: Path) -> None:
    """Write a canonical A1 sheet painted with one flat colour.

    Every composition of a kind renders identically, so the pixel
    deduplication must merge them per animation family: one water, one
    waterfall and one static composition survive.
    """

    path.parent.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGBA", (768, 576), (80, 160, 240, 255))

    image.save(path)
    image.close()


def convert_a1(
    path: Path,
    converter: SimpleConverter | None = None,
):
    sheet = (
        (converter or SimpleConverter())
        .convert(
            make_analysis(
                make_sheet("Inside", SheetType.A1, 768, 576, path=path),
            )
        )
        .tilesets[0]
        .sheets[0]
    )

    return sheet


def test_a1_source_region_places_water_frames_side_by_side() -> None:
    """Animated waters store three 96x144 frames side by side."""

    assert a1_source_region(0, 0) == (0, 0)
    assert a1_source_region(0, 1) == (96, 0)
    assert a1_source_region(0, 2) == (192, 0)

    assert a1_source_region(1, 0) == (0, 144)
    assert a1_source_region(1, 1) == (96, 144)
    assert a1_source_region(1, 2) == (192, 144)

    # Kind 4 = tx 4, ty 0: bx = 8, by = 0 (rmmz_core.js decode).
    assert a1_source_region(4, 0) == (384, 0)
    assert a1_source_region(4, 1) == (480, 0)
    assert a1_source_region(4, 2) == (576, 0)

    # Kind 12 = tx 4, ty 1: bx = 8, by = 6.
    assert a1_source_region(12, 0) == (384, 288)
    assert a1_source_region(14, 2) == (576, 432)


def test_a1_source_region_places_waterfall_frames_stacked() -> None:
    """Waterfalls store three 96x48 frames stacked vertically."""

    # Kind 5 = tx 5, ty 0: bx = 8 + 6, by = 0.
    assert a1_source_region(5, 0) == (672, 0)
    assert a1_source_region(5, 1) == (672, 48)
    assert a1_source_region(5, 2) == (672, 96)

    # Kind 9 = tx 1, ty 1: bx = 0 + 6, by = 6.
    assert a1_source_region(9, 0) == (288, 288)
    assert a1_source_region(9, 1) == (288, 336)
    assert a1_source_region(9, 2) == (288, 384)

    assert a1_source_region(15, 0) == (672, 432)
    assert a1_source_region(15, 2) == (672, 528)


def test_a1_static_kinds_hold_a_single_frame() -> None:
    """Kinds 2 and 3 are read without the animation index."""

    assert a1_kind_frames(2) == 1
    assert a1_kind_frames(3) == 1

    assert a1_source_region(2, 0) == (288, 0)
    assert a1_source_region(3, 0) == (288, 144)

    with pytest.raises(ValueError):
        a1_source_region(2, 1)


def test_a1_kind_classification() -> None:
    """Mirror Tilemap.isWaterfallTile and the frame counts."""

    assert not a1_is_waterfall(0)
    assert not a1_is_waterfall(1)
    assert not a1_is_waterfall(3)
    assert a1_is_waterfall(5)
    assert a1_is_waterfall(15)

    for kind in (0, 1, 4, 6, 8, 10, 12, 14):
        assert a1_kind_frames(kind) == 3

    for kind in (5, 7, 9, 11, 13, 15):
        assert a1_kind_frames(kind) == 3

    with pytest.raises(ValueError):
        a1_is_waterfall(16)


def test_a1_animation_durations_follow_the_engine_timing() -> None:
    """Waters cycle [0, 1, 2, 1], waterfalls [0, 1, 2] every 0.5 s."""

    assert a1_animation_durations(0) == (0.5, 1.0, 0.5)
    assert a1_animation_durations(4) == (0.5, 1.0, 0.5)
    assert a1_animation_durations(5) == (0.5, 0.5, 0.5)
    assert a1_animation_durations(2) is None
    assert a1_animation_durations(3) is None


def test_a1_animation_id_separates_the_three_families() -> None:
    assert a1_animation_id(0) == "water"
    assert a1_animation_id(2) == "static"
    assert a1_animation_id(5) == "waterfall"


def test_a1_kind_region_covers_every_frame() -> None:
    """The detection region spans all animation frames of a kind."""

    assert a1_kind_region(0) == (0, 0, 288, 144)
    assert a1_kind_region(1) == (0, 144, 288, 144)
    assert a1_kind_region(2) == (288, 0, 96, 144)
    assert a1_kind_region(3) == (288, 144, 96, 144)
    assert a1_kind_region(4) == (384, 0, 288, 144)
    assert a1_kind_region(5) == (672, 0, 96, 144)
    assert a1_kind_region(9) == (288, 288, 96, 144)
    assert a1_kind_region(15) == (672, 432, 96, 144)


def test_a1_shape_quarters_use_the_engine_tables() -> None:
    """Waters compose from the floor table, waterfalls from theirs."""

    # Kind 0, shape 47: the isolated piece of the floor table, read at
    # the frame-0 region (0, 0).
    assert a1_shape_quarters(0, 47, 0) == (
        (0, 0, 0, 0),
        (24, 0, 24, 0),
        (0, 24, 0, 24),
        (24, 24, 24, 24),
    )

    # Kind 0, shape 0, frame 1: the interior piece, read at the
    # frame-1 region (96, 0) with the engine's reversed quarters.
    assert a1_shape_quarters(0, 0, 1) == (
        (96 + 48, 96, 0, 0),
        (96 + 24, 96, 24, 0),
        (96 + 48, 72, 0, 24),
        (96 + 24, 72, 24, 24),
    )

    # Kind 5, shape 1: the left half of the waterfall block at
    # (672, 0); shape 5 cycles the 4-shape waterfall table.
    assert a1_shape_quarters(5, 1, 0) == (
        (672, 0, 0, 0),
        (696, 0, 24, 0),
        (672, 24, 0, 24),
        (696, 24, 24, 24),
    )

    assert a1_shape_quarters(5, 5, 0) == a1_shape_quarters(5, 1, 0)


def test_a1_composition_quarters_joins_all_frames() -> None:
    """The joint strip lays every frame out side by side."""

    water = a1_composition_quarters(0, 47)

    # Three frames: destinations span 3 * 48 px.
    assert max(piece[2] for piece in water) == 2 * 48 + 24
    assert len(water) == 12

    # Composing the strip yields a 144x48 image.
    image = Image.new("RGBA", (768, 576), (10, 20, 30, 255))
    strip = compose_quarters(image, water)
    assert strip.size == (144, 48)

    static = a1_composition_quarters(2, 47)

    # One frame: destinations span a single 48 px tile.
    assert max(piece[2] for piece in static) == 24
    assert len(static) == 4


def test_a1_unique_compositions_skips_cycled_waterfall_shapes() -> None:
    """Only the 4 distinct waterfall shapes yield compositions."""

    waterfall_compositions = [
        index
        for index, _ in a1_unique_compositions()
        if a1_is_waterfall((index // 3) // 48)
    ]

    # One composition per distinct waterfall shape per kind.
    assert len(waterfall_compositions) == 6 * 4

    for index in waterfall_compositions:
        composition = index // 3
        assert composition % 48 < 4


def test_a1_unique_composition_count() -> None:
    """10 water kinds x 48 shapes + 6 waterfalls x 4 shapes."""

    assert A1_UNIQUE_COMPOSITION_COUNT == 10 * 48 + 6 * 4
    assert A1_UNIQUE_COMPOSITION_COUNT == sum(
        1 for _ in a1_unique_compositions()
    )


def test_a1_quarters_from_index_round_trips() -> None:
    """Frame-0 indexes decode back to the per-frame quarters."""

    for kind in (0, 2, 5, 9):
        for shape in (0, 1, 46 if not a1_is_waterfall(kind) else 3):
            for frame in range(a1_kind_frames(kind)):
                index = (kind * 48 + shape) * 3 + frame

                assert (
                    a1_quarters_from_index(index)
                    == a1_shape_quarters(kind, shape, frame)
                )


def test_a1_unique_tiles_dedups_per_animation_family() -> None:
    """A uniform sheet keeps one composition per animation family."""

    image = Image.new("RGBA", (768, 576), (80, 160, 240, 255))

    kept = list(
        a1_unique_tiles(
            image,
            dedup_key=lambda index, signature: a1_animation_id(
                (index // 3) // 48
            ),
        )
    )

    # Water (kind 0), static (kind 2) and waterfall (kind 5) survive;
    # every other composition is graphically identical within its
    # family and merges into the first occurrence.
    assert [index for index, _ in kept] == [0, 288, 720]

    # The water and waterfall strips hold three frames, the static one
    # a single frame.
    assert [len(quarters) for _index, quarters in kept] == [12, 4, 12]


def test_a1_unfolds_into_one_tile_per_frame(tmp_path: Path) -> None:
    """A fully distinct A1 sheet unfolds into 1320 packed tiles."""

    source_path = tmp_path / "Inside_A1.png"

    write_a1_sheet(source_path)

    sheet = convert_a1(source_path)

    assert sheet.sheet_type == SheetType.A1
    assert sheet.columns == 16
    assert len(sheet.tiles) == 8 * 144 + 2 * 48 + 6 * 12

    # The row padding (animation groups never straddle two rows) can
    # only add empty slots, never remove tiles.
    assert sheet.rows * 16 >= len(sheet.tiles)
    assert sheet.height == sheet.rows * 48
    assert sheet.width == 768


def test_a1_unfolding_requires_the_canonical_dimensions(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "Inside_A1.png"

    image = Image.new("RGBA", (768, 384))
    image.save(source_path)
    image.close()

    with pytest.raises(ValueError, match="A1 sheets must be 768x576px"):
        SimpleConverter().convert(
            make_analysis(
                make_sheet("Inside", SheetType.A1, 768, 384, path=source_path),
            )
        )


def test_a1_packs_animation_frames_on_consecutive_cells(
    tmp_path: Path,
) -> None:
    """The frames of one composition sit on consecutive atlas cells."""

    source_path = tmp_path / "Inside_A1.png"

    write_a1_sheet(source_path)

    sheet = convert_a1(source_path)

    # Kind 0, shape 0: the first three tiles, on row 0.
    first_group = sheet.tiles[0:3]

    assert [tile.ref.index for tile in first_group] == [0, 1, 2]
    assert [tile.x for tile in first_group] == [0, 48, 96]
    assert [tile.y for tile in first_group] == [0, 0, 0]

    # Every animated group stays on one row and never straddles the
    # 16-column grid.
    groups: dict[int, list] = {}

    for tile in sheet.tiles:
        groups.setdefault(tile.ref.index // 3, []).append(tile)

    for group in groups.values():
        columns = {tile.x // 48 for tile in group}
        rows = {tile.y // 48 for tile in group}

        assert len(rows) == 1
        assert sorted(columns) == list(range(min(columns), min(columns) + len(group)))
        assert max(columns) < 16


def test_a1_tile_ids_map_to_engine_ids(tmp_path: Path) -> None:
    """Unfolded A1 tiles map to ID = TILE_ID_A1 + index // 3."""

    source_path = tmp_path / "Inside_A1.png"

    write_a1_sheet(source_path)

    sheet = convert_a1(source_path)

    first = sheet.tiles[0]

    assert first.ref.index == 0
    assert tile_to_tile_id(first) == 2048

    # Kind 5, shape 1, frame 2: composition (5 * 48 + 1) = 241.
    waterfall = next(
        tile
        for tile in sheet.tiles
        if tile.ref.index == (5 * 48 + 1) * 3 + 2
    )

    assert tile_to_tile_id(waterfall) == 2048 + 241


def test_a1_tiles_carry_their_quarters(tmp_path: Path) -> None:
    """Converter tiles store the engine composition of each frame."""

    source_path = tmp_path / "Inside_A1.png"

    write_a1_sheet(source_path)

    sheet = convert_a1(source_path)

    assert sheet.tiles[0].quarters == a1_shape_quarters(0, 0, 0)
    assert sheet.tiles[1].quarters == a1_shape_quarters(0, 0, 1)
    assert sheet.tiles[2].quarters == a1_shape_quarters(0, 0, 2)

    # The static kind 2 emits a single tile (its frame-0 composition).
    static = next(
        tile for tile in sheet.tiles if tile.ref.index == (2 * 48 + 0) * 3
    )

    assert static.quarters == a1_shape_quarters(2, 0, 0)


def test_a1_dedup_merges_identical_compositions_per_family(
    tmp_path: Path,
) -> None:
    """A uniform sheet collapses to one composition per family."""

    source_path = tmp_path / "Inside_A1.png"

    write_uniform_a1_sheet(source_path)

    sheet = convert_a1(source_path)

    # One water group (3 frames), one static (1 frame), one waterfall
    # group (3 frames) — 7 tiles in total, in engine ID order.
    assert [tile.ref.index for tile in sheet.tiles] == [
        0,
        1,
        2,
        (2 * 48) * 3,
        (5 * 48) * 3,
        (5 * 48) * 3 + 1,
        (5 * 48) * 3 + 2,
    ]


def build_godot_tileset(converted):
    """Run the full atlas → Godot tileset → terrain pipeline."""

    from rpgmaker2godot.atlas import AtlasBuilder

    atlas = AtlasBuilder().build(converted)

    mapping = GodotAtlasMapper().map(atlas)

    godot_tileset = GodotTileSetBuilder().build(
        mapping,
        Path("Inside_Autotile.png"),
    )

    resolution = GodotTerrainBuilder().resolve(converted)

    terrain_plan = GodotTerrainBuilder().assign(
        godot_tileset,
        resolution,
    )

    return godot_tileset, terrain_plan


def test_a1_terrain_sets_pair_waters_and_waterfalls(tmp_path: Path) -> None:
    """Waters use blob matching, waterfalls side matching, one material."""

    source_path = tmp_path / "Inside_A1.png"

    write_a1_sheet(source_path)

    converted = (
        SimpleConverter()
        .convert(
            make_analysis(
                make_sheet("Inside", SheetType.A1, 768, 576, path=source_path),
            )
        )
        .tilesets[0]
    )

    resolution = GodotTerrainBuilder().resolve(converted)

    names = [
        terrain.name
        for terrain_set in resolution.terrain_sets
        for terrain in terrain_set.terrains
    ]
    modes = [
        terrain_set.mode for terrain_set in resolution.terrain_sets
    ]

    # Water 1-4 (kinds 0-3), then Water 5 + Waterfall 5 ... Water 10 +
    # Waterfall 10 (kinds 4..15) = 4 + 12 = 16 terrain sets.
    assert names == [
        "Water 1",
        "Water 2",
        "Water 3",
        "Water 4",
        "Water 5",
        "Waterfall 5",
        "Water 6",
        "Waterfall 6",
        "Water 7",
        "Waterfall 7",
        "Water 8",
        "Waterfall 8",
        "Water 9",
        "Waterfall 9",
        "Water 10",
        "Waterfall 10",
    ]

    assert modes == [
        TERRAIN_MATCH_CORNERS_AND_SIDES,
        TERRAIN_MATCH_CORNERS_AND_SIDES,
        TERRAIN_MATCH_CORNERS_AND_SIDES,
        TERRAIN_MATCH_CORNERS_AND_SIDES,
        TERRAIN_MATCH_CORNERS_AND_SIDES,
        TERRAIN_MATCH_SIDES,
        TERRAIN_MATCH_CORNERS_AND_SIDES,
        TERRAIN_MATCH_SIDES,
        TERRAIN_MATCH_CORNERS_AND_SIDES,
        TERRAIN_MATCH_SIDES,
        TERRAIN_MATCH_CORNERS_AND_SIDES,
        TERRAIN_MATCH_SIDES,
        TERRAIN_MATCH_CORNERS_AND_SIDES,
        TERRAIN_MATCH_SIDES,
        TERRAIN_MATCH_CORNERS_AND_SIDES,
        TERRAIN_MATCH_SIDES,
    ]

    # A waterfall shares the material number and colour of the water
    # on its left (kind 4 + kind 5 = material 5).
    assert (
        resolution.terrain_sets[4].terrains[0].color
        == resolution.terrain_sets[5].terrains[0].color
    )


def test_a1_waterfall_peering_connects_left_and_right(
    tmp_path: Path,
) -> None:
    """Waterfall shapes match sides only; waters match the blob."""

    source_path = tmp_path / "Inside_A1.png"

    write_a1_sheet(source_path)

    converted = (
        SimpleConverter()
        .convert(
            make_analysis(
                make_sheet("Inside", SheetType.A1, 768, 576, path=source_path),
            )
        )
        .tilesets[0]
    )

    _godot_tileset, terrain_plan = build_godot_tileset(converted)

    def peering_for(index: int) -> tuple[str, ...]:
        terrain = terrain_plan.tile_terrains[
            next(
                tile.ref
                for tile in converted.sheets[0].tiles
                if tile.ref.index == index
            )
        ]

        return tuple(name for name, _bit in terrain.peering_bits)

    # Waterfall shape 0: both sides connected (left + right, never
    # top or bottom).
    assert sorted(peering_for((5 * 48 + 0) * 3)) == [
        "left_side",
        "right_side",
    ]

    # Waterfall shape 1: left edge exposed.
    assert sorted(peering_for((5 * 48 + 1) * 3)) == ["right_side"]

    # Waterfall shape 2: right edge exposed.
    assert sorted(peering_for((5 * 48 + 2) * 3)) == ["left_side"]

    # Waterfall shape 3: isolated.
    assert peering_for((5 * 48 + 3) * 3) == ()

    # Water shape 0: the full blob (all sides and corners).
    assert sorted(peering_for(0)) == [
        "bottom_left_corner",
        "bottom_right_corner",
        "bottom_side",
        "left_side",
        "right_side",
        "top_left_corner",
        "top_right_corner",
        "top_side",
    ]


def test_a1_animated_tiles_are_defined_in_the_godot_tileset(
    tmp_path: Path,
) -> None:
    """Base tiles carry the animation; frame cells are not created."""

    source_path = tmp_path / "Inside_A1.png"

    write_a1_sheet(source_path)

    converted = (
        SimpleConverter()
        .convert(
            make_analysis(
                make_sheet("Inside", SheetType.A1, 768, 576, path=source_path),
            )
        )
        .tilesets[0]
    )

    godot_tileset, _terrain_plan = build_godot_tileset(converted)

    source = godot_tileset.atlas_sources[0]

    by_ref = {tile.ref.index: tile for tile in source.tiles}

    # The base tile of kind 0, shape 0 carries the water animation.
    base = by_ref[0]

    assert base.animation is not None
    assert base.animation.frames_count == 3
    assert base.animation.durations == (0.5, 1.0, 0.5)
    assert base.cell.column == 0
    assert base.cell.row == 0

    # The animation frames are NOT created as tiles: cells (1, 0) and
    # (2, 0) belong to the base tile's animation.
    assert all(tile.cell != (1, 0) for tile in source.tiles)
    assert all(tile.cell != (2, 0) for tile in source.tiles)

    # The static kind 2, shape 0 has no animation.
    static = by_ref[(2 * 48) * 3]

    assert static.animation is None

    # The waterfall kind 5, shape 0 animates at 0.5 s per frame.
    waterfall = by_ref[(5 * 48) * 3]

    assert waterfall.animation is not None
    assert waterfall.animation.durations == (0.5, 0.5, 0.5)


def test_a1_animation_properties_are_written_to_the_tres(
    tmp_path: Path,
) -> None:
    """The .tres carries the animation_frames_count and durations."""

    from rpgmaker2godot.godot.resource.resource_writer import (
        GodotResourceWriter,
    )

    source_path = tmp_path / "Inside_A1.png"

    write_a1_sheet(source_path)

    converted = (
        SimpleConverter()
        .convert(
            make_analysis(
                make_sheet("Inside", SheetType.A1, 768, 576, path=source_path),
            )
        )
        .tilesets[0]
    )

    godot_tileset, terrain_plan = build_godot_tileset(converted)

    resource_path = tmp_path / "Inside_Autotile.tres"

    GodotResourceWriter().write(
        godot_tileset,
        resource_path,
        Path("Inside_Autotile.png"),
        terrain_plan=terrain_plan,
    )

    content = resource_path.read_text(encoding="utf-8")

    lines = content.splitlines()

    # The water animation (durations in seconds; the duplicated surface
    # index of the [0, 1, 2, 1] cycle becomes a doubled duration).
    assert "0:0/animation_frames_count = 3" in lines
    assert "0:0/animation_frame_0/duration = 0.5" in lines
    assert "0:0/animation_frame_1/duration = 1" in lines
    assert "0:0/animation_frame_2/duration = 0.5" in lines

    # The animation frames' cells are not created as tiles.
    assert "1:0/0 = 0" not in lines
    assert "2:0/0 = 0" not in lines
    assert "0:0/0 = 0" in lines


def test_a1_atlas_placements_carry_their_quarters(tmp_path: Path) -> None:
    """The atlas placements compose A1 tiles from their quarter pieces.

    Regression guard: A1 tiles must take the unfolded-autotile path of
    the AtlasBuilder (quarter pieces), never the plain rectangular crop
    used by the normal sheets — a crop at the tile's packed position
    would show misplaced source material instead of the composition.
    """

    from rpgmaker2godot.atlas import AtlasBuilder

    source_path = tmp_path / "Inside_A1.png"

    write_a1_sheet(source_path)

    converted = (
        SimpleConverter()
        .convert(
            make_analysis(
                make_sheet("Inside", SheetType.A1, 768, 576, path=source_path),
            )
        )
        .tilesets[0]
    )

    atlas = AtlasBuilder().build(converted)

    placements = {
        placement.tile.index: placement for placement in atlas.placements
    }

    # The base tile of kind 0, shape 0 composes from its four quarters.
    base = placements[0]

    assert base.quarters
    assert tuple(
        (q.source_x, q.source_y, q.dest_x, q.dest_y) for q in base.quarters
    ) == a1_shape_quarters(0, 0, 0)

    # Its first animation frame sits on the next atlas slot.
    frame_1 = placements[1]

    assert frame_1.quarters
    assert tuple(
        (q.source_x, q.source_y, q.dest_x, q.dest_y) for q in frame_1.quarters
    ) == a1_shape_quarters(0, 0, 1)
    assert frame_1.atlas_x == base.atlas_x + 48
    assert frame_1.atlas_y == base.atlas_y

    # A waterfall composition composes from the waterfall table.
    waterfall = placements[(5 * 48) * 3]

    assert waterfall.quarters
    assert tuple(
        (q.source_x, q.source_y, q.dest_x, q.dest_y) for q in waterfall.quarters
    ) == a1_shape_quarters(5, 0, 0)


def test_a1_atlas_renders_the_composed_tiles(tmp_path: Path) -> None:
    """The written atlas holds the composed pixels of every A1 tile.

    Pixel-level regression guard for the same bug: the rendered 48x48
    region of a tile must equal the composition of its quarters — not a
    rectangular crop of the source sheet taken at the tile's packed
    atlas position.
    """

    from rpgmaker2godot.atlas import AtlasBuilder, AtlasWriter

    source_path = tmp_path / "Inside_A1.png"

    write_a1_sheet(source_path)

    converted = (
        SimpleConverter()
        .convert(
            make_analysis(
                make_sheet("Inside", SheetType.A1, 768, 576, path=source_path),
            )
        )
        .tilesets[0]
    )

    atlas = AtlasBuilder().build(converted)

    atlas_path = tmp_path / "Inside_A1_atlas.png"

    AtlasWriter().write(atlas, atlas_path)

    source = Image.open(source_path).convert("RGBA")
    rendered = Image.open(atlas_path).convert("RGBA")

    try:
        for index, (kind, shape, frame) in enumerate(
            (
                (0, 0, 0),   # water, shape 0, frame 0
                (0, 0, 1),   # water, shape 0, frame 1
                (0, 1, 0),   # water edge, frame 0
                (5, 0, 0),   # waterfall, shape 0, frame 0
                (5, 2, 1),   # waterfall, shape 2, frame 1
            )
        ):
            expected = compose_quarters(
                source,
                a1_shape_quarters(kind, shape, frame),
            )

            placement = next(
                placement
                for placement in atlas.placements
                if placement.tile.index
                == (kind * 48 + shape) * 3 + frame
            )

            actual = rendered.crop(
                (
                    placement.atlas_x,
                    placement.atlas_y,
                    placement.atlas_x + 48,
                    placement.atlas_y + 48,
                )
            )

            assert actual.tobytes() == expected.tobytes(), (
                f"tile {index} (kind {kind}, shape {shape}, "
                f"frame {frame}) renders the wrong pixels"
            )

            expected.close()
            actual.close()
    finally:
        source.close()
        rendered.close()
