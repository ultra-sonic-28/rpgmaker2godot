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

        for column, row in atlas.tiles:
            lines.append(
                f"{column}:{row}/0 = 0"
            )

        lines.append("")

        lines.append("[resource]")

        lines.append(
            "tile_size = "
            f"Vector2i({resource.tile_width}, {resource.tile_height})"
        )

        lines.append(
            'sources/0 = '
            f'SubResource("{atlas.resource_id}")'
        )

        lines.append("")

        return "\n".join(lines)