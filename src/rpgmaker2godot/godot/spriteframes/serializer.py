from .models import GodotSpriteFramesResource


class GodotSpriteFramesSerializer:
    """Serialize a Godot SpriteFrames resource (Godot 4 text format).

    The output mirrors what the Godot editor writes for a
    ``SpriteFrames`` resource: one external ``Texture2D`` resource,
    one ``AtlasTexture`` sub-resource per animation frame and the
    ``animations`` array — kept multi-line like Godot's own output,
    since a single-line array would not stay readable for 23 frames.
    """

    def serialize(
        self,
        resource: GodotSpriteFramesResource,
    ) -> str:
        lines: list[str] = []

        load_steps = resource.frame_count + 2

        lines.append(
            f'[gd_resource type="SpriteFrames" '
            f"load_steps={load_steps} format=3]"
        )
        lines.append("")

        texture = resource.texture

        lines.append(
            f'[ext_resource type="{texture.resource_type}" '
            f'path="{texture.path}" id="{texture.resource_id}"]'
        )
        lines.append("")

        for animation in resource.animations:
            for frame in animation.frames:
                lines.append(
                    f'[sub_resource type="AtlasTexture" '
                    f'id="{frame.resource_id}"]'
                )

                lines.append(
                    f'atlas = ExtResource("{texture.resource_id}")'
                )

                lines.append(
                    "region = Rect2("
                    f"{_format_coordinate(frame.x)}, "
                    f"{_format_coordinate(frame.y)}, "
                    f"{_format_coordinate(frame.width)}, "
                    f"{_format_coordinate(frame.height)})"
                )

                lines.append("")

        lines.append("[resource]")

        if not resource.animations:
            lines.append("animations = []")
        else:
            # The animations array mirrors the multi-line style the
            # Godot editor writes: the first entry opens on the
            # "animations" line, entries are separated by "}, {" and
            # the array closes with "}]".
            lines.append("animations = [{")

            for animation_index, animation in enumerate(
                resource.animations,
            ):
                if animation_index > 0:
                    lines.append("}, {")

                frames = animation.frames

                if frames:
                    lines.append('"frames": [{')

                    for frame_index, frame in enumerate(frames):
                        if frame_index > 0:
                            lines.append("}, {")

                        lines.append('"duration": 1.0,')

                        lines.append(
                            f'"texture": SubResource("{frame.resource_id}")'
                        )

                    lines.append("}],")
                else:
                    lines.append('"frames": [],')

                lines.append(
                    f'"loop": {"true" if animation.loop else "false"},'
                )

                lines.append(f'"name": &"{animation.name}",')

                lines.append(f'"speed": {_format_float(animation.speed)}')

            lines.append("}]")

        lines.append("")

        return "\n".join(lines)


def _format_coordinate(value: float) -> str:
    """Format one coordinate the way Godot writes float32 values.

    Integral values are written without a decimal part,
    matching Godot's own output (e.g. "48", not "48.0").
    """

    if value == int(value):
        return str(int(value))

    return repr(value)


def _format_float(value: float) -> str:
    """Format a plain float property (e.g. an animation speed)."""

    return repr(float(value))
