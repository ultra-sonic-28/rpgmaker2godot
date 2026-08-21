import json
from pathlib import Path

from .model import TilesetFlags


class TilesetsJsonReader:
    """Read RPG Maker's Tilesets.json file.

    The reader preserves the structure and ordering of RPG Maker's
    tileset array.

    Each JSON entry becomes one :class:`TilesetFlags` instance. The
    index in the JSON array is used as the tileset ID because RPG Maker
    uses the array position as the global tileset identifier.

    A ``null`` entry is represented by an empty ``TilesetFlags`` object.
    This preserves the positional relationship between the JSON array
    and the resulting tuple.
    """

    def read_flags(
        self,
        path: Path,
    ) -> tuple[TilesetFlags, ...]:
        """Read and validate the raw flags of all RPG Maker tilesets.

        The returned tuple preserves the order of ``Tilesets.json``:

        ``result[n]`` corresponds to the tileset entry at JSON index ``n``.

        The flags themselves remain raw RPG Maker 16-bit values. Their
        interpretation is deliberately left to ``TilePropertiesResolver``.
        """

        if not path.is_file():
            raise FileNotFoundError(
                f"Tilesets.json not found: {path}"
            )

        try:
            data = json.loads(
                path.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid Tilesets.json: {path}"
            ) from exc

        if not isinstance(data, list):
            raise ValueError(
                "Tilesets.json root must be a JSON array."
            )

        result: list[TilesetFlags] = []

        for index, tileset in enumerate(data):
            # RPG Maker may contain null entries in Tilesets.json.
            # Keep the entry so that the index-to-ID relationship is
            # never shifted.
            if tileset is None:
                result.append(
                    TilesetFlags(
                        id=index,
                        name="",
                        flags=(),
                    )
                )
                continue

            if not isinstance(tileset, dict):
                raise ValueError(
                    f"Tileset at index {index} must be an object."
                )

            tileset_id = tileset.get("id")

            if tileset_id is None:
                # The array index is the authoritative identifier for
                # our positional representation, but an explicit RPG
                # Maker ID is still expected when the entry exists.
                tileset_id = index

            if not isinstance(tileset_id, int):
                raise ValueError(
                    f"Invalid tileset id at index {index}: "
                    f"{tileset_id!r}"
                )

            if tileset_id < 0:
                raise ValueError(
                    f"Invalid tileset id at index {index}: "
                    f"{tileset_id}"
                )

            name = tileset.get("name", "")

            if not isinstance(name, str):
                raise ValueError(
                    f"Invalid tileset name at index {index}: "
                    f"{name!r}"
                )

            flags = tileset.get("flags")

            if flags is None:
                raise ValueError(
                    f"Tileset at index {index} has no 'flags' field."
                )

            if not isinstance(flags, list):
                raise ValueError(
                    f"Tileset at index {index} has invalid "
                    "'flags' field."
                )

            decoded_flags: list[int] = []

            for flag_index, value in enumerate(flags):
                if not isinstance(value, int):
                    raise ValueError(
                        f"Invalid flag at tileset {index}, "
                        f"index {flag_index}: {value!r}"
                    )

                if not 0 <= value <= 0xFFFF:
                    raise ValueError(
                        f"Invalid flag at tileset {index}, "
                        f"index {flag_index}: {value}"
                    )

                decoded_flags.append(value)

            result.append(
                TilesetFlags(
                    id=tileset_id,
                    name=name,
                    flags=tuple(decoded_flags),
                )
            )

        return tuple(result)