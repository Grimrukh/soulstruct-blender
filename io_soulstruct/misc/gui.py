"""Panel collection of various operators that haven't found a better home yet."""
from __future__ import annotations

__all__ = [
    "MiscSoulstructOperatorsPanel",
]

import bpy

from .misc_mesh import *
from .misc_other import *
from .misc_outliner import *


class MiscSoulstructOperatorsPanel(bpy.types.Panel):

    bl_label = "Misc. Soulstruct"
    bl_idname = "SCENE_PT_misc_soulstruct"
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

        layout.label(text="Model Collection Visibility:")
        layout.operator(ShowAllMapPieceModels.bl_idname, text="Map Piece Models")
        layout.operator(ShowAllCollisionModels.bl_idname, text="Collision Models")
        layout.operator(ShowAllNavmeshModels.bl_idname, text="Navmesh Models")
        layout.label(text="MSB Collection Visibility:")
        layout.operator(ShowAllMSBMapPieceParts.bl_idname, text="MSB Map Pieces")
        layout.operator(ShowAllMSBCollisionParts.bl_idname, text="MSB Collisions")
        layout.operator(ShowAllMSBNavmeshParts.bl_idname, text="MSB Navmeshes")
        layout.operator(ShowAllMSBConnectCollisionParts.bl_idname, text="MSB Connect Collisions")
        layout.operator(ShowAllMSBObjectParts.bl_idname, text="MSB Objects")
        layout.operator(ShowAllMSBCharacterParts.bl_idname, text="MSB Characters")
        layout.operator(ShowAllMSBPlayerStartParts.bl_idname, text="MSB Player Starts")
        layout.operator(ShowAllMSBRegionsEvents.bl_idname, text="MSB Regions/Events")

        layout.label(text="Other Tools:")
        layout.operator(PrintGameTransform.bl_idname)
