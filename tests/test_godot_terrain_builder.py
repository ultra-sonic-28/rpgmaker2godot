"""Terrain plan generation from a converted A4 tileset."""

from pathlib import Path

from PIL import Image

from rpgmaker2godot.analysis.detector import TilesetDetector
from rpgmaker2godot.atlas.builder import AtlasBuilder
from rpgmaker2godot.conversion.converter import SimpleConverter
from rpgmaker2godot.godot.atlas.atlas_mapper import GodotAtlasMapper
from rpgmaker2godot.godot.terrain.terrain_builder import GodotTerrainBuilder
from rpgmaker2godot.godot.tileset.tileset_builder import GodotTileSetBuilder


def write_single_material_a4_sheet(path: Path) -> None:
    """A4 sheet with one opaque wall material (column 0, band 0)."""

    sheet = Image.new("RGBA", (768, 720), (0, 0, 0, 0))

    for y in range(0, 144, 24):
        for x in range(0, 96, 24):
            qx, qy = x // 24, y // 24

            sheet.paste(
                ((qx * 37) % 256, (qy * 61) % 256, 30, 255),
                (x, y, x + 24, y + 24),
            )

    for y in range(144, 240, 24):
        for x in range(0, 96, 24):
            qx, qy = x // 24, (y - 144) // 24

            sheet.paste(
                ((qx * 37) % 256, (qy * 61) % 256, 90, 255),
                (x, y, x + 24, y + 24),
            )

    sheet.save(path)
    sheet.close()


def build_pipeline(tmp_path: Path):
    """Run detection → conversion → atlas → Godot tileset."""

    source = tmp_path / "Inside_A4.png"

    write_single_material_a4_sheet(source)

    analysis = TilesetDetector().analyze(tmp_path)
    conversion = SimpleConverter().convert(analysis)

    atlas = AtlasBuilder().build(conversion.tilesets[0])
    mapping = GodotAtlasMapper().map(atlas)
    godot_tileset = GodotTileSetBuilder().build(mapping, source)

    return conversion.tilesets[0], godot_tileset


def tile_by_kind_shape(godot_tileset, kind: int, shape: int):
    for source in godot_tileset.atlas_sources:
        for tile in source.tiles:
            tile_kind, tile_shape = divmod(tile.ref.index, 48)

            if (tile_kind, tile_shape) == (kind, shape):
                return tile

    raise AssertionError(f"No tile for (kind={kind}, shape={shape})")


def test_builds_one_terrain_set_per_material_part(tmp_path) -> None:
    tileset, godot_tileset = build_pipeline(tmp_path)

    plan = GodotTerrainBuilder().build(tileset, godot_tileset)

    assert len(plan.terrain_sets) == 2

    top_set, side_set = plan.terrain_sets

    assert top_set.mode == 0  # MATCH_CORNERS_AND_SIDES
    assert side_set.mode == 2  # MATCH_SIDES

    assert top_set.terrains[0].name == "Wall top 1"
    assert side_set.terrains[0].name == "Wall side 1"

    # Both parts of one material share its color.
    assert top_set.terrains[0].color == side_set.terrains[0].color


def test_assigns_terrains_to_used_material_tiles(tmp_path) -> None:
    tileset, godot_tileset = build_pipeline(tmp_path)

    plan = GodotTerrainBuilder().build(tileset, godot_tileset)

    interior = tile_by_kind_shape(godot_tileset, 0, 0)

    terrain = plan.tile_terrains[interior.ref]

    assert terrain.set_index == 0
    assert terrain.terrain_index == 0

    # Fully surrounded Wall Top: every direction connects.
    assert len(terrain.peering_bits) == 8

    side_variant = tile_by_kind_shape(godot_tileset, 8, 1)

    side_terrain = plan.tile_terrains[side_variant.ref]

    assert side_terrain.set_index == 1

    # Wall Side shape 1: left border — no left bit, three side bits.
    bit_names = {name for name, _ in side_terrain.peering_bits}

    assert bit_names == {"top_side", "right_side", "bottom_side"}


def test_leaves_unused_material_tiles_without_terrain(tmp_path) -> None:
    tileset, godot_tileset = build_pipeline(tmp_path)

    plan = GodotTerrainBuilder().build(tileset, godot_tileset)

    unused = tile_by_kind_shape(godot_tileset, 1, 0)

    assert unused.ref not in plan.tile_terrains


def write_single_material_a3_sheet(path: Path) -> None:
    """A3 sheet with one opaque building material (column 0, band 0).

    Kind 0 (roof row) and kind 8 (wall row) are drawn with distinct
    quarter colours; every other source region stays transparent.
    """

    sheet = Image.new("RGBA", (768, 384), (0, 0, 0, 0))

    for y in range(0, 96, 24):
        for x in range(0, 96, 24):
            qx, qy = x // 24, y // 24

            sheet.paste(
                ((qx * 37) % 256, (qy * 61) % 256, 30, 255),
                (x, y, x + 24, y + 24),
            )

    for y in range(96, 192, 24):
        for x in range(0, 96, 24):
            qx, qy = x // 24, (y - 96) // 24

            sheet.paste(
                ((qx * 37) % 256, (qy * 61) % 256, 90, 255),
                (x, y, x + 24, y + 24),
            )

    sheet.save(path)
    sheet.close()


def build_a3_pipeline(tmp_path: Path):
    """Run detection → conversion → atlas → Godot tileset for A3."""

    source = tmp_path / "Inside_A3.png"

    write_single_material_a3_sheet(source)

    analysis = TilesetDetector().analyze(tmp_path)
    conversion = SimpleConverter().convert(analysis)

    atlas = AtlasBuilder().build(conversion.tilesets[0])
    mapping = GodotAtlasMapper().map(atlas)
    godot_tileset = GodotTileSetBuilder().build(mapping, source)

    return conversion.tilesets[0], godot_tileset


def test_a3_builds_one_terrain_set_per_material_part(tmp_path) -> None:
    tileset, godot_tileset = build_a3_pipeline(tmp_path)

    plan = GodotTerrainBuilder().build(tileset, godot_tileset)

    assert len(plan.terrain_sets) == 2

    roof_set, wall_set = plan.terrain_sets

    # Every A3 row composes from the wall table: side matching only.
    assert roof_set.mode == 2  # MATCH_SIDES
    assert wall_set.mode == 2  # MATCH_SIDES

    assert roof_set.terrains[0].name == "Roof 1"
    assert wall_set.terrains[0].name == "Wall 1"

    # Both parts of one material share its color.
    assert roof_set.terrains[0].color == wall_set.terrains[0].color


def test_a3_assigns_side_only_peering_bits(tmp_path) -> None:
    tileset, godot_tileset = build_a3_pipeline(tmp_path)

    plan = GodotTerrainBuilder().build(tileset, godot_tileset)

    roof = tile_by_kind_shape(godot_tileset, 0, 0)

    terrain = plan.tile_terrains[roof.ref]

    assert terrain.set_index == 0
    assert terrain.terrain_index == 0

    # Fully surrounded wall-table shape: every side connects, no
    # corner bit (sides-only matching).
    bit_names = {name for name, _ in terrain.peering_bits}

    assert bit_names == {
        "top_side",
        "right_side",
        "bottom_side",
        "left_side",
    }

    wall_variant = tile_by_kind_shape(godot_tileset, 8, 1)

    wall_terrain = plan.tile_terrains[wall_variant.ref]

    assert wall_terrain.set_index == 1

    # Wall shape 1: left border — no left bit, three side bits.
    wall_bit_names = {name for name, _ in wall_terrain.peering_bits}

    assert wall_bit_names == {"top_side", "right_side", "bottom_side"}


def test_a3_leaves_unused_material_tiles_without_terrain(tmp_path) -> None:
    tileset, godot_tileset = build_a3_pipeline(tmp_path)

    plan = GodotTerrainBuilder().build(tileset, godot_tileset)

    # Kind 1's region is transparent: its tile has no terrain.
    unused = tile_by_kind_shape(godot_tileset, 1, 0)

    assert unused.ref not in plan.tile_terrains


def write_single_material_a2_sheet(path: Path) -> None:
    """A2 sheet with one opaque ground material (column 0, row 0).

    Kind 0's 96x144 source region is drawn with distinct quarter
    colours; every other source region stays transparent.
    """

    sheet = Image.new("RGBA", (768, 576), (0, 0, 0, 0))

    for y in range(0, 144, 24):
        for x in range(0, 96, 24):
            qx, qy = x // 24, y // 24

            sheet.paste(
                ((qx * 37) % 256, (qy * 61) % 256, 30, 255),
                (x, y, x + 24, y + 24),
            )

    sheet.save(path)
    sheet.close()


def build_a2_pipeline(tmp_path: Path):
    """Run detection → conversion → atlas → Godot tileset for A2."""

    source = tmp_path / "Inside_A2.png"

    write_single_material_a2_sheet(source)

    analysis = TilesetDetector().analyze(tmp_path)
    conversion = SimpleConverter().convert(analysis)

    atlas = AtlasBuilder().build(conversion.tilesets[0])
    mapping = GodotAtlasMapper().map(atlas)
    godot_tileset = GodotTileSetBuilder().build(mapping, source)

    return conversion.tilesets[0], godot_tileset


def test_a2_builds_one_ground_terrain_set(tmp_path) -> None:
    tileset, godot_tileset = build_a2_pipeline(tmp_path)

    plan = GodotTerrainBuilder().build(tileset, godot_tileset)

    assert len(plan.terrain_sets) == 1

    ground_set = plan.terrain_sets[0]

    # A2 grounds compose from the floor table: blob matching.
    assert ground_set.mode == 0  # MATCH_CORNERS_AND_SIDES
    assert ground_set.terrains[0].name == "Ground 1"


def test_a2_assigns_blob_peering_bits(tmp_path) -> None:
    tileset, godot_tileset = build_a2_pipeline(tmp_path)

    plan = GodotTerrainBuilder().build(tileset, godot_tileset)

    interior = tile_by_kind_shape(godot_tileset, 0, 0)

    terrain = plan.tile_terrains[interior.ref]

    assert terrain.set_index == 0
    assert terrain.terrain_index == 0

    # Fully surrounded floor-table shape: every side and corner
    # connects.
    assert len(terrain.peering_bits) == 8

    # Shape 47 (isolated): no peering bit at all.
    isolated = tile_by_kind_shape(godot_tileset, 0, 47)

    isolated_terrain = plan.tile_terrains[isolated.ref]

    assert isolated_terrain.set_index == 0
    assert isolated_terrain.peering_bits == ()


def test_a2_leaves_unused_material_tiles_without_terrain(tmp_path) -> None:
    tileset, godot_tileset = build_a2_pipeline(tmp_path)

    plan = GodotTerrainBuilder().build(tileset, godot_tileset)

    # Kind 1's region is transparent: its tile has no terrain.
    unused = tile_by_kind_shape(godot_tileset, 1, 0)

    assert unused.ref not in plan.tile_terrains


def test_a2_ground_materials_precede_a3_and_a4_materials(tmp_path) -> None:
    """Material numbering runs A2 grounds → A3 buildings → A4 walls."""

    a2_path = tmp_path / "Inside_A2.png"
    a3_path = tmp_path / "Inside_A3.png"
    a4_path = tmp_path / "Inside_A4.png"

    write_single_material_a2_sheet(a2_path)
    write_single_material_a3_sheet(a3_path)
    write_single_material_a4_sheet(a4_path)

    analysis = TilesetDetector().analyze(tmp_path)
    conversion = SimpleConverter().convert(analysis)

    autotile_tileset = conversion.tilesets[0]

    atlas = AtlasBuilder().build(autotile_tileset)
    mapping = GodotAtlasMapper().map(atlas)
    godot_tileset = GodotTileSetBuilder().build(mapping, a2_path)

    plan = GodotTerrainBuilder().build(autotile_tileset, godot_tileset)

    names = [
        terrain.name
        for terrain_set in plan.terrain_sets
        for terrain in terrain_set.terrains
    ]

    assert names == [
        "Ground 1",
        "Roof 2",
        "Wall 2",
        "Wall top 3",
        "Wall side 3",
    ]