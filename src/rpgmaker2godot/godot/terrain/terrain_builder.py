"""Build Godot terrain sets from the unfolded A3/A4 autotiles.

One terrain set is generated per material part, so painting a wall in
the Godot editor reproduces RPG Maker's ``_addAutotile`` behaviour:

* ``Roof x`` / ``Wall x`` (A3 buildings) — mode ``MATCH_SIDES`` (the
  wall-table side matching, shared by every A3 autotile);
* ``Wall top x`` (A4) — mode ``MATCH_CORNERS_AND_SIDES`` (the
  floor-table blob matching);
* ``Wall side x`` (A4) — mode ``MATCH_SIDES`` (the wall-table side
  matching).

A terrain set carries a single matching mode, which is why the top and
the side of one A4 wall material live in two sets. The A3 roof and wall
rows always use the side matching. Materials are numbered continuously
across the tileset's sheets (A3 buildings first, then A4 walls,
following the atlas stacking order) and detected automatically from
the source sheets' slots whose region is not fully transparent.
"""

import colorsys
from dataclasses import dataclass

from PIL import Image

from rpgmaker2godot.godot.model import (
    GodotTerrain,
    GodotTerrainPlan,
    GodotTerrainSet,
    GodotTileSet,
    GodotTileTerrain,
)
from rpgmaker2godot.model import SheetType
from rpgmaker2godot.model.tileset import Tileset
from rpgmaker2godot.tileset.autotile.a3 import (
    A3_AUTOTILE_COUNT,
    A3_SHAPES_PER_AUTOTILE,
    a3_source_region,
)
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
BUILDING_BAND_COUNT = 2
WALL_BAND_COUNT = 3

WALL_TOP_REGION_HEIGHT = 144
WALL_SIDE_REGION_HEIGHT = 96

# A3 source regions are square: one 96x96 slot per autotile.
A3_REGION_WIDTH = 96
A3_REGION_HEIGHT = 96


@dataclass(frozen=True)
class TerrainResolution:
    """Result of the terrain *resolution* phase.

    The A3/A4 source images have been scanned for drawn autotiles and
    the matching terrain sets (their modes, names and material colours)
    are known. Attaching the terrains to the individual Godot atlas
    tiles is not part of this result: it only needs the Godot tileset
    and is deferred to the *assignment* phase, performed during export.

    ``kind_assignment`` maps each autotile sheet type to its
    ``kind -> (set_index, is_floor)`` entries: ``is_floor`` selects the
    corners-and-sides (blob) matching of the A4 Wall Tops, while every
    A3 part and A4 Wall Side uses the side matching.
    """

    terrain_sets: tuple[GodotTerrainSet, ...]
    kind_assignment: dict[SheetType, dict[int, tuple[int, bool]]]


class GodotTerrainBuilder:
    """Derive the Godot terrain plan from a converted tileset."""

    def resolve(
        self,
        tileset: Tileset,
    ) -> TerrainResolution:
        """Detect the drawn A3/A4 autotiles and define their terrain sets.

        This is the resolution/definition phase: it only reads the A3/A4
        source images, so it can run before the Godot tileset is built
        and be reported as its own CLI step.
        """

        a3_sheets = [
            sheet
            for sheet in tileset.sheets
            if sheet.sheet_type == SheetType.A3
        ]

        a4_sheets = [
            sheet
            for sheet in tileset.sheets
            if sheet.sheet_type == SheetType.A4
        ]

        if not a3_sheets and not a4_sheets:
            return TerrainResolution((), {})

        if len(a3_sheets) > 1:
            raise ValueError(
                "Terrain generation supports exactly one A3 sheet "
                "per tileset."
            )

        if len(a4_sheets) > 1:
            raise ValueError(
                "Terrain generation supports exactly one A4 sheet "
                "per tileset."
            )

        used_building_kinds = (
            self._detect_used_a3_kinds(a3_sheets[0].source_path)
            if a3_sheets
            else set()
        )

        used_wall_kinds = (
            self._detect_used_a4_kinds(a4_sheets[0].source_path)
            if a4_sheets
            else set()
        )

        terrain_sets, kind_assignment = self._build_sets(
            used_building_kinds,
            used_wall_kinds,
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
        """Attach the resolved terrains to the Godot tileset's A3/A4 cells."""

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

    def _detect_used_a3_kinds(self, source_path) -> set[int]:
        """Return the A3 kinds whose source region is drawn."""

        used: set[int] = set()

        with Image.open(source_path) as raw:
            source = raw.convert("RGBA")

        try:
            for kind in range(A3_AUTOTILE_COUNT):
                source_x, source_y = a3_source_region(kind)

                region = source.crop(
                    (
                        source_x,
                        source_y,
                        source_x + A3_REGION_WIDTH,
                        source_y + A3_REGION_HEIGHT,
                    )
                )

                if region.getchannel("A").getbbox() is not None:
                    used.add(kind)

                region.close()
        finally:
            source.close()

        return used

    def _detect_used_a4_kinds(self, source_path) -> set[int]:
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
        used_building_kinds: set[int],
        used_wall_kinds: set[int],
    ) -> tuple[
        list[GodotTerrainSet],
        dict[SheetType, dict[int, tuple[int, bool]]],
    ]:
        """Create one terrain set per used material part.

        The A3 building materials come first — they are stacked under
        the A4 walls in the merged atlas — then the A4 wall materials.
        The ``material`` counter (and therefore the terrain colours) is
        shared by both families.
        """

        terrain_sets: list[GodotTerrainSet] = []
        kind_assignment: dict[
            SheetType,
            dict[int, tuple[int, bool]],
        ] = {
            SheetType.A3: {},
            SheetType.A4: {},
        }

        material = 0

        # A3 buildings: two bands of one Roof row over one Wall row.
        # Both rows compose from the wall table, hence the side
        # matching for every A3 terrain set.
        for column in range(WALL_COLUMN_COUNT):
            for band in range(BUILDING_BAND_COUNT):
                roof_kind = 16 * band + column
                wall_kind = 16 * band + 8 + column

                used_roof = roof_kind in used_building_kinds
                used_wall = wall_kind in used_building_kinds

                if not (used_roof or used_wall):
                    continue

                material += 1
                color = GodotTerrainBuilder._material_color(material)

                if used_roof:
                    kind_assignment[SheetType.A3][roof_kind] = (
                        len(terrain_sets),
                        False,
                    )

                    terrain_sets.append(
                        GodotTerrainSet(
                            mode=TERRAIN_MATCH_SIDES,
                            terrains=(
                                GodotTerrain(
                                    name=f"Roof {material}",
                                    color=color,
                                ),
                            ),
                        )
                    )

                if used_wall:
                    kind_assignment[SheetType.A3][wall_kind] = (
                        len(terrain_sets),
                        False,
                    )

                    terrain_sets.append(
                        GodotTerrainSet(
                            mode=TERRAIN_MATCH_SIDES,
                            terrains=(
                                GodotTerrain(
                                    name=f"Wall {material}",
                                    color=color,
                                ),
                            ),
                        )
                    )

        # A4 walls: three bands of one Wall Top row over one Wall Side
        # row.
        for column in range(WALL_COLUMN_COUNT):
            for band in range(WALL_BAND_COUNT):
                top_kind = 16 * band + column
                side_kind = 16 * band + 8 + column

                used_top = top_kind in used_wall_kinds
                used_side = side_kind in used_wall_kinds

                if not (used_top or used_side):
                    continue

                material += 1
                color = GodotTerrainBuilder._material_color(material)

                if used_top:
                    kind_assignment[SheetType.A4][top_kind] = (
                        len(terrain_sets),
                        True,
                    )

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
                    kind_assignment[SheetType.A4][side_kind] = (
                        len(terrain_sets),
                        False,
                    )

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
        kind_assignment: dict[SheetType, dict[int, tuple[int, bool]]],
    ) -> dict:
        """Attach terrain data to every A3/A4 tile of the Godot tileset."""

        tile_terrains = {}

        shapes_per_autotile = {
            SheetType.A3: A3_SHAPES_PER_AUTOTILE,
            SheetType.A4: A4_SHAPES_PER_AUTOTILE,
        }

        for source in godot_tileset.atlas_sources:
            for tile in source.tiles:
                shapes = shapes_per_autotile.get(tile.ref.sheet_type)

                if shapes is None:
                    continue

                kind, shape = divmod(tile.ref.index, shapes)

                assignment = kind_assignment.get(tile.ref.sheet_type, {})

                if kind not in assignment:
                    continue

                set_index, is_floor = assignment[kind]

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
