"""Build Godot terrain sets from the unfolded A4 autotiles.

One terrain set is generated per material part, so painting a wall in
the Godot editor reproduces RPG Maker's ``_addAutotile`` behaviour:

* ``Wall top x`` — mode ``MATCH_CORNERS_AND_SIDES`` (the floor-table
  blob matching);
* ``Wall side x`` — mode ``MATCH_SIDES`` (the wall-table side matching).

A terrain set carries a single matching mode, which is why the top and
the side of one wall material live in two sets. Both are named after
the same material number, detected automatically from the A4 sheet
slots whose source region is not fully transparent.
"""

import colorsys
from dataclasses import dataclass

from PIL import Image

from rpgmaker2godot.godot.model import (
    GodotTerrain,
    GodotTerrainPlan,
    GodotTerrainSet,
    GodotTileTerrain,
    GodotTileSet,
)
from rpgmaker2godot.model import SheetType
from rpgmaker2godot.model.tileset import Tileset
from rpgmaker2godot.tileset.autotile.a4 import (
    A4_AUTOTILE_COUNT,
    A4_SHAPES_PER_AUTOTILE,
    a4_source_region,
)
from rpgmaker2godot.tileset.autotile.peering import (
    floor_shape_peering,
    wall_shape_peering,
)

TERRAIN_MATCH_CORNERS_AND_SIDES = 0
TERRAIN_MATCH_SIDES = 2

WALL_COLUMN_COUNT = 8
WALL_BAND_COUNT = 3

WALL_TOP_REGION_HEIGHT = 144
WALL_SIDE_REGION_HEIGHT = 96


@dataclass(frozen=True)
class TerrainResolution:
    """Result of the terrain *resolution* phase.

    The A4 source image has been scanned for drawn autotiles and the
    matching terrain sets (their modes, names and material colours) are
    known. Attaching the terrains to the individual Godot atlas tiles is
    not part of this result: it only needs the Godot tileset and is
    deferred to the *assignment* phase, performed during export.
    """

    terrain_sets: tuple[GodotTerrainSet, ...]
    kind_assignment: dict[int, tuple[int, bool]]


class GodotTerrainBuilder:
    """Derive the Godot terrain plan from a converted tileset."""

    def resolve(
        self,
        tileset: Tileset,
    ) -> TerrainResolution:
        """Detect the drawn A4 autotiles and define their terrain sets.

        This is the resolution/definition phase: it only reads the A4
        source image, so it can run before the Godot tileset is built and
        be reported as its own CLI step.
        """

        a4_sheets = [
            sheet
            for sheet in tileset.sheets
            if sheet.sheet_type == SheetType.A4
        ]

        if not a4_sheets:
            return TerrainResolution((), {})

        if len(a4_sheets) > 1:
            raise ValueError(
                "Terrain generation supports exactly one A4 sheet "
                "per tileset."
            )

        used_kinds = self._detect_used_kinds(
            a4_sheets[0].source_path,
        )

        terrain_sets, kind_assignment = self._build_sets(
            used_kinds,
        )

        return TerrainResolution(
            terrain_sets=tuple(terrain_sets),
            kind_assignment=kind_assignment,
        )

    def assign(
        self,
        godot_tileset: GodotTileSet,
        resolution: TerrainResolution,
    ) -> GodotTerrainPlan:
        """Attach the resolved terrains to the Godot tileset's A4 cells."""

        tile_terrains = self._assign_tiles(
            godot_tileset,
            resolution.kind_assignment,
        )

        return GodotTerrainPlan(
            terrain_sets=resolution.terrain_sets,
            tile_terrains=tile_terrains,
        )

    def build(
        self,
        tileset: Tileset,
        godot_tileset: GodotTileSet,
    ) -> GodotTerrainPlan:
        """Resolve then assign terrains for one converted tileset.

        Convenience wrapper kept for callers that want a single call
        returning the fully-built plan.
        """

        return self.assign(
            godot_tileset,
            self.resolve(tileset),
        )

    def _detect_used_kinds(self, source_path) -> set[int]:
        """Return the A4 kinds whose source region is drawn."""

        used: set[int] = set()

        with Image.open(source_path) as raw:
            source = raw.convert("RGBA")

        try:
            for kind in range(A4_AUTOTILE_COUNT):
                source_x, source_y, is_side = a4_source_region(kind)

                region_height = (
                    WALL_SIDE_REGION_HEIGHT
                    if is_side
                    else WALL_TOP_REGION_HEIGHT
                )

                region = source.crop(
                    (
                        source_x,
                        source_y,
                        source_x + 96,
                        source_y + region_height,
                    )
                )

                if region.getchannel("A").getbbox() is not None:
                    used.add(kind)

                region.close()
        finally:
            source.close()

        return used

    @staticmethod
    def _build_sets(
        used_kinds: set[int],
    ) -> tuple[list[GodotTerrainSet], dict[int, tuple[int, bool]]]:
        """Create one terrain set per used material part."""

        terrain_sets: list[GodotTerrainSet] = []
        kind_assignment: dict[int, tuple[int, bool]] = {}

        material = 0

        for column in range(WALL_COLUMN_COUNT):
            for band in range(WALL_BAND_COUNT):
                top_kind = 16 * band + column
                side_kind = 16 * band + 8 + column

                used_top = top_kind in used_kinds
                used_side = side_kind in used_kinds

                if not (used_top or used_side):
                    continue

                material += 1
                color = GodotTerrainBuilder._material_color(material)

                if used_top:
                    kind_assignment[top_kind] = (len(terrain_sets), True)

                    terrain_sets.append(
                        GodotTerrainSet(
                            mode=TERRAIN_MATCH_CORNERS_AND_SIDES,
                            terrains=(
                                GodotTerrain(
                                    name=f"Wall top {material}",
                                    color=color,
                                ),
                            ),
                        )
                    )

                if used_side:
                    kind_assignment[side_kind] = (len(terrain_sets), False)

                    terrain_sets.append(
                        GodotTerrainSet(
                            mode=TERRAIN_MATCH_SIDES,
                            terrains=(
                                GodotTerrain(
                                    name=f"Wall side {material}",
                                    color=color,
                                ),
                            ),
                        )
                    )

        return terrain_sets, kind_assignment

    @staticmethod
    def _material_color(material: int) -> tuple[float, float, float]:
        """Deterministic distinct color for one material."""

        hue = ((material - 1) * 0.618033988749895) % 1.0

        red, green, blue = colorsys.hsv_to_rgb(hue, 0.55, 1.0)

        return (round(red, 4), round(green, 4), round(blue, 4))

    @staticmethod
    def _assign_tiles(
        godot_tileset: GodotTileSet,
        kind_assignment: dict[int, tuple[int, bool]],
    ) -> dict:
        """Attach terrain data to every A4 tile of the Godot tileset."""

        tile_terrains = {}

        for source in godot_tileset.atlas_sources:
            for tile in source.tiles:
                if tile.ref.sheet_type != SheetType.A4:
                    continue

                kind, shape = divmod(
                    tile.ref.index,
                    A4_SHAPES_PER_AUTOTILE,
                )

                if kind not in kind_assignment:
                    continue

                set_index, is_floor = kind_assignment[kind]

                peering = (
                    floor_shape_peering(shape)
                    if is_floor
                    else wall_shape_peering(shape)
                )

                peering_bits = tuple(
                    (name, 0)
                    for name, connected in peering
                    if connected
                )

                tile_terrains[tile.ref] = GodotTileTerrain(
                    set_index=set_index,
                    terrain_index=0,
                    peering_bits=peering_bits,
                )

        return tile_terrains
