from __future__ import annotations

__all__ = [
    "AddDebugNodeGroupToMaterials",
    "RemoveDebugNodeGroupFromMaterials",
]

import bpy
from soulstruct.blender.msb.properties.parts import BlenderMSBPartSubtype
from soulstruct.blender.utilities.bpy_types import SoulstructType
from soulstruct.blender.utilities.operators import LoggingOperator

from .nodes import *


def _get_scene_msb_geometry_objects(context: bpy.types.Context) -> list[bpy.types.MeshObject]:
    """Get all objects in the scene that an MSB Part geometry subtype."""
    objs = []
    for obj in context.scene.objects:
        if obj.soulstruct_type == SoulstructType.MSB_PART:
            if obj.MSB_PART.entry_subtype_enum in {
                BlenderMSBPartSubtype.MapPiece,
                BlenderMSBPartSubtype.Collision,
                BlenderMSBPartSubtype.Navmesh,
            }:
                objs.append(obj)
    return objs


class AddDebugNodeGroupToMaterials(LoggingOperator):
    bl_idname = "soulstruct.add_debug_nodes_materials"
    bl_label = "Add Material Debug Nodes"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        # TODO: I don't think I need to do this here.
        # for obj in iter(bpy.data.objects):
        #     if hasattr(obj, "map_progress"):
        #         obj.map_progress.sync_pass_index(obj)

        ensure_debug_node_group(context)

        # Collect all MSB geometry materials.
        mats = set()
        for obj in _get_scene_msb_geometry_objects(context):
            for slot in obj.material_slots:
                if slot.material:
                    mats.add(slot.material)

        self.info(f"Adding debug nodes into {len(mats)} unique material(s) from MSB geometry objects.")

        applied = 0
        for mat in mats:
            if add_debug_group_to_material(context, mat):
                applied += 1

        # Make sure enabled state propagates.
        sync_material_debug_nodes(context)

        return {"FINISHED"}


class RemoveDebugNodeGroupFromMaterials(LoggingOperator):
    bl_idname = "soulstruct.remove_debug_node_group"
    bl_label = "Remove Material Debug Nodes"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        mats = set()
        for obj in _get_scene_msb_geometry_objects(context):
            for slot in (obj.material_slots or []):
                if slot.material:
                    mats.add(slot.material)

        removed = 0
        for mat in mats:
            if remove_debug_group_from_material(mat):
                removed += 1

        self.info(f"Removed debug node group from {removed} material(s).")
        return {"FINISHED"}
