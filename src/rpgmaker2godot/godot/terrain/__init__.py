"""Godot terrain generation from the unfolded A4 autotiles."""

from .terrain_builder import GodotTerrainBuilder
from .terrain_builder import GodotTerrainBuilder as TerrainBuilder

__all__ = [
    "GodotTerrainBuilder",
    "TerrainBuilder",
]