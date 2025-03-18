"""Panel collection of various operators that haven't found a better home yet."""
from __future__ import annotations

__all__ = [
    "MiscSoulstructMeshOperatorsPanel",
    "MiscSoulstructCollectionOperatorsPanel",
    "MiscSoulstructOtherOperatorsPanel",
]

import bpy

from io_soulstruct.general.gui import map_stem_box

from .misc_mesh import *
from .misc_other import *
from .misc_outliner import *


class MiscSoulstructMeshOperatorsPanel(bpy.types.Panel):

    bl_label = "Mesh Operators"
    bl_idname = "SCENE_PT_misc_soulstruct_mesh"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Misc. Soulstruct"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        layout.label(text="Mesh Tools:")
        layout.operator(CopyMeshSelectionOperator.bl_idname)
        layout.operator(CutMeshSelectionOperator.bl_idname)
        layout.operator(BooleanMeshCut.bl_idname)
        layout.operator(ApplyLocalMatrixToMesh.bl_idname)
        layout.operator(ScaleMeshIslands.bl_idname)
        layout.operator(SelectActiveMeshVerticesNearSelected.bl_idname)
        layout.operator(ConvexHullOnEachMeshIsland.bl_idname)
        layout.operator(SetActiveFaceNormalUpward.bl_idname)
        layout.operator(SpawnObjectIntoMeshAtFaces.bl_idname)
        layout.operator(WeightVerticesWithFalloff.bl_idname)
        layout.operator(ApplyModifierNonSingleUser.bl_idname)


class MiscSoulstructCollectionOperatorsPanel(bpy.types.Panel):

    bl_label = "Collection Operators"
    bl_idname = "SCENE_PT_misc_soulstruct_collection"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Misc. Soulstruct"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        map_stem_box(layout, context.scene.soulstruct_settings)

        layout.prop(context.scene.misc_outliner_settings, "collection_mode")

        layout.separator()
        layout.label(text="Model Collection Visibility:")

        row = layout.row()
        row.label(text="All Models")
        row.operator(ShowAllModels.bl_idname, text="", icon="HIDE_OFF").show = True
        row.operator(ShowAllModels.bl_idname, text="", icon="HIDE_ON").show = False

        row = layout.row()
        row.label(text="Game Models")
        row.operator(ShowAllGameModels.bl_idname, text="", icon="HIDE_OFF").show = True
        row.operator(ShowAllGameModels.bl_idname, text="", icon="HIDE_ON").show = False

        for op in (ShowAllObjectModels, ShowAllCharacterModels):
            row = layout.row()
            row.label(text="  " + op.LABEL)
            row.operator(op.bl_idname, text="", icon="HIDE_OFF").show = True
            row.operator(op.bl_idname, text="", icon="HIDE_ON").show = False

        row = layout.row()
        row.label(text="Map Models")
        row.operator(ShowAllMapModels.bl_idname, text="", icon="HIDE_OFF").show = True
        row.operator(ShowAllMapModels.bl_idname, text="", icon="HIDE_ON").show = False

        for op in (ShowAllMapPieceModels, ShowAllCollisionModels, ShowAllNavmeshModels):
            row = layout.row()
            row.label(text="  " + op.LABEL)
            row.operator(op.bl_idname, text="", icon="HIDE_OFF").show = True
            row.operator(op.bl_idname, text="", icon="HIDE_ON").show = False

        layout.separator()
        layout.label(text="MSB Collection Visibility:")
        row = layout.row()
        row.label(text="Full MSB")
        row.operator(ShowAllMSB.bl_idname, text="", icon="HIDE_OFF").show = True
        row.operator(ShowAllMSB.bl_idname, text="", icon="HIDE_ON").show = False
        for op in (
            ShowAllMSBMapPieceParts,
            ShowAllMSBCollisionParts,
            ShowAllMSBNavmeshParts,
            ShowAllMSBConnectCollisionParts,
            ShowAllMSBObjectParts,
            ShowAllMSBCharacterParts,
            ShowAllMSBPlayerStartParts,
            ShowAllMSBRegionsEvents,
        ):
            row = layout.row()
            row.label(text="  " + op.LABEL)
            row.operator(op.bl_idname, text="", icon="HIDE_OFF").show = True
            row.operator(op.bl_idname, text="", icon="HIDE_ON").show = False


class MiscSoulstructOtherOperatorsPanel(bpy.types.Panel):

    bl_label = "Other Operators"
    bl_idname = "SCENE_PT_misc_soulstruct_other"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Misc. Soulstruct"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        layout.operator(PrintGameTransform.bl_idname)
