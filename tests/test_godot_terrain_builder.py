"""Terrain plan generation from a converted A4 tileset."""

from pathlib import Path

from PIL import Image

from rpgmaker2godot.atlas.builder import AtlasBuilder
from rpgmaker2godot.analysis.detector import TilesetDetector
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