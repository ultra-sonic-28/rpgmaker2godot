from pathlib import Path

from PIL import Image

from rpgmaker2godot.atlas.writer import AtlasWriter
from rpgmaker2godot.atlas.models import Atlas, AtlasPlacement
from rpgmaker2godot.model import SheetType, TileRef


def test_writes_atlas_dimensions(tmp_path: Path) -> None:
    source_path = tmp_path / "Inside_B.png"

    Image.new(
        "RGBA",
        (96, 96),
        (255, 0, 0, 255),
    ).save(source_path)

    atlas = Atlas(
        width=96,
        height=96,
        tile_width=48,
        tile_height=48,
        placements=(
            AtlasPlacement(
                tile=TileRef(
                    tileset="Inside",
                    sheet_type=SheetType.B,
                    index=0,
                ),
                source_path=source_path,
                source_x=0,
                source_y=0,
                atlas_x=0,
                atlas_y=0,
                width=48,
                height=48,
            ),
        ),
    )

    output_path = tmp_path / "atlas.png"

    AtlasWriter().write(
        atlas,
        output_path,
    )

    with Image.open(output_path) as image:
        assert image.size == (96, 96)
        assert image.mode == "RGBA"


def test_writes_tiles_at_explicit_positions(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "Inside_B.png"

    source = Image.new(
        "RGBA",
        (96, 48),
    )

    source.paste(
        (255, 0, 0, 255),
        (0, 0, 48, 48),
    )

    source.paste(
        (0, 0, 255, 255),
        (48, 0, 96, 48),
    )

    source.save(source_path)

    atlas = Atlas(
        width=96,
        height=48,
        tile_width=48,
        tile_height=48,
        placements=(
            AtlasPlacement(
                tile=TileRef(
                    tileset="Inside",
                    sheet_type=SheetType.B,
                    index=0,
                ),
                source_path=source_path,
                source_x=48,
                source_y=0,
                atlas_x=0,
                atlas_y=0,
                width=48,
                height=48,
            ),
            AtlasPlacement(
                tile=TileRef(
                    tileset="Inside",
                    sheet_type=SheetType.B,
                    index=1,
                ),
                source_path=source_path,
                source_x=0,
                source_y=0,
                atlas_x=48,
                atlas_y=0,
                width=48,
                height=48,
            ),
        ),
    )

    output_path = tmp_path / "atlas.png"

    AtlasWriter().write(
        atlas,
        output_path,
    )

    with Image.open(output_path) as image:
        assert image.getpixel((24, 24)) == (
            0,
            0,
            255,
            255,
        )

        assert image.getpixel((72, 24)) == (
            255,
            0,
            0,
            255,
        )


def test_atlas_background_is_transparent(
    tmp_path: Path,
) -> None:
    atlas = Atlas(
        width=96,
        height=96,
        tile_width=48,
        tile_height=48,
        placements=(),
    )

    output_path = tmp_path / "atlas.png"

    AtlasWriter().write(
        atlas,
        output_path,
    )

    with Image.open(output_path) as image:
        assert image.mode == "RGBA"
        assert image.getpixel((0, 0)) == (
            0,
            0,
            0,
            0,
        )