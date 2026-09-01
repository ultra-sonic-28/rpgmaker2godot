"""Conversion of texture paths into Godot ``res://`` paths."""

from pathlib import Path


def to_godot_path(
    resource_path: Path,
    texture_path: Path,
) -> str:
    """Convert a texture path into a Godot ``res://`` path.

    ``res://`` paths are preserved as-is, relative paths are prefixed
    with ``res://`` and absolute paths must be located inside the
    resource directory (the directory holding the generated ``.tres``),
    in which case they are rewritten relative to it.
    """

    raw_path = str(texture_path)

    # Explicit Godot path.
    # On Windows, Path("res://...") becomes "res:\\..."
    # when converted back to a string.
    if raw_path.startswith("res://"):
        return raw_path

    if raw_path.startswith("res:\\"):
        return "res://" + raw_path[len("res:\\"):].replace("\\", "/")

    # Simple relative path, e.g. "Inside.png".
    if not texture_path.is_absolute():
        return f"res://{texture_path.as_posix()}"

    # Absolute filesystem path: it must be located next to the
    # generated .tres or below its directory.
    try:
        relative_path = texture_path.relative_to(
            resource_path.parent,
        )
    except ValueError:
        raise ValueError(
            "Texture path must be located inside the "
            "Godot resource directory: "
            f"{texture_path}"
        ) from None

    return f"res://{relative_path.as_posix()}"
