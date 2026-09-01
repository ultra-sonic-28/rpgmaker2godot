"""Resource models for a Godot SpriteFrames (.tres) resource."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GodotSpriteFramesTexture:
    """External texture resource referenced by the SpriteFrames."""

    resource_id: str
    resource_type: str
    path: str


@dataclass(frozen=True)
class GodotSpriteFramesFrame:
    """One AtlasTexture sub-resource cropping the sheet texture."""

    resource_id: str
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class GodotSpriteFramesAnimation:
    """One named animation of the SpriteFrames resource."""

    name: str
    speed: float
    loop: bool
    frames: tuple[GodotSpriteFramesFrame, ...]


@dataclass(frozen=True)
class GodotSpriteFramesResource:
    """A complete Godot SpriteFrames resource."""

    texture: GodotSpriteFramesTexture
    animations: tuple[GodotSpriteFramesAnimation, ...]

    @property
    def frame_count(self) -> int:
        """Total number of AtlasTexture sub-resources."""

        return sum(
            len(animation.frames)
            for animation in self.animations
        )


__all__ = [
    "GodotSpriteFramesAnimation",
    "GodotSpriteFramesFrame",
    "GodotSpriteFramesResource",
    "GodotSpriteFramesTexture",
]
