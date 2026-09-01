"""Internal representation of a converted character spritesheet."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CharacterFrame:
    """One animation frame: a rectangular region of the source sheet."""

    column: int
    row: int
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class CharacterAnimation:
    """One character animation (a row of the spritesheet layout)."""

    name: str
    speed: float
    loop: bool
    frames: tuple[CharacterFrame, ...]
    duration: float = 1.0


@dataclass(frozen=True)
class CharacterSpriteSheet:
    """A fully converted character spritesheet."""

    name: str
    source_path: Path
    width: int
    height: int
    frame_width: int
    frame_height: int
    animations: tuple[CharacterAnimation, ...]

    @property
    def frame_count(self) -> int:
        """Total number of frames across every animation."""

        return sum(
            len(animation.frames)
            for animation in self.animations
        )


@dataclass(frozen=True)
class CharacterConversionResult:
    """The conversion result for every character spritesheet."""

    sheets: tuple[CharacterSpriteSheet, ...]


__all__ = [
    "CharacterAnimation",
    "CharacterConversionResult",
    "CharacterFrame",
    "CharacterSpriteSheet",
]
