from __future__ import annotations

__all__ = [
    "MSBImportSettings",
    "MSBExportSettings",
    "MSBToolSettings",
]

import re
import typing as tp
from fnmatch import fnmatch

import bpy
from .events import MSBEventSubtype


class MSBImportSettings(bpy.types.PropertyGroup):
    """Common MSB import settings. Drawn manually in operator browser windows."""

    import_map_piece_models: bpy.props.BoolProperty(
        name="Import Map Piece Models",
        description="Import models for MSB Map Piece parts, rather than using placeholder meshes",
        default=True,
    )
    import_collision_models: bpy.props.BoolProperty(
        name="Import Collision Models",
        description="Import models for MSB Collision/Connect Collision parts, rather than using placeholder meshes",
        default=True,
    )
    import_navmesh_models: bpy.props.BoolProperty(
        name="Import Navmesh Models",
        description="Import models for MSB Navmesh parts, rather than using placeholder meshes",
        default=True,
    )
    import_object_models: bpy.props.BoolProperty(
        name="Import Object Models",
        description="Import models for MSB Object/Asset parts, rather than using placeholder meshes",
        default=True,
    )
    import_character_models: bpy.props.BoolProperty(
        name="Import Character Models",
        description="Import models for MSB Character and MSB Player Start parts, rather than using placeholder meshes",
        default=True,
    )

    part_name_model_filter: bpy.props.StringProperty(
        name="Part Name Model Import Filter",
        description="Glob/Regex for filtering which MSB Parts should have their models loaded (if their type is "
                    "also enabled for import above), rather than using placeholder meshes",
        default="*",
    )

    part_name_filter_match_mode: bpy.props.EnumProperty(
        name="Part Name Filter Match Mode",
        description="Whether to use glob or regex for MSB Part name matching for model import",
        items=[
            ("GLOB", "Glob", "Use glob (*, ?, etc.) for MSB Part name matching"),
            ("REGEX", "Regex", "Use Python regular expressions for MSB Part name matching"),
        ],
        default="GLOB",
    )

    def get_name_match_filter(self) -> tp.Callable[[str], bool]:
        match self.part_name_filter_match_mode:
            case "GLOB":
                def is_name_match(name: str):
                    return self.part_name_model_filter in {"", "*"} or fnmatch(name, self.part_name_model_filter)
            case "REGEX":
                pattern = re.compile(self.part_name_model_filter)

                def is_name_match(name: str):
                    return self.part_name_model_filter == "" or re.match(pattern, name)
            case _:  # should never happen
                raise ValueError(f"Invalid MSB Part name match mode: {self.part_name_filter_match_mode}")
        return is_name_match

    hide_model_collections: bpy.props.BoolProperty(
        name="Hide Model Collections",
        description="Hide any new Model collections (in viewport) created for the first time on MSB import",
        default=True,
    )

    hide_dummy_entries: bpy.props.BoolProperty(
        name="Hide Dummy Characters/Objects",
        description="Hide dummy MSB Characters, Objects, and Assets (disabled, cutscene only, etc.) in the viewport",
        default=True,
    )


class MSBExportSettings(bpy.types.PropertyGroup):

    use_world_transforms: bpy.props.BoolProperty(
        name="Use World Transforms",
        description="Use world transforms when exporting MSB entries, rather than local transforms. Recommended so "
                    "that you can use Blender parenting to place groups of MSB entries and still see exactly what you "
                    "see in Blender in-game",
        default=True,
    )

    export_collision_models: bpy.props.BoolProperty(
        name="Export Collision Models",
        description="Export models for MSB Collision parts to new hi/lo-res HKXBHD Binders in map. Convenient way to "
                    "ensure that collision models are synchronized with the MSB (Collision HKX export is quite fast)",
        default=False,
    )

    export_navmesh_models: bpy.props.BoolProperty(
        name="Export Navmesh Models",
        description="Export models for MSB Navmesh parts to a new NVMBND Binder in map. Convenient way to ensure that "
                    "navmesh models are synchronized with the MSB (NVM export is quite fast)",
        default=False,
    )

    export_nvmdump: bpy.props.BoolProperty(
        name="Export NVMDUMP",
        description="Export NVMDUMP text file to map",
        default=True,
    )

    export_soulstruct_jsons: bpy.props.BoolProperty(
        name="Export Soulstruct JSONs",
        description="Export MSB JSON files to 'maps' directory in Soulstruct GUI Project Directory, if given",
        default=False,
    )


class MSBToolSettings(bpy.types.PropertyGroup):

    event_color: bpy.props.FloatVectorProperty(
        name="Event Color",
        description="Color for setting MSB Event objects in the viewport",
        subtype="COLOR",
        size=4,
        default=(0.0, 0.0, 0.0, 1.0),
    )

    event_color_type: bpy.props.EnumProperty(
        name="Event Subtype to Color",
        items=[
            ("ALL", "All", "Color all MSB Events"),
            (MSBEventSubtype.Light, "Light", "MSB Light Events"),
            (MSBEventSubtype.Sound, "Sound", "MSB Sound Events"),
            (MSBEventSubtype.VFX, "VFX", "MSB VFX Events"),
            (MSBEventSubtype.Wind, "Wind", "MSB Wind Events"),
            (MSBEventSubtype.Treasure, "Treasure", "MSB Treasure Events"),
            (MSBEventSubtype.Spawner, "Spawner", "MSB Spawner Events"),
            (MSBEventSubtype.Message, "Message", "MSB Message Events"),
            (MSBEventSubtype.ObjAct, "ObjAct", "MSB ObjAct (Object Action) Events"),
            (MSBEventSubtype.SpawnPoint, "Spawn Point", "MSB Spawn Point Events"),
            (MSBEventSubtype.MapOffset, "Map Offset", "MSB Map Offset Events"),
            (MSBEventSubtype.Navigation, "Navigation", "MSB Navigation Events"),
            (MSBEventSubtype.Environment, "Environment", "MSB Environment Events"),
            (MSBEventSubtype.NPCInvasion, "NPC Invasion", "MSB NPC Invasion Events"),
        ],
        default="ALL",
    )

    event_color_active_collection_only: bpy.props.BoolProperty(
        name="Active Collection Only",
        description="Only color MSB Events in the active collection or a child of it",
        default=True,
    )
