import json

import pytest

from rpgmaker2godot.tileset.reader import (
    TilesetsJsonReader,
)


def test_reads_tileset_flags(tmp_path) -> None:
    path = tmp_path / "Tilesets.json"

    path.write_text(
        json.dumps(
            [
                None,
                {
                    "id": 1,
                    "name": "Inside",
                    "flags": [
                        0,
                        1,
                        0x20,
                        0xF000,
                    ],
                },
            ]
        ),
        encoding="utf-8",
    )

    result = TilesetsJsonReader().read_flags(path)

    print(result)
    assert len(result) == 2

    assert result[0].id == 0
    assert result[0].name == ""
    assert result[0].flags == ()

    assert result[1].id == 1
    assert result[1].name == "Inside"
    assert result[1].flags == (
        0,
        1,
        0x20,
        0xF000,
    )


def test_rejects_invalid_json(tmp_path) -> None:
    path = tmp_path / "Tilesets.json"
    path.write_text("{invalid", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid Tilesets.json"):
        TilesetsJsonReader().read_flags(path)


def test_rejects_non_array_root(tmp_path) -> None:
    path = tmp_path / "Tilesets.json"
    path.write_text("{}", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="Tilesets.json root must be a JSON array",
    ):
        TilesetsJsonReader().read_flags(path)


def test_rejects_invalid_flag(tmp_path) -> None:
    path = tmp_path / "Tilesets.json"

    path.write_text(
        json.dumps(
            [
                {
                    "id": 1,
                    "name": "Inside",
                    "flags": [0, "invalid"],
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Invalid flag",
    ):
        TilesetsJsonReader().read_flags(path)


def test_rejects_flag_larger_than_16_bits(tmp_path) -> None:
    path = tmp_path / "Tilesets.json"

    path.write_text(
        json.dumps(
            [
                {
                    "id": 1,
                    "name": "Inside",
                    "flags": [0x10000],
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Invalid flag",
    ):
        TilesetsJsonReader().read_flags(path)