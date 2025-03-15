from __future__ import annotations

__all__ = [
    "PartArmatureDuplicator",
]

import typing as tp

import bpy

from io_soulstruct.flver.models.types import BlenderFLVER, FLVERBoneDataType
from io_soulstruct.msb.properties import MSBPartArmatureMode
from io_soulstruct.utilities import *

if tp.TYPE_CHECKING:
    from .parts import BaseBlenderMSBPart


class PartArmatureDuplicator:
    """Stateless utility used by FLVER-based MSB Parts to duplicate the model's Armature to the Part object.

    Armatures are optional for Parts and do not affect MSB export at all. They are only helpful for:
        a) properly visually a static pose of a Map Piece or Object,
        b) seeing dynamic animations in-place in MSB layouts,
     or c) animating individual characters, objects, etc. in Cutscenes.

    When we create a Part Armature, we always duplicate the current pose of the model Armature.
    """

    @classmethod
    def maybe_duplicate_flver_model_armature(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        armature_mode: MSBPartArmatureMode,
        bl_part: BaseBlenderMSBPart,
        model: bpy.types.MeshObject,
    ):
        """Check `armature_mode` (and presence of `model`) and duplicate model Armature to Part accordingly."""
        if model.soulstruct_type != SoulstructType.FLVER:
            operator.warning(
                f"MSB Part '{bl_part.name}' does not have a FLVER model to duplicate Armature from. (This non-FLVER "
                f"Part class should not have a `PartArmatureDuplicator` instance!)"
            )
            return  # definitely do not duplicate

        # Check if we should duplicate.
        if armature_mode == MSBPartArmatureMode.NEVER:
            return  # harmless case
        if not model:
            # I don't think we need to log a warning here, as the missing Model will already be reported.
            return

        bl_flver = BlenderFLVER(model)

        if armature_mode != MSBPartArmatureMode.ALWAYS and not bl_flver.armature:
            # No Armature to duplicate (i.e. FLVER has an implicit default Armature) and we won't create it.
            return

        if armature_mode == MSBPartArmatureMode.CUSTOM_ONLY and bl_flver.bone_data_type != FLVERBoneDataType.CUSTOM:
            # FLVER bones aren't written to custom data (implying a static pose), so we don't duplicate.
            return

        # We definitely duplicate at this stage, creating the default Armature if needed.
        cls._duplicate_flver_model_armature(context, bl_part, bl_flver)

    @staticmethod
    def _duplicate_flver_model_armature(
        context: bpy.types.Context,
        bl_part: BaseBlenderMSBPart,
        bl_flver: BlenderFLVER,
    ) -> None:

        bl_transform = BlenderTransform.from_bl_obj(bl_part.obj)
        bl_part.clear_bl_obj_transform()

        if not bl_flver.armature:
            # This FLVER model doesn't have an Armature, implying the FLVER has only one default bone. We create it
            # explicitly for the Part (already determined by caller). Armature name (object and data) are handled.
            # TODO: This doesn't create an Armature Modifier, but there are no vertex groups anyway. Pretty useless?
            armature_obj = BlenderFLVER.create_default_armature_parent(context, bl_part.game_name, bl_part.obj)
        else:
            # Duplicate model's Armature. This handles parenting, rigging, etc. We always copy the current Pose
            # (remember that the true FLVER static pose data is stored in custom `EditBone` properties).
            armature_obj = bl_flver.duplicate_armature(context, bl_part.obj, copy_pose=True)
            # Rename duplicated Armature and new modifier (name always set to 'FLVER Armature' initially).
            armature_obj.name = armature_obj.data.name = f"{bl_part.game_name} Armature"
            bl_part.obj.modifiers["FLVER Armature"].name = "Part Armature"

        # Set now-cleared Mesh object transform to new Armature parent of Part.
        armature_obj.location = bl_transform.bl_translate
        armature_obj.rotation_euler = bl_transform.bl_rotate
        armature_obj.scale = bl_transform.bl_scale
