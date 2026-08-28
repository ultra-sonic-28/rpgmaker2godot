import pytest

from rpgmaker2godot.model import (
    SheetType,
    Tile,
)
from rpgmaker2godot.tileset.model import (
    TileProperties,
    TilesetFlags,
)
from rpgmaker2godot.tileset.resolver import (
    TilePropertiesResolver,
)
from tests.helpers.atlas import make_tile_ref


def make_tile(
    *,
    column: int,
    row: int,
    sheet_type: SheetType = SheetType.B,
) -> Tile:
    return Tile(
        ref=make_tile_ref(
            index=0,
            sheet_type=sheet_type,
        ),
        column=column,
        row=row,
        x=column * 48,
        y=row * 48,
        width=48,
        height=48,
    )


def test_resolves_tile_properties() -> None:
    tile = make_tile(
        column=3,
        row=2,
    )

    tile_id = 2 * 16 + 3

    flags = [0] * (tile_id + 1)

    flags[tile_id] = (
        0x0001  # blocked down
        | 0x0004  # blocked right
        | 0x0020  # ladder
        | 0x0080  # counter
        | 0xF000  # terrain tag 15
    )

    tileset = TilesetFlags(
        id=1,
        name="Inside",
        flags=tuple(flags),
    )

    resolver = TilePropertiesResolver(
        {"Inside": tileset}
    )

    properties = resolver.resolve(tile)

    assert properties == TileProperties(
        can_pass_down=False,
        can_pass_left=True,
        can_pass_right=False,
        can_pass_up=True,
        is_star=False,
        is_ladder=True,
        is_bush=False,
        is_counter=True,
        is_damage_floor=False,
        terrain_tag=15,
    )


def test_rejects_unknown_tileset() -> None:
    tile = make_tile(
        column=0,
        row=0,
    )

    resolver = TilePropertiesResolver({})

    with pytest.raises(
        ValueError,
        match="Unknown RPG Maker tileset",
    ):
        resolver.resolve(tile)


def test_rejects_tile_id_outside_flags() -> None:
    tile = make_tile(
        column=0,
        row=10,
    )

    tileset = TilesetFlags(
        id=1,
        name="Inside",
        flags=(0,),
    )

    resolver = TilePropertiesResolver(
        {"Inside": tileset}
    )

    with pytest.raises(IndexError):
        resolver.resolve(tile)


def test_resolve_logs_tile_coordinates(
    caplog,
) -> None:
    import logging

    tile = make_tile(
        column=5,
        row=7,
    )

    tile_id = 7 * 16 + 5

    tileset = TilesetFlags(
        id=1,
        name="Inside",
        flags=(0,) * (tile_id + 1),
    )

    resolver = TilePropertiesResolver({"Inside": tileset})

    resolver_logger = "rpgmaker2godot.tileset.resolver"

    with caplog.at_level(logging.DEBUG, logger=resolver_logger):
        properties = resolver.resolve(tile)

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

    messages = [record.getMessage() for record in caplog.records]

    assert any(
        f"resolve Inside tile_id={tile_id} coord=(5, 7) raw_flags=0x0000"
        in message
        for message in messages
    )