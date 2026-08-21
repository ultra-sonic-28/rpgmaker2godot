from dataclasses import dataclass


@dataclass(frozen=True)
class TilesetFlags:
    """Raw RPG Maker flags belonging to one tileset.

    `flags[tile_id]` is the raw 16-bit flag value stored by
    RPG Maker in Tilesets.json.
    """

    id: int
    name: str
    flags: tuple[int, ...]

    def get(self, tile_id: int) -> int:
        """Return the raw flag value for a global Tile ID."""

        if tile_id < 0:
            raise ValueError(
                f"Tile ID must be >= 0, got {tile_id}."
            )

        if tile_id >= len(self.flags):
            raise IndexError(
                f"Tile ID {tile_id} is outside flags array "
                f"(length={len(self.flags)})."
            )

        return self.flags[tile_id]


@dataclass(frozen=True)
class TileProperties:
    """Decoded RPG Maker properties for a single tile.

    RPG Maker stores the properties of a tile in a 16-bit flag.
    This class exposes the individual semantic properties instead
    of forcing the rest of the application to manipulate bit masks.
    | Bits     | Signification           |
    | -------- | ----------------------- |
    | `0x0001` | passage bas             |
    | `0x0002` | passage gauche          |
    | `0x0004` | passage droite          |
    | `0x0008` | passage haut            |
    | `0x0010` | `*` / priorité spéciale |
    | `0x0020` | ladder                  |
    | `0x0040` | bush                    |
    | `0x0080` | counter                 |
    | `0x0100` | damage floor            |
    | `0x0F00` | terrain tag             |
    """

    can_pass_down: bool
    can_pass_left: bool
    can_pass_right: bool
    can_pass_up: bool

    is_star: bool
    is_ladder: bool
    is_bush: bool
    is_counter: bool
    is_damage_floor: bool

    terrain_tag: int