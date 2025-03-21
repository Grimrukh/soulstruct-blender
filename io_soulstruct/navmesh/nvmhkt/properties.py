"""Settings for NVMHKT import operators."""
__all__ = ["NVMHKTImportSettings"]

import bpy

from soulstruct.games import ELDEN_RING

from io_soulstruct.bpy_base.property_group import SoulstructPropertyGroup


class NVMHKTImportSettings(SoulstructPropertyGroup):
    """Determines which NVMHKT navmeshes are collected by 'all'-style importers."""

    GAME_PROP_NAMES = {
        # TODO: I think Bloodborne and onward use NVMHKT.
        ELDEN_RING: (),  # all properties are supported
    }

    import_hires_navmeshes: bpy.props.BoolProperty(
        name="Import Hi-Res Navs (n*/q*)",
        description="Import hi-res 'n*' navmeshes from NVMHKTBNDs (prefers 'q*' navmeshes if present and not empty)",
        default=True,
    )

    import_lores_navmeshes: bpy.props.BoolProperty(
        name="Import Lo-Res Navs (o*)",
        description="Import low-res 'o*' navmeshes from NVMHKTBNDs",
        default=False,
    )

    correct_model_versions: bpy.props.BoolProperty(
        name="Correct Model Versions",
        description="In V1+ map versions, the navmesh model names still end in 00, which may conflict with V0 versions "
                    "you have loaded. Enable this to change the model name endings to match the map version. Make sure "
                    "you enable the corresponding export option to change it back to 00",
        default=True,
    )

    create_dungeon_connection_points: bpy.props.BoolProperty(
        name="Create Dungeon Connection Points",
        description="When importing a dungeon navmesh connected directly to one or more overworld tiles, create an "
                    "Empty object at the connection points (recorded from vanilla Elden Ring GameParam)",
        default=True,
    )

    overworld_transform_mode: bpy.props.EnumProperty(
        name="Overworld Transform Mode",
        description="How to transform overworld navmeshes (m60/m61) on import",
        items=[
            ("NONE", "None", "Do not move overworld navmeshes"),
            ("WORLD", "World", "Transform overworld navmeshes to world coordinates by adding tile translations"),
        ],
        default="WORLD",
    )

    dungeon_transform_mode: bpy.props.EnumProperty(
        name="Dungeon Transform Mode",
        description="How to transform dungeon navmeshes (non-m60/m61) to their tile or world coordinates",
        items=[
            ("NONE", "None", "Do not move dungeon navmeshes"),
            ("TILE", "Overworld Tile", "Transform dungeon navmeshes to their connected overworld tile's local space"),
            ("WORLD", "World", "Transform dungeon navmeshes to world coordinates by adding tile and grid translations"),
        ],
        default="WORLD",
    )
