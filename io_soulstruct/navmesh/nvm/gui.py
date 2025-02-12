from __future__ import annotations

__all__ = [
    "NVMNavmeshImportPanel",
    "NVMNavmeshExportPanel",
    "NVMNavmeshToolsPanel",
    "OBJECT_UL_nvm_event_entity_triangle",
    "NVMEventEntityPanel",
]

import typing as tp

import bmesh
import bpy

from soulstruct.base.events.enums import NavmeshFlag
from soulstruct.games import DEMONS_SOULS, DARK_SOULS_PTDE, DARK_SOULS_DSR

from io_soulstruct.exceptions import SoulstructTypeError
from io_soulstruct.general.gui import map_stem_box
from io_soulstruct.types import *

from .import_operators import *
from .export_operators import *
from .misc_operators import *
from .types import BlenderNVM


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
            self.layout.label(text="Game does not use NVM.")
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
            self.layout.label(text="Game does not use NVM.")
            return

        try:
            BlenderNVM.from_selected_objects(context)
        except SoulstructTypeError:
            self.layout.label(text="Select one or more navmesh (NVM) models.")
            return

        layout = self.layout
        map_stem_box(layout, settings)

        layout.prop(context.scene.soulstruct_settings, "detect_map_from_collection")
        map_stem = settings.get_active_object_detected_map(context)
        if not map_stem:
            layout.label(text="To Map: <NO MAP>")
        else:
            map_stem = settings.get_latest_map_stem_version(map_stem)
            layout.label(text=f"To Map: {map_stem}")
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

        self.layout.label(text="Navmesh Creation:")
        self.layout.operator(GenerateNavmeshFromCollision.bl_idname)

        self.layout.label(text="Misc. Navmesh:")
        self.layout.operator(RenameNavmesh.bl_idname)

        self.layout.label(text="Selected Face Indices:")
        selected_faces_box = self.layout.box()
        # noinspection PyTypeChecker
        obj = context.edit_object

        # Selected object can be a NVM model or an MSB Navmesh part referencing one. We modify the same Mesh data.
        if bpy.context.mode == "EDIT_MESH" and obj and (obj.soulstruct_type == SoulstructType.NAVMESH or (
            obj.soulstruct_type == SoulstructType.MSB_PART and obj.MSB_PART.part_subtype == "MSB_NAVMESH"
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
        row.prop(props, "navmesh_flag")
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


class OBJECT_UL_nvm_event_entity_triangle(bpy.types.UIList):
    """Draws a list of items."""
    PROP_NAME: tp.ClassVar[str] = "index"

    def draw_item(
        self,
        context,
        layout,
        data,
        item,
        icon,
        active_data,
        active_property,
        index=0,
        flt_flag=0,
    ):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.label(text=f"Triangle {index}:")
            row.prop(item, self.PROP_NAME, text="", emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text=f"Triangle {index}:")
            layout.prop(item, self.PROP_NAME, text="", emboss=False)


class NVMEventEntityPanel(bpy.types.Panel):
    """Draw a Panel in the Object properties window exposing NVM Event Entity properties for active object."""
    bl_label = "NVM Event Entity Settings"
    bl_idname = "OBJECT_PT_nvm_event_entity"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context) -> bool:
        return context.active_object and context.active_object.soulstruct_type == SoulstructType.NVM_EVENT_ENTITY

    def draw(self, context):
        layout = self.layout

        obj = context.active_object
        if obj is None:
            # Should already fail Panel poll.
            layout.label(text="No active NVM Event Entity.")
            return

        props = obj.NVM_EVENT_ENTITY
        layout.prop(props, "entity_id")

        layout.label(text="Triangles:")
        row = layout.row()
        row.template_list(
            listtype_name=OBJECT_UL_nvm_event_entity_triangle.__name__,
            list_id="",
            dataptr=props,
            propname="triangle_indices",
            active_dataptr=props,
            active_propname="triangle_index",
        )
        col = row.column(align=True)
        col.operator(AddNVMEventEntityTriangleIndex.bl_idname, icon='ADD', text="")
        col.operator(RemoveNVMEventEntityTriangleIndex.bl_idname, icon='REMOVE', text="")

        layout.prop(props, "triangle_indices")
