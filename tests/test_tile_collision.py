import logging

import pytest

from rpgmaker2godot.model.tile_collision import TileCollision
from rpgmaker2godot.tileset.collision import (
    tile_properties_to_collision,
)
from rpgmaker2godot.tileset.model import TileProperties


def make_properties(
    *,
    can_pass_down: bool = True,
    can_pass_left: bool = True,
    can_pass_right: bool = True,
    can_pass_up: bool = True,
) -> TileProperties:
    """Build TileProperties with irrelevant fields disabled."""

    return TileProperties(
        can_pass_down=can_pass_down,
        can_pass_left=can_pass_left,
        can_pass_right=can_pass_right,
        can_pass_up=can_pass_up,
        is_star=False,
        is_ladder=False,
        is_bush=False,
        is_counter=False,
        is_damage_floor=False,
        terrain_tag=0,
    )


def test_tile_collision_is_immutable() -> None:
    collision = TileCollision(
        block_down=True,
        block_left=False,
        block_right=True,
        block_up=False,
    )

    with pytest.raises(
        AttributeError,
    ):
        collision.block_down = False  # type: ignore[misc]


def test_all_directions_passable() -> None:
    properties = make_properties()

    result = tile_properties_to_collision(properties)

    assert result == TileCollision(
        block_down=False,
        block_left=False,
        block_right=False,
        block_up=False,
    )


def test_all_directions_blocked() -> None:
    properties = make_properties(
        can_pass_down=False,
        can_pass_left=False,
        can_pass_right=False,
        can_pass_up=False,
    )

    result = tile_properties_to_collision(properties)

    assert result == TileCollision(
        block_down=True,
        block_left=True,
        block_right=True,
        block_up=True,
    )


@pytest.mark.parametrize(
    (
        "can_pass_down",
        "can_pass_left",
        "can_pass_right",
        "can_pass_up",
        "expected",
    ),
    (
        (
            False,
            True,
            True,
            True,
            TileCollision(
                block_down=True,
                block_left=False,
                block_right=False,
                block_up=False,
            ),
        ),
        (
            True,
            False,
            True,
            True,
            TileCollision(
                block_down=False,
                block_left=True,
                block_right=False,
                block_up=False,
            ),
        ),
        (
            True,
            True,
            False,
            True,
            TileCollision(
                block_down=False,
                block_left=False,
                block_right=True,
                block_up=False,
            ),
        ),
        (
            True,
            True,
            True,
            False,
            TileCollision(
                block_down=False,
                block_left=False,
                block_right=False,
                block_up=True,
            ),
        ),
    ),
)
def test_each_blocked_direction_is_inverted_correctly(
    can_pass_down: bool,
    can_pass_left: bool,
    can_pass_right: bool,
    can_pass_up: bool,
    expected: TileCollision,
) -> None:
    properties = make_properties(
        can_pass_down=can_pass_down,
        can_pass_left=can_pass_left,
        can_pass_right=can_pass_right,
        can_pass_up=can_pass_up,
    )

    result = tile_properties_to_collision(properties)

    assert result == expected


@pytest.mark.parametrize(
    "property_name",
    (
        "is_star",
        "is_ladder",
        "is_bush",
        "is_counter",
        "is_damage_floor",
    ),
)
def test_non_directional_properties_do_not_affect_collision(
    property_name: str,
) -> None:
    properties = make_properties()

    properties = TileProperties(
        can_pass_down=properties.can_pass_down,
        can_pass_left=properties.can_pass_left,
        can_pass_right=properties.can_pass_right,
        can_pass_up=properties.can_pass_up,
        is_star=(
            True if property_name == "is_star"
            else properties.is_star
        ),
        is_ladder=(
            True if property_name == "is_ladder"
            else properties.is_ladder
        ),
        is_bush=(
            True if property_name == "is_bush"
            else properties.is_bush
        ),
        is_counter=(
            True if property_name == "is_counter"
            else properties.is_counter
        ),
        is_damage_floor=(
            True if property_name == "is_damage_floor"
            else properties.is_damage_floor
        ),
        terrain_tag=7,
    )

    result = tile_properties_to_collision(properties)

    assert result == TileCollision(
        block_down=False,
        block_left=False,
        block_right=False,
        block_up=False,
    )


def test_logs_tile_id_and_coordinates_when_provided(caplog) -> None:
    collision_logger = "rpgmaker2godot.tileset.collision"

    properties = TileProperties(
        can_pass_down=False,
        can_pass_left=False,
        can_pass_right=False,
        can_pass_up=False,
        is_star=False,
        is_ladder=False,
        is_bush=False,
        is_counter=False,
        is_damage_floor=False,
        terrain_tag=0,
    )

    with caplog.at_level(logging.DEBUG, logger=collision_logger):
        tile_properties_to_collision(
            properties,
            tile_id=275,
            coord=(3, 11),
        )

    messages = [record.getMessage() for record in caplog.records]

    assert any(
        "tile_id=275 coord=(3, 11)" in message
        for message in messages
    )


def test_omits_identifiers_when_not_provided(caplog) -> None:
    collision_logger = "rpgmaker2godot.tileset.collision"

    properties = TileProperties(
        can_pass_down=False,
        can_pass_left=True,
        can_pass_right=True,
        can_pass_up=False,
        is_star=False,
        is_ladder=False,
        is_bush=False,
        is_counter=False,
        is_damage_floor=False,
        terrain_tag=0,
    )

    with caplog.at_level(logging.DEBUG, logger=collision_logger):
        tile_properties_to_collision(properties)

    messages = [record.getMessage() for record in caplog.records]

    assert any("properties -> collision: " in message for message in messages)
    assert not any("tile_id=" in message for message in messages)
    assert not any("coord=" in message for message in messages)