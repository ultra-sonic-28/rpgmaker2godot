from .resource import (
    GodotTileSetResource,
)


class GodotResourceSerializer:
    """Serialize a minimal Godot TileSet resource."""

    def serialize(
        self,
        resource: GodotTileSetResource,
    ) -> str:
        lines: list[str] = []

        lines.append(
            '[gd_resource type="TileSet" load_steps=3 format=3]'
        )
        lines.append("")

        texture = resource.texture

        lines.append(
            f'[ext_resource type="{texture.resource_type}" '
            f'path="{texture.path}" id="{texture.resource_id}"]'
        )
        lines.append("")

        atlas = resource.atlas_source

        lines.append(
            '[sub_resource type="TileSetAtlasSource" '
            f'id="{atlas.resource_id}"]'
        )

        lines.append(
            f'texture = ExtResource("{atlas.texture_resource_id}")'
        )

        lines.append(
            "texture_region_size = "
            f"Vector2i({atlas.tile_width}, {atlas.tile_height})"
        )

        for tile in atlas.tiles:
            if tile.width != 1 or tile.height != 1:
                lines.append(
                    f"{tile.column}:{tile.row}/size_in_atlas = "
                    f"Vector2i({tile.width}, {tile.height})"
                )

            lines.append(
                f"{tile.column}:{tile.row}/0 = 0"
            )

            if tile.terrain is not None:
                lines.append(
                    f"{tile.column}:{tile.row}/0/terrain_set = "
                    f"{tile.terrain.set_index}"
                )

                lines.append(
                    f"{tile.column}:{tile.row}/0/terrain = "
                    f"{tile.terrain.terrain_index}"
                )

                for bit_name, bit_terrain in tile.terrain.peering_bits:
                    lines.append(
                        f"{tile.column}:{tile.row}/0/"
                        f"terrains_peering_bit/{bit_name} = "
                        f"{bit_terrain}"
                    )

            if tile.collision is not None:
                for polygon_index, polygon in enumerate(
                    tile.collision.polygons,
                ):
                    lines.append(
                        f"{tile.column}:{tile.row}/0/"
                        f"physics_layer_0/polygon_{polygon_index}/points = "
                        f"{self._serialize_polygon_points(polygon)}"
                    )

        lines.append("")

        lines.append("[resource]")

        lines.append(
            "tile_size = "
            f"Vector2i({resource.tile_width}, {resource.tile_height})"
        )

        for index, terrain_set in enumerate(resource.terrain_sets):
            lines.append(
                f"terrain_set_{index}/mode = {terrain_set.mode}"
            )

            for terrain_index, terrain in enumerate(terrain_set.terrains):
                lines.append(
                    f"terrain_set_{index}/terrain_{terrain_index}/name = "
                    f'"{terrain.name}"'
                )

                red, green, blue = terrain.color

                lines.append(
                    f"terrain_set_{index}/terrain_{terrain_index}/color = "
                    f"Color("
                    f"{_format_coordinate(red)}, "
                    f"{_format_coordinate(green)}, "
                    f"{_format_coordinate(blue)}, 1)"
                )

        if resource.has_physics_layer:
            lines.append(
                "physics_layer_0/collision_layer = 1"
            )

        lines.append(
            'sources/0 = '
            f'SubResource("{atlas.resource_id}")'
        )

        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _serialize_polygon_points(
        points: tuple[tuple[float, float], ...],
    ) -> str:
        """Serialize polygon points as a Godot PackedVector2Array."""

        coordinates: list[str] = []

        for x, y in points:
            coordinates.append(_format_coordinate(x))
            coordinates.append(_format_coordinate(y))

        return f"PackedVector2Array({', '.join(coordinates)})"


def _format_coordinate(value: float) -> str:
    """Format one coordinate the way Godot writes float32 values.

    Integral values are written without a decimal part,
    matching Godot's own output (e.g. "48", not "48.0").
    """

    if value == int(value):
        return str(int(value))

    return repr(value)