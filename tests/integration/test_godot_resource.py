from dataclasses import replace
import subprocess
from pathlib import Path

from PIL import Image
import pytest

from rpgmaker2godot.analysis.detector import TilesetDetector
from rpgmaker2godot.conversion.converter import SimpleConverter
from rpgmaker2godot.godot.export.simple import SimpleExporter
from tests.test_cli import create_sheet
from tests.helpers.godot_atlas import make_multi_cell_conversion
from tests.helpers.godot_integration import find_godot, write_project, write_validation_script


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
