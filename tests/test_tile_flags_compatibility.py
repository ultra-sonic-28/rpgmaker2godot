import pytest

from rpgmaker2godot.tileset.flags import (
    decode_tile_flags,
)


@pytest.mark.parametrize(
    ("raw_flags", "direction", "expected_can_pass"),
    [
        (0x0000, "down", True),
        (0x0001, "down", False),

        (0x0000, "left", True),
        (0x0002, "left", False),

        (0x0000, "right", True),
        (0x0004, "right", False),

        (0x0000, "up", True),
        (0x0008, "up", False),
    ],
)
def test_passability_matches_rpgmaker_flag_semantics(
    raw_flags: int,
    direction: str,
    expected_can_pass: bool,
) -> None:
    properties = decode_tile_flags(raw_flags)

    assert getattr(
        properties,
        f"can_pass_{direction}",
    ) is expected_can_pass


@pytest.mark.parametrize(
    ("raw_flags", "attribute"),
    [
        (0x0010, "is_star"),
        (0x0020, "is_ladder"),
        (0x0040, "is_bush"),
        (0x0080, "is_counter"),
        (0x0100, "is_damage_floor"),
    ],
)
def test_rpgmaker_boolean_flags_are_exposed_correctly(
    raw_flags: int,
    attribute: str,
) -> None:
    properties = decode_tile_flags(raw_flags)

    assert getattr(properties, attribute) is True


@pytest.mark.parametrize(
    "terrain_tag",
    range(16),
)
def test_terrain_tag_matches_rpgmaker_exposed_value(
    terrain_tag: int,
) -> None:
    raw_flags = terrain_tag << 12

    properties = decode_tile_flags(raw_flags)

    assert properties.terrain_tag == terrain_tag


def rpgmaker_terrain_tag(raw_flags: int) -> int:
    """Reference implementation of RPG Maker's terrain-tag exposure."""

    return (raw_flags >> 12) & 0x0F


@pytest.mark.parametrize(
    "raw_flags",
    [
        0x0000,
        0x0001,
        0x0010,
        0x0020,
        0x0100,
        0x0800,
        0x1234,
        0xFFFF,
    ],
)
def test_terrain_tag_is_compatible_with_rpgmaker(
    raw_flags: int,
) -> None:
    properties = decode_tile_flags(raw_flags)

    assert properties.terrain_tag == (
        (raw_flags >> 12) & 0x0F
    )