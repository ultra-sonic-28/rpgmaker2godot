import pytest

from rpgmaker2godot.tileset.flags import decode_tile_flags
from rpgmaker2godot.tileset.model import TileProperties

def test_decode_tile_flags_empty() -> None:
    properties = decode_tile_flags(0x0000)

    assert properties == TileProperties(
        can_pass_down=True,
        can_pass_left=True,
        can_pass_right=True,
        can_pass_up=True,
        is_star=False,
        is_ladder=False,
        is_bush=False,
        is_counter=False,
        is_damage_floor=False,
        terrain_tag=0,
    )


def test_decode_tile_flags_pass_down() -> None:
    properties = decode_tile_flags(0x0001)

    assert properties.can_pass_down is False
    assert properties.can_pass_left is True
    assert properties.can_pass_right is True
    assert properties.can_pass_up is True


def test_decode_tile_flags_ladder() -> None:
    properties = decode_tile_flags(0x0020)

    assert properties.is_ladder is True


def test_decode_tile_flags_bush() -> None:
    properties = decode_tile_flags(0x0040)

    assert properties.is_bush is True


def test_decode_tile_flags_counter() -> None:
    properties = decode_tile_flags(0x0080)

    assert properties.is_counter is True


def test_decode_tile_flags_damage_floor() -> None:
    properties = decode_tile_flags(0x0100)

    assert properties.is_damage_floor is True


def test_decode_tile_flags_terrain_tag() -> None:
    properties = decode_tile_flags(0x5000)

    assert properties.terrain_tag == 5


@pytest.mark.parametrize(
    ("tag",),
    (
        (0,),
        (1,),
        (5,),
        (15,),
    ),
)
def test_decode_tile_flags_all_terrain_tags(
    tag: int,
) -> None:
    flags = tag << 12

    properties = decode_tile_flags(flags)

    assert properties.terrain_tag == tag


def test_decode_tile_flags_combined() -> None:
    flags = (
        0x0001  # down blocked
        | 0x0008  # up blocked
        | 0x0020  # ladder
        | 0x0040  # bush
        | 0x0080  # counter
        | 0x0100  # damage floor
        | (7 << 12)  # terrain tag 7
    )

    properties = decode_tile_flags(flags)

    assert properties.can_pass_down is False
    assert properties.can_pass_left is True
    assert properties.can_pass_right is True
    assert properties.can_pass_up is False

    assert properties.is_star is False
    assert properties.is_ladder is True
    assert properties.is_bush is True
    assert properties.is_counter is True
    assert properties.is_damage_floor is True

    assert properties.terrain_tag == 7