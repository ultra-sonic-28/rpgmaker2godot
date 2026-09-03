from pathlib import Path

from PIL import Image

from rpgmaker2godot.atlas.builder import AtlasBuilder
from rpgmaker2godot.atlas.models import Atlas, AtlasPlacement
from rpgmaker2godot.atlas.writer import AtlasWriter
from rpgmaker2godot.model import SheetType, TileRef
from tests.helpers.atlas import (
    make_sheet,
    make_tileset_with_sheets,
)


def create_source_image(
    path: Path,
    size: tuple[int, int],
    color: tuple[int, int, int, int],
) -> None:
    Image.new(
        "RGBA",
        size,
        color,
    ).save(path)


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


def test_writes_a4_quarter_composed_tile(
    tmp_path: Path,
) -> None:
    """An A4 placement composes its four 24x24 quarters in the atlas.

    Build a minimal 768x720 A4 sheet where each 24x24 quarter has a
    unique colour, then export an unfolded tile and check that the
    resulting atlas cell contains the four quarters selected by the
    engine shape table (here Wall Top, autotile 0, shape 0).
    """

    from rpgmaker2godot.tileset.autotile.a4 import a4_shape_quarters

    source_path = tmp_path / "Inside_A4.png"
    source = Image.new("RGBA", (768, 720))
    for y in range(0, 720, 24):
        for x in range(0, 768, 24):
            qx, qy = x // 24, y // 24
            # Deterministic unique colour per quarter.
            source.paste(
                ((qx * 37) % 256, (qy * 61) % 256, (qx + qy * 3) % 256, 255),
                (x, y, x + 24, y + 24),
            )
    source.save(source_path)

    # Use SimpleConverter to unfold the A4 sheet into tiles.
    from rpgmaker2godot.analysis.detector import TilesetDetector
    from rpgmaker2godot.conversion.converter import SimpleConverter

    analysis = TilesetDetector().analyze(tmp_path)
    conversion = SimpleConverter().convert(analysis)

    tileset = conversion.tilesets[0]
    # Placements for the whole tileset (A4 only here).
    atlas = AtlasBuilder().build(tileset)

    # Take the placement for tile index 0 (autotile 0, shape 0).
    a4_placements = [
        p
        for p in atlas.placements
        if p.tile.sheet_type == SheetType.A4
    ]
    assert len(a4_placements) == 24 * 48 + 24 * 16
    placement0 = a4_placements[0]

    # Atlas position of the first A4 tile (in the packed region).
    ax, ay = placement0.atlas_x, placement0.atlas_y
    assert (ax, ay) == (0, 0)

    # The engine shape table picks quarters for (kind 0, shape 0).
    quarters = a4_shape_quarters(0, 0)

    output_path = tmp_path / "atlas.png"
    AtlasWriter().write(atlas, output_path)

    with Image.open(output_path) as image:
        # Each 24x24 quadrant of the atlas tile must carry the colour of
        # the matching source quarter.
        for index, (qx, qy, dx, dy) in enumerate(quarters):
            # The source quarter colour.
            sx, sy = qx, qy
            expected = source.getpixel((sx + 12, sy + 12))
            # The atlas pixel at the destination quadrant's centre.
            actual = image.getpixel((ax + dx + 12, ay + dy + 12))
            assert actual == expected, (
                f"quarter {index}: expected {expected} got {actual}"
            )

    image.close()
    source.close()


def test_writes_a3_quarter_composed_tile(
    tmp_path: Path,
) -> None:
    """An A3 placement composes its four 24x24 quarters in the atlas.

    Build a minimal 768x384 A3 sheet where each 24x24 quarter has a
    unique colour, then export an unfolded tile and check that the
    resulting atlas cell contains the four quarters selected by the
    engine shape table (here Roof, autotile 0, shape 0).
    """

    from rpgmaker2godot.tileset.autotile.a3 import a3_shape_quarters

    source_path = tmp_path / "Inside_A3.png"
    source = Image.new("RGBA", (768, 384))
    for y in range(0, 384, 24):
        for x in range(0, 768, 24):
            qx, qy = x // 24, y // 24
            # Deterministic unique colour per quarter.
            source.paste(
                ((qx * 37) % 256, (qy * 61) % 256, (qx + qy * 3) % 256, 255),
                (x, y, x + 24, y + 24),
            )
    source.save(source_path)

    # Use SimpleConverter to unfold the A3 sheet into tiles.
    from rpgmaker2godot.analysis.detector import TilesetDetector
    from rpgmaker2godot.conversion.converter import SimpleConverter

    analysis = TilesetDetector().analyze(tmp_path)
    conversion = SimpleConverter().convert(analysis)

    tileset = conversion.tilesets[0]
    # Placements for the whole tileset (A3 only here).
    atlas = AtlasBuilder().build(tileset)

    # Take the placement for tile index 0 (autotile 0, shape 0).
    a3_placements = [
        p
        for p in atlas.placements
        if p.tile.sheet_type == SheetType.A3
    ]
    assert len(a3_placements) == 32 * 16
    placement0 = a3_placements[0]

    # Atlas position of the first A3 tile (in the packed region).
    ax, ay = placement0.atlas_x, placement0.atlas_y
    assert (ax, ay) == (0, 0)

    # The engine shape table picks quarters for (kind 0, shape 0).
    quarters = a3_shape_quarters(0, 0)

    output_path = tmp_path / "atlas.png"
    AtlasWriter().write(atlas, output_path)

    with Image.open(output_path) as image:
        # Each 24x24 quadrant of the atlas tile must carry the colour of
        # the matching source quarter.
        for index, (qx, qy, dx, dy) in enumerate(quarters):
            # The source quarter colour.
            sx, sy = qx, qy
            expected = source.getpixel((sx + 12, sy + 12))
            # The atlas pixel at the destination quadrant's centre.
            actual = image.getpixel((ax + dx + 12, ay + dy + 12))
            assert actual == expected, (
                f"quarter {index}: expected {expected} got {actual}"
            )

    image.close()
    source.close()


def test_writes_a4_autotile_on_transparent_background(
    tmp_path: Path,
) -> None:
    """A4 autotile tiles must sit on a transparent background.

    The composed 48x48 tiles are drawn onto the transparent atlas
    canvas and every source quarter keeps its alpha channel: fully
    transparent quarters stay transparent, semi-transparent pixels are
    preserved, and the surrounding canvas remains transparent too.
    """

    from rpgmaker2godot.analysis.detector import TilesetDetector
    from rpgmaker2godot.conversion.converter import SimpleConverter
    from rpgmaker2godot.tileset.autotile.a4 import a4_shape_quarters

    source_path = tmp_path / "Inside_A4.png"
    source = Image.new("RGBA", (768, 720), (0, 0, 0, 0))

    # Quarter with a recognizable alpha = unique per 24x24 cell.
    for y in range(0, 720, 24):
        for x in range(0, 768, 24):
            qx, qy = x // 24, y // 24
            alpha = (qx * 7 + qy * 5) % 256
            source.paste(
                (120, 90, 60, alpha),
                (x, y, x + 24, y + 24),
            )
    source.save(source_path)

    analysis = TilesetDetector().analyze(tmp_path)
    conversion = SimpleConverter().convert(analysis)
    atlas = AtlasBuilder().build(conversion.tilesets[0])

    output_path = tmp_path / "atlas.png"
    AtlasWriter().write(atlas, output_path)

    # Autotile 0 (Wall Top), shape 0 -- engine-selected quarters.
    quarters = a4_shape_quarters(0, 0)

    with Image.open(output_path) as image:
        assert image.mode == "RGBA"

        for index, (sx, sy, dx, dy) in enumerate(quarters):
            src_alpha = source.getpixel((sx + 12, sy + 12))[3]
            out_alpha = image.getpixel((dx + 12, dy + 12))[3]
            assert out_alpha == src_alpha, (
                f"quarter {index}: source alpha {src_alpha} != "
                f"output alpha {out_alpha}"
            )

        # A quarter that is fully transparent must stay a transparent
        # hole (alpha 0) in the output.
        for index, (sx, sy, dx, dy) in enumerate(quarters):
            if source.getpixel((sx + 12, sy + 12))[3] == 0:
                assert image.getpixel((dx + 12, dy + 12))[3] == 0

    source.close()


def test_writes_multi_sheet_atlas(tmp_path: Path) -> None:
    create_source_image(
        tmp_path / "Inside_A5.png",
        (96, 96),
        (255, 0, 0, 255),
    )

    create_source_image(
        tmp_path / "Inside_B.png",
        (96, 96),
        (0, 255, 0, 255),
    )

    create_source_image(
        tmp_path / "Inside_C.png",
        (96, 96),
        (0, 0, 255, 255),
    )

    tileset = make_tileset_with_sheets(
        make_sheet(
            SheetType.A5,
            width=96,
            height=96,
            source_directory=tmp_path,
        ),
        make_sheet(
            SheetType.B,
            width=96,
            height=96,
            source_directory=tmp_path,
        ),
        make_sheet(
            SheetType.C,
            width=96,
            height=96,
            source_directory=tmp_path,
        ),
    )

    atlas = AtlasBuilder().build(tileset)

    output_path = tmp_path / "atlas.png"

    AtlasWriter().write(
        atlas,
        output_path,
    )

    with Image.open(output_path) as image:
        assert image.size == (96, 288)

        assert image.getpixel((24, 24)) == (
            255,
            0,
            0,
            255,
        )

        assert image.getpixel((24, 120)) == (
            0,
            255,
            0,
            255,
        )

        assert image.getpixel((24, 216)) == (
            0,
            0,
            255,
            255,
        )