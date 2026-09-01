from pathlib import Path

from rpgmaker2godot.character.models import CharacterSpriteSheet
from rpgmaker2godot.godot.resource.path import to_godot_path

from .models import (
    GodotSpriteFramesAnimation,
    GodotSpriteFramesFrame,
    GodotSpriteFramesResource,
    GodotSpriteFramesTexture,
)
from .serializer import GodotSpriteFramesSerializer


class GodotSpriteFramesWriter:
    """Write a CharacterSpriteSheet as a Godot SpriteFrames .tres."""

    def __init__(
        self,
        serializer: GodotSpriteFramesSerializer | None = None,
    ) -> None:
        self._serializer = (
            serializer
            if serializer is not None
            else GodotSpriteFramesSerializer()
        )

    def write(
        self,
        sheet: CharacterSpriteSheet,
        output_path: Path,
        texture_path: Path,
    ) -> None:
        resource = self._build_resource(
            sheet,
            output_path,
            texture_path,
        )

        content = self._serializer.serialize(resource)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            content,
            encoding="utf-8",
        )

    def _build_resource(
        self,
        sheet: CharacterSpriteSheet,
        output_path: Path,
        texture_path: Path,
    ) -> GodotSpriteFramesResource:
        texture_resource_id = "1_texture"

        texture = GodotSpriteFramesTexture(
            resource_id=texture_resource_id,
            resource_type="Texture2D",
            path=to_godot_path(
                output_path,
                texture_path,
            ),
        )

        frame_counter = 0

        animations: list[GodotSpriteFramesAnimation] = []

        for animation in sheet.animations:
            frames: list[GodotSpriteFramesFrame] = []

            for frame in animation.frames:
                frame_counter += 1

                frames.append(
                    GodotSpriteFramesFrame(
                        resource_id=f"AtlasTexture_{frame_counter}",
                        x=frame.x,
                        y=frame.y,
                        width=frame.width,
                        height=frame.height,
                    )
                )

            animations.append(
                GodotSpriteFramesAnimation(
                    name=animation.name,
                    speed=animation.speed,
                    loop=animation.loop,
                    frames=tuple(frames),
                )
            )

        return GodotSpriteFramesResource(
            texture=texture,
            animations=tuple(animations),
        )
