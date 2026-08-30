import subprocess
from pathlib import Path

import pytest
from PIL import Image

from rpgmaker2godot.analysis.detector import TilesetDetector
from rpgmaker2godot.conversion.converter import SimpleConverter
from rpgmaker2godot.godot.export.simple import SimpleExporter
from rpgmaker2godot.model import ConversionResult, SheetType, TileRef
from rpgmaker2godot.model.sheet import Sheet
from rpgmaker2godot.model.tile import Tile
from rpgmaker2godot.model.tile_collision import TileCollision
from rpgmaker2godot.model.tileset import Tileset
from tests.helpers.godot_atlas import make_multi_cell_conversion
from tests.helpers.godot_integration import (
    find_godot,
    write_project,
    write_validation_script,
)
from tests.test_cli import create_sheet


@pytest.mark.integration
def test_generated_tileset_loads_in_godot(
    tmp_path: Path,
) -> None:
    godot = find_godot()

    if godot is None:
        pytest.skip(
            "Godot executable not available. "
            "Set the GODOT environment variable."
        )

    input_directory = tmp_path / "tilesets"
    project_directory = tmp_path / "godot"
    generated_directory = project_directory / "generated"

    generated_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    create_sheet(
        input_directory,
        "Inside_A5.png",
    )

    create_sheet(
        input_directory,
        "Inside_B.png",
    )

    create_sheet(
        input_directory,
        "Inside_C.png",
    )

    analysis = TilesetDetector().analyze(
        input_directory,
    )

    conversion = SimpleConverter().convert(
        analysis,
    )

    SimpleExporter(godot_project_root=project_directory).export(
        conversion,
        generated_directory,
    )

    write_project(project_directory)

    script_path = write_validation_script(
        project_directory,
    )

    generated_png = generated_directory / "Inside.png"
    assert generated_png.exists()
    assert generated_png.stat().st_size > 0

    with Image.open(generated_png) as image:
        image.verify()
        
    generated_tres = generated_directory / "Inside.tres"
    assert generated_tres.exists()
    assert generated_tres.stat().st_size > 0

    content = generated_tres.read_text(encoding="utf-8")

    assert (
        'path="res://generated/Inside.png"'
        in content
    )

    subprocess.run(
        [
            godot,
            "--headless",
            "--path",
            str(project_directory),
            "--editor",
            "--quit",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    result = subprocess.run(
        [
            godot,
            "--headless",
            "--path",
            str(project_directory),
            "--script",
            str(script_path.name),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    print("IMPORT STDOUT:")
    print(result.stdout)

    print("IMPORT STDERR:")
    print(result.stderr)

    import_file = generated_directory / "Inside.png.import"

    assert import_file.exists(), (
        "Godot did not import generated PNG.\n"
        f"Expected: {import_file}\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

    assert result.returncode == 0, (
        "Godot failed to load generated TileSet.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )


@pytest.mark.integration
def test_generated_tileset_rejects_missing_atlas_cell(
    tmp_path: Path,
) -> None:
    godot = find_godot()

    if godot is None:
        pytest.skip(
            "Godot executable not available. "
            "Set the GODOT environment variable."
        )

    input_directory = tmp_path / "tilesets"
    project_directory = tmp_path / "godot"
    generated_directory = project_directory / "generated"

    generated_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    create_sheet(
        input_directory,
        "Inside_A5.png",
    )

    create_sheet(
        input_directory,
        "Inside_B.png",
    )

    create_sheet(
        input_directory,
        "Inside_C.png",
    )

    analysis = TilesetDetector().analyze(
        input_directory,
    )

    conversion = SimpleConverter().convert(
        analysis,
    )

    SimpleExporter(
        godot_project_root=project_directory,
    ).export(
        conversion,
        generated_directory,
    )

    write_project(project_directory)

    generated_tres = generated_directory / "Inside.tres"

    content = generated_tres.read_text(
        encoding="utf-8",
    )

    # Remove deliberately one atlas cell.
    content = content.replace(
        "1:3/0 = 0\n",
        "",
    )

    generated_tres.write_text(
        content,
        encoding="utf-8",
    )

    script_path = write_validation_script(
        project_directory,
        validate_all_cells=False,
        expected_missing_cell=(1, 3),
    )

    subprocess.run(
        [
            godot,
            "--headless",
            "--path",
            str(project_directory),
            "--editor",
            "--quit",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    result = subprocess.run(
        [
            godot,
            "--headless",
            "--path",
            str(project_directory),
            "--script",
            str(script_path.name),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        "Godot unexpectedly accepted a TileSet "
        "with a missing atlas cell.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )


@pytest.mark.integration
def test_generated_tileset_preserves_multi_cell_tile_sizes(
    tmp_path: Path,
) -> None:
    godot = find_godot()

    if godot is None:
        pytest.skip(
            "Godot executable not available. "
            "Set the GODOT environment variable."
        )

    project_directory = tmp_path / "godot"
    generated_directory = project_directory / "generated"

    generated_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    source_path = tmp_path / "tilesets" / "Inside_A5.png"

    create_sheet(
        source_path.parent,
        source_path.name,
        size=(192, 288),
    )

    conversion = make_multi_cell_conversion(
        source_path,
    )

    SimpleExporter(
        godot_project_root=project_directory,
    ).export(
        conversion,
        generated_directory,
    )

    write_project(project_directory)

    script_path = write_validation_script(
        project_directory,
        expected_atlas_size=(192, 288),
        expected_columns=4,
        expected_rows=6,
        validate_all_cells=False,
        expected_tile_sizes=(
            ((0, 0), (2, 1)),
            ((2, 0), (1, 2)),
            ((0, 2), (2, 3)),
        ),
    )

    subprocess.run(
        [
            godot,
            "--headless",
            "--path",
            str(project_directory),
            "--editor",
            "--quit",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    result = subprocess.run(
        [
            godot,
            "--headless",
            "--path",
            str(project_directory),
            "--script",
            str(script_path.name),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        "Godot failed to validate multi-cell TileSet.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )


def make_conversion_with_collisions(
    source_path: Path,
) -> ConversionResult:
    """Build a 2x2 B-sheet conversion carrying collision flags.

    Tiles (0,0), (1,0) and (1,1) block movement; tile (0,1) carries
    no collision information at all.
    """

    tile_size = 48

    blocked = TileCollision(
        block_down=True,
        block_left=True,
        block_right=True,
        block_up=True,
    )
    partial = TileCollision(
        block_down=True,
        block_left=False,
        block_right=False,
        block_up=False,
    )

    def make_tile(
        index: int,
        column: int,
        row: int,
        collision: TileCollision | None,
    ) -> Tile:
        return Tile(
            ref=TileRef(
                tileset="Inside",
                sheet_type=SheetType.B,
                index=index,
            ),
            column=column,
            row=row,
            x=column * tile_size,
            y=row * tile_size,
            width=tile_size,
            height=tile_size,
            collision=collision,
        )

    tiles = (
        make_tile(0, 0, 0, blocked),
        make_tile(1, 1, 0, partial),
        make_tile(2, 0, 1, None),
        make_tile(3, 1, 1, partial),
    )

    sheet = Sheet(
        sheet_type=SheetType.B,
        source_path=source_path,
        width=2 * tile_size,
        height=2 * tile_size,
        tile_width=tile_size,
        tile_height=tile_size,
        columns=2,
        rows=2,
        tiles=tiles,
    )

    return ConversionResult(
        tilesets=(
            Tileset(
                name="Inside",
                sheets=(sheet,),
            ),
        ),
    )


@pytest.mark.integration
def test_generated_tileset_loads_collision_polygons_in_godot(
    tmp_path: Path,
) -> None:
    godot = find_godot()

    if godot is None:
        pytest.skip(
            "Godot executable not available. "
            "Set the GODOT environment variable."
        )

    project_directory = tmp_path / "godot"
    generated_directory = project_directory / "generated"

    generated_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    source_path = tmp_path / "tilesets" / "Inside_B.png"

    create_sheet(
        source_path.parent,
        source_path.name,
        size=(96, 96),
    )

    conversion = make_conversion_with_collisions(source_path)

    SimpleExporter(
        godot_project_root=project_directory,
    ).export(
        conversion,
        generated_directory,
    )

    write_project(project_directory)

    # Godot collision polygons are relative to the tile CENTER.
    full_tile_points = (
        -24.0, -24.0, 24.0, -24.0, 24.0, 24.0, -24.0, 24.0,
    )
    bottom_band_points = (
        -24.0, 16.0, 24.0, 16.0, 24.0, 24.0, -24.0, 24.0,
    )

    script_path = write_validation_script(
        project_directory,
        expected_atlas_size=(96, 96),
        expected_columns=2,
        expected_rows=2,
        validate_all_cells=True,
        expected_collision_polygons=(
            # (0, 0) blocks every side: fully solid tile.
            ((0, 0), full_tile_points),
            # (1, 0) and (1, 1) only block downwards: bottom band.
            ((1, 0), bottom_band_points),
            ((1, 1), bottom_band_points),
        ),
        expected_collision_free_cells=((0, 1),),
    )

    subprocess.run(
        [
            godot,
            "--headless",
            "--path",
            str(project_directory),
            "--editor",
            "--quit",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    result = subprocess.run(
        [
            godot,
            "--headless",
            "--path",
            str(project_directory),
            "--script",
            str(script_path.name),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        "Godot failed to validate collision polygons.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )


@pytest.mark.integration
def test_generated_a4_tileset_loads_in_godot(
    tmp_path: Path,
) -> None:
    """The unfolded A4 tileset loads and exposes its unique tiles in Godot.

    A single ``*_A4.png`` (768x720) sheet holds 48 autotiles unfolded
    into 2304 raw shape variants; the duplicated Wall Side shapes are
    dropped, leaving 1536 unique tiles of 48x48. They are packed 16 per
    row, giving an atlas of 768x4608 (96 rows). The generated ``.tres``
    must load in Godot with every one of those cells present.
    """

    godot = find_godot()

    if godot is None:
        pytest.skip(
            "Godot executable not available. "
            "Set the GODOT environment variable."
        )

    input_directory = tmp_path / "tilesets"
    project_directory = tmp_path / "godot"
    generated_directory = project_directory / "generated"

    generated_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Distinct 24x24 quarters: the pixel-level deduplication keeps all
    # 1536 unfolded tiles, whose full atlas must load in Godot.
    input_directory.mkdir(parents=True, exist_ok=True)

    a4_path = input_directory / "Inside_A4.png"

    a4_sheet = Image.new("RGBA", (768, 720))

    for y in range(0, 720, 24):
        for x in range(0, 768, 24):
            qx, qy = x // 24, y // 24

            a4_sheet.paste(
                (
                    (qx * 37) % 256,
                    (qy * 61) % 256,
                    (qx + qy * 3) % 256,
                    255,
                ),
                (x, y, x + 24, y + 24),
            )

    a4_sheet.save(a4_path)
    a4_sheet.close()

    analysis = TilesetDetector().analyze(
        input_directory,
    )

    conversion = SimpleConverter().convert(
        analysis,
    )

    SimpleExporter(
        godot_project_root=project_directory,
    ).export(
        conversion,
        generated_directory,
    )

    write_project(project_directory)

    generated_png = generated_directory / "Inside.png"
    assert generated_png.exists()
    assert generated_png.stat().st_size > 0

    generated_tres = generated_directory / "Inside.tres"
    assert generated_tres.exists()
    assert generated_tres.stat().st_size > 0

    script_path = write_validation_script(
        project_directory,
        expected_atlas_size=(768, 4608),
        expected_columns=16,
        expected_rows=96,
        validate_all_cells=True,
    )

    subprocess.run(
        [
            godot,
            "--headless",
            "--path",
            str(project_directory),
            "--editor",
            "--quit",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    result = subprocess.run(
        [
            godot,
            "--headless",
            "--path",
            str(project_directory),
            "--script",
            str(script_path.name),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        "Godot failed to load the generated A4 TileSet.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )


@pytest.mark.integration
def test_generated_a4_tileset_terrains_load_in_godot(
    tmp_path: Path,
) -> None:
    """The A4 tileset exposes one terrain set per material part.

    With every 24x24 quarter drawn, all 48 kinds are used: 24 wall tops
    (MATCH_CORNERS_AND_SIDES) and 24 wall sides (MATCH_SIDES), i.e. 48
    terrain sets. Cell (0, 0) holds kind 0, shape 0 — a fully
    surrounded Wall Top expecting the terrain on all eight peering
    directions.
    """

    godot = find_godot()

    if godot is None:
        pytest.skip(
            "Godot executable not available. "
            "Set the GODOT environment variable."
        )

    input_directory = tmp_path / "tilesets"
    project_directory = tmp_path / "godot"
    generated_directory = project_directory / "generated"

    generated_directory.mkdir(parents=True, exist_ok=True)

    # Distinct 24x24 quarters: every autotile kind is used.
    input_directory.mkdir(parents=True, exist_ok=True)

    a4_path = input_directory / "Inside_A4.png"

    a4_sheet = Image.new("RGBA", (768, 720))

    for y in range(0, 720, 24):
        for x in range(0, 768, 24):
            qx, qy = x // 24, y // 24

            a4_sheet.paste(
                (
                    (qx * 37) % 256,
                    (qy * 61) % 256,
                    (qx + qy * 3) % 256,
                    255,
                ),
                (x, y, x + 24, y + 24),
            )

    a4_sheet.save(a4_path)
    a4_sheet.close()

    analysis = TilesetDetector().analyze(input_directory)

    conversion = SimpleConverter().convert(analysis)

    SimpleExporter(
        godot_project_root=project_directory,
    ).export(
        conversion,
        generated_directory,
    )

    write_project(project_directory)

    script_path = write_validation_script(
        project_directory,
        expected_atlas_size=(768, 4608),
        expected_columns=16,
        expected_rows=96,
        validate_all_cells=False,
        expected_terrain_set_count=48,
        expected_terrain_modes=(
            (0, 0),
            (1, 2),
        ),
        expected_terrain_names=(
            (0, "Wall top 1"),
            (1, "Wall side 1"),
        ),
        expected_cell_terrains=(
            ((0, 0), 0, 0),
        ),
        expected_cell_peering_bits=(
            (
                (0, 0),
                (
                    ("right_side", 0),
                    ("bottom_right_corner", 0),
                    ("bottom_side", 0),
                    ("bottom_left_corner", 0),
                    ("left_side", 0),
                    ("top_left_corner", 0),
                    ("top_side", 0),
                    ("top_right_corner", 0),
                ),
            ),
        ),
    )

    subprocess.run(
        [
            godot,
            "--headless",
            "--path",
            str(project_directory),
            "--editor",
            "--quit",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    result = subprocess.run(
        [
            godot,
            "--headless",
            "--path",
            str(project_directory),
            "--script",
            str(script_path.name),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        "Godot failed to validate the A4 terrains.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )
