from pathlib import Path

from tests.helpers.godot_integration import write_validation_script


FULL_TILE_POINTS = (
    0.0, 0.0, 48.0, 0.0, 48.0, 48.0, 0.0, 48.0,
)


def test_writes_collision_polygon_checks(tmp_path: Path) -> None:
    script_path = write_validation_script(
        tmp_path,
        validate_all_cells=False,
        expected_collision_polygons=(
            ((0, 0), FULL_TILE_POINTS),
        ),
        expected_collision_free_cells=((1, 0),),
    )

    content = script_path.read_text(encoding="utf-8")

    assert "get_physics_layers_count()" in content
    assert "get_collision_polygons_count(0)" in content
    assert "get_collision_polygon_points(0, 0)" in content
    # Incremental construction: no composite literal parsing.
    assert (
        "var expected_points_0_0 := PackedVector2Array()"
        in content
    )
    assert (
        "expected_points_0_0.append(Vector2(0.0, 0.0))"
        in content
    )
    assert (
        "expected_points_0_0.append(Vector2(48.0, 48.0))"
        in content
    )
    # Size guard gives a precise diagnosis on mismatch.
    assert (
        ".size() != expected_points_0_0.size()"
        in content
    )
    assert (
        "validate_collision_free(atlas_source, Vector2i(1, 0))"
        in content
    )


def test_omits_collision_checks_when_not_expected(
    tmp_path: Path,
) -> None:
    script_path = write_validation_script(
        tmp_path,
        validate_all_cells=False,
    )

    content = script_path.read_text(encoding="utf-8")

    assert "var expected_polygons" not in content
    assert ".append(Vector2(" not in content
    assert (
        "validate_collision_free(atlas_source"
        not in content
    )