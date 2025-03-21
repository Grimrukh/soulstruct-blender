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

from soulstruct.games import *

from io_soulstruct.bpy_base.property_group import SoulstructPropertyGroup
from .events import BlenderMSBEventSubtype
from .parts import MSBPartArmatureMode


class MSBImportSettings(SoulstructPropertyGroup):
    """Common MSB import settings. Drawn manually in operator browser windows."""

    GAME_PROP_NAMES = {
        DEMONS_SOULS: (
            "import_map_piece_models",
            "import_collision_models",
            "import_navmesh_models",
            "import_object_models",
            "import_character_models",
            "part_armature_mode",
            "model_name_filter",
            "model_name_filter_match_mode",
        ),
        DARK_SOULS_PTDE: (
            "import_map_piece_models",
            "import_collision_models",
            "import_navmesh_models",
            "import_object_models",
            "import_character_models",
            "part_armature_mode",
            "model_name_filter",
            "model_name_filter_match_mode",
        ),
    }

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

    part_armature_mode: bpy.props.EnumProperty(
        name="Part Armature Mode",
        description="How to handle armatures for MSB Parts that use FLVER models",
        items=[
            (MSBPartArmatureMode.NEVER, "Never", "Never create armatures for FLVER MSB Parts"),
            (
                MSBPartArmatureMode.CUSTOM_ONLY,
                "Custom Only",
                "Only create armatures for FLVER MSB Parts for FLVER models that use Custom bone data",
            ),
            (
                MSBPartArmatureMode.IF_PRESENT,
                "If Present",
                "Create armatures for FLVER MSB Parts for FLVER models that have an armature",
            ),
            (MSBPartArmatureMode.ALWAYS, "Always", "Always create armatures for FLVER MSB Parts"),
        ],
        default=MSBPartArmatureMode.CUSTOM_ONLY,
    )

    model_name_filter: bpy.props.StringProperty(
        name="Model Name Import Filter",
        description="Glob/Regex for filtering which MSB Models should be loaded (if their type is "
                    "ALSO enabled for import above), rather than using placeholder meshes",
        default="*",
    )

    model_name_filter_match_mode: bpy.props.EnumProperty(
        name="Model Name Filter Match Mode",
        description="Whether 'Model Name Filter' is a Glob or Regex pattern",
        items=[
            ("GLOB", "Glob", "Use glob (*, ?, etc.) for MSB Part name matching"),
            ("REGEX", "Regex", "Use Python regular expressions for MSB Part name matching"),
        ],
        default="GLOB",
    )

    def import_any_models(self) -> bool:
        """Returns True if any of the MSB model import settings are enabled."""
        return any(getattr(
            self, f"import_{part}_models") for part in ["map_piece", "collision", "navmesh", "object", "character"]
        )

    def import_any_flver_models(self) -> bool:
        """Returns True if any of the FLVER model import settings are enabled."""
        return (
            self.import_map_piece_models
            or self.import_character_models
            or self.import_object_models
        )

    def get_model_name_match_filter(self) -> tp.Callable[[str], bool]:
        match self.model_name_filter_match_mode:
            case "GLOB":
                def is_name_match(name: str):
                    return self.model_name_filter in {"", "*"} or fnmatch(name, self.model_name_filter)
            case "REGEX":
                pattern = re.compile(self.model_name_filter)

                def is_name_match(name: str):
                    return self.model_name_filter == "" or re.match(pattern, name)
            case _:  # should never happen
                raise ValueError(f"Invalid MSB Model name match mode: {self.model_name_filter}")
        return is_name_match


class MSBExportSettings(SoulstructPropertyGroup):

    GAME_PROP_NAMES = {
        DEMONS_SOULS: (
            "use_world_transforms",
            "export_collision_models",
            "export_navmesh_models",
            # No NVMDUMP file.
            "export_soulstruct_jsons",
            "skip_connect_collisions",
            "skip_render_hidden",
        ),
        DARK_SOULS_PTDE: (
            "use_world_transforms",
            "export_collision_models",
            "export_navmesh_models",
            "export_nvmdump",
            "export_soulstruct_jsons",
            "skip_connect_collisions",
            "skip_render_hidden",
        ),
    }

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

    skip_connect_collisions: bpy.props.BoolProperty(
        name="Skip Connect Collisions",
        description="Do not export MSB Connect Collision parts. Useful for debugging map loading problems",
        default=False,
    )

    skip_render_hidden: bpy.props.BoolProperty(
        name="Skip Render Hidden",
        description="Do not export MSB parts that are hidden from rendering (camera icon in in hierarchy)",
        default=False,
    )


class MSBToolSettings(SoulstructPropertyGroup):

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
            (BlenderMSBEventSubtype.Light, "Light", "MSB Light Events"),
            (BlenderMSBEventSubtype.Sound, "Sound", "MSB Sound Events"),
            (BlenderMSBEventSubtype.VFX, "VFX", "MSB VFX Events"),
            (BlenderMSBEventSubtype.Wind, "Wind", "MSB Wind Events"),
            (BlenderMSBEventSubtype.Treasure, "Treasure", "MSB Treasure Events"),
            (BlenderMSBEventSubtype.Spawner, "Spawner", "MSB Spawner Events"),
            (BlenderMSBEventSubtype.Message, "Message", "MSB Message Events"),
            (BlenderMSBEventSubtype.ObjAct, "ObjAct", "MSB ObjAct (Object Action) Events"),
            (BlenderMSBEventSubtype.SpawnPoint, "Spawn Point", "MSB Spawn Point Events"),
            (BlenderMSBEventSubtype.MapOffset, "Map Offset", "MSB Map Offset Events"),
            (BlenderMSBEventSubtype.Navigation, "Navigation", "MSB Navigation Events"),
            (BlenderMSBEventSubtype.Environment, "Environment", "MSB Environment Events"),
            (BlenderMSBEventSubtype.NPCInvasion, "NPC Invasion", "MSB NPC Invasion Events"),
        ],
        default="ALL",
    )

    event_color_active_collection_only: bpy.props.BoolProperty(
        name="Active Collection Only",
        description="Only color MSB Events in the active collection or a child of it",
        default=True,
    )
