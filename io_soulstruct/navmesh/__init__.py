from __future__ import annotations

__all__ = [
    "ImportNVM",
    "ImportNVMWithBinderChoice",
    "ImportSelectedMapNVM",

    "ExportLooseNVM",
    "ExportNVMIntoBinder",
    "ExportNVMIntoSelectedMap",

    "ImportNVMHKT",
    "ImportNVMHKTWithBinderChoice",
    "ImportNVMHKTFromNVMHKTBND",
    "ImportAllNVMHKTsFromNVMHKTBND",
    "ImportAllOverworldNVMHKTs",
    "ImportAllDLCOverworldNVMHKTs",
    "NVMHKTImportSettings",

    "NVMNavmeshImportPanel",
    "NVMNavmeshExportPanel",
    "NVMNavmeshToolsPanel",
    "NavmeshERImportPanel",

    "NavmeshFaceSettings",
    "AddNVMFaceFlags",
    "RemoveNVMFaceFlags",
    "SetNVMFaceObstacleCount",
    "ResetNVMFaceInfo",

    "NVMProps",
    "NVMEventEntityProps",
]

import bmesh
import bpy

from soulstruct.base.events.enums import NavmeshFlag
from soulstruct.games import DEMONS_SOULS, DARK_SOULS_PTDE, DARK_SOULS_DSR

from io_soulstruct.exceptions import SoulstructTypeError
from io_soulstruct.general.gui import map_stem_box
from io_soulstruct.types import *
from .nvm import *
from .nvm.utilities import set_face_material
from .nvmhkt import *


class NVMNavmeshImportPanel(bpy.types.Panel):
    bl_label = "NVM Navmesh Import"
    bl_idname = "NVM_PT_nvm_navmesh_import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Navmesh"
    bl_options = {"DEFAULT_CLOSED"}

    # noinspection PyUnusedLocal
    def draw(self, context):
        settings = context.scene.soulstruct_settings
        if not settings.is_game(DEMONS_SOULS, DARK_SOULS_PTDE, DARK_SOULS_DSR):
            self.layout.label(text="Unsupported game.")
            return

        layout = self.layout
        map_stem_box(layout, settings)
        if settings.map_stem:
            layout.label(text=f"From {settings.map_stem}:")
            layout.operator(ImportSelectedMapNVM.bl_idname)
        else:
            layout.label(text="No game map selected.")
        layout.operator(ImportNVM.bl_idname, text="Import Any NVM")


class NVMNavmeshExportPanel(bpy.types.Panel):
    bl_label = "NVM Navmesh Export"
    bl_idname = "NVM_PT_nvm_navmesh_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Navmesh"
    bl_options = {"DEFAULT_CLOSED"}

    # noinspection PyUnusedLocal
    def draw(self, context):
        settings = context.scene.soulstruct_settings
        if not settings.is_game(DEMONS_SOULS, DARK_SOULS_PTDE, DARK_SOULS_DSR):
            self.layout.label(text="Unsupported game.")
            return

        try:
            BlenderNVM.from_selected_objects(context)
        except SoulstructTypeError:
            self.layout.label(text="Select one or more navmesh (NVM) models.")
            return

        layout = self.layout
        map_stem_box(layout, settings)
        layout.label(text="Export to Game/Project:")
        layout.prop(context.scene.soulstruct_settings, "detect_map_from_collection")
        layout.operator(ExportNVMIntoSelectedMap.bl_idname)

        layout.label(text="Generic Export:")
        layout.operator(ExportLooseNVM.bl_idname)
        layout.operator(ExportNVMIntoBinder.bl_idname)


class NVMNavmeshToolsPanel(bpy.types.Panel):
    bl_label = "NVM Navmesh Tools"
    bl_idname = "NVM_PT_nvm_navmesh_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Navmesh"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        """Still shown if game is not DSR."""

        self.layout.label(text="Selected Face Indices:")
        selected_faces_box = self.layout.box()
        # noinspection PyTypeChecker
        obj = context.edit_object

        # Selected object can be a NVM model or an MSB Navmesh part referencing one. We modify the same Mesh data.
        if bpy.context.mode == "EDIT_MESH" and obj and (obj.soulstruct_type == SoulstructType.NAVMESH or (
            obj.soulstruct_type == SoulstructType.MSB_PART and obj.MSB_PART.part_subtype == "Navmesh"
        )):
            self.layout.operator(ResetNVMFaceInfo.bl_idname)
            obj: bpy.types.MeshObject
            bm = bmesh.from_edit_mesh(obj.data)
            try:
                layout_selected_faces(bm, self.layout, context, selected_faces_box)
            finally:
                bm.free()
                del bm
        else:
            selected_faces_box.label(text="Select navmesh faces in Edit Mode")


def layout_selected_faces(bm: bmesh.types.BMesh, layout, context, selected_faces_box):
    flags_layer = bm.faces.layers.int.get("nvm_face_flags")
    obstacle_count_layer = bm.faces.layers.int.get("nvm_face_obstacle_count")

    if flags_layer is None or obstacle_count_layer is None:
        # Prompt user to select some faces.
        selected_faces_box.label(text="Select navmesh faces in Edit Mode")
        return

    selected_faces = [f for f in bm.faces if f.select]
    for face in selected_faces:
        face_row = selected_faces_box.row()
        face_flags = face[flags_layer]
        face_obstacle_count = face[obstacle_count_layer]
        suffix = " | ".join([n.name for n in NavmeshFlag if n.value & face_flags])
        if suffix:
            suffix = f" ({suffix})"
        if face_obstacle_count > 0:
            suffix += f" <{face_obstacle_count} obstacles>"
        # Show selected face index, flag type names, and obstacle count.
        face_row.label(text=f"{face.index}{suffix}")

    if selected_faces:
        # Call refresh operator to tag redraw.
        # refresh_row = selected_faces_box.row()
        # refresh_row.operator(RefreshFaceIndices.bl_idname)

        # Draw operators to add/remove a chosen flag type to/from all selected faces.
        props = context.scene.navmesh_face_settings
        flag_box = layout.box()
        row = flag_box.row()
        row.prop(props, "flag_type")
        row = flag_box.row()
        row.operator(AddNVMFaceFlags.bl_idname, text="Add Flag")
        row.operator(RemoveNVMFaceFlags.bl_idname, text="Remove Flag")

        # Box and button to set obstacle count for selected faces.
        obstacle_box = layout.box()
        row = obstacle_box.row()
        row.prop(props, "obstacle_count")
        row = obstacle_box.row()
        row.operator(SetNVMFaceObstacleCount.bl_idname, text="Set Obstacle Count")

    else:
        # Prompt user to select some faces.
        selected_faces_box.label(text="Select navmesh faces in Edit Mode")

    del bm


class NavmeshERImportPanel(bpy.types.Panel):
    bl_label = "ER Navmesh Import"
    bl_idname = "NVM_PT_er_navmesh_import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Navmesh"
    bl_options = {"DEFAULT_CLOSED"}

    # noinspection PyUnusedLocal
    def draw(self, context):
        settings = context.scene.soulstruct_settings
        if settings.game_variable_name != "ELDEN_RING":
            self.layout.label(text="Elden Ring only.")
            return

        import_loose_box = self.layout.box()
        import_loose_box.operator(ImportNVMHKT.bl_idname)

        settings_box = self.layout.box()
        settings_box.label(text="Import Settings")
        settings_box.prop(context.scene.nvmhkt_import_settings, "import_hires_navmeshes")
        settings_box.prop(context.scene.nvmhkt_import_settings, "import_lores_navmeshes")
        settings_box.prop(context.scene.nvmhkt_import_settings, "correct_model_versions")
        settings_box.prop(context.scene.nvmhkt_import_settings, "create_dungeon_connection_points")
        settings_box.prop(context.scene.nvmhkt_import_settings, "overworld_transform_mode")
        settings_box.prop(context.scene.nvmhkt_import_settings, "dungeon_transform_mode")

        quick_box = self.layout.box()
        quick_box.label(text="From Game/Project")
        quick_box.prop(context.scene.soulstruct_settings, "import_bak_file", text="From .BAK File")
        quick_box.operator(ImportNVMHKTFromNVMHKTBND.bl_idname)
        quick_box.operator(ImportAllNVMHKTsFromNVMHKTBND.bl_idname)
        quick_box.operator(ImportAllOverworldNVMHKTs.bl_idname)
        quick_box.operator(ImportAllDLCOverworldNVMHKTs.bl_idname)
