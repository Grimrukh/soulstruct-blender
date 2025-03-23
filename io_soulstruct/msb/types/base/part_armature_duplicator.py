from __future__ import annotations

__all__ = [
    "PartArmatureDuplicator",
]

import typing as tp

import bpy
from mathutils import Matrix

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
    ) -> bool:
        """Check `armature_mode` (and presence of `model`) and duplicate model Armature to Part accordingly."""
        if not model:
            # I don't think we need to log a warning here, as the missing Model will already be reported.
            return False

        if model.soulstruct_type == SoulstructType.MSB_MODEL_PLACEHOLDER:
            # Ignore these Parts (no FLVER imported).
            return False

        if model.soulstruct_type != SoulstructType.FLVER:
            operator.warning(
                f"MSB Part '{bl_part.name}' does not have a FLVER model to duplicate Armature from. (This non-FLVER "
                f"Part class should not have a `PartArmatureDuplicator` instance!)"
            )
            return False  # definitely do not duplicate

        # Check if we should duplicate.
        if armature_mode == MSBPartArmatureMode.NEVER:
            return False  # harmless case

        bl_flver = BlenderFLVER(model)

        if armature_mode != MSBPartArmatureMode.ALWAYS and not bl_flver.armature:
            # No Armature to duplicate (i.e. FLVER has an implicit default Armature) and we won't create it.
            return False

        if armature_mode == MSBPartArmatureMode.CUSTOM_ONLY and bl_flver.bone_data_type != FLVERBoneDataType.CUSTOM:
            # FLVER bones aren't written to custom data (implying a static pose), so we don't duplicate.
            return False

        # We definitely duplicate at this stage, creating the default Armature if needed.
        # TODO: To animate Parts "in place" in the MSB, need their root motion to ADD to Armature's transform.
        #  Easiest solution here is to give the Part Armature a "<ROOT>" bone to write root motion to.
        #  Harmless because we never export the Part Armature... except for the mythical Cutscene Export.
        cls._duplicate_flver_model_armature(context, bl_part, bl_flver)
        return True

    @staticmethod
    def _duplicate_flver_model_armature(
        context: bpy.types.Context,
        bl_part: BaseBlenderMSBPart,
        bl_flver: BlenderFLVER,
    ) -> None:

        # Prepare to move the Mesh's local transform to the new Armature.
        matrix_local = bl_part.obj.matrix_local.copy()
        bl_part.obj.matrix_local = Matrix.Identity(4)

        if not bl_flver.armature:
            # This FLVER model doesn't have an Armature, implying the FLVER has only one default bone. We create it
            # explicitly for the Part (already determined by caller). Armature name (object and data) are handled.
            # TODO: This doesn't create an Armature Modifier, but there are no vertex groups anyway. Pretty useless?
            armature_obj = BlenderFLVER.create_default_armature_parent(context, bl_part.game_name, bl_part.obj)
        else:
            # Duplicate model's Armature. This handles parenting, rigging, etc. We always copy the current Pose
            # (remember that the true FLVER static pose data is stored in custom `EditBone` properties).
            armature_obj = bl_flver.duplicate_armature(context, bl_part.obj)
            # Rename duplicated Armature and new modifier (name always set to 'FLVER Armature' initially).
            armature_obj.name = armature_obj.data.name = f"{bl_part.game_name} Armature"

            # Create a new Bone called '<PART_ROOT>' and parent all other root bones to it.
            # This is to allow for root motion in the future.
            # TODO: This is super slow and we don't need it for Cutscenes. Find a better way to animate Parts.
            # PartArmatureDuplicator._create_part_root_bone(context, armature_obj)

            bl_part.obj.modifiers["FLVER Armature"].name = "Part Armature"

        # Finish moving local transform to new Armature.
        armature_obj.matrix_local = matrix_local

    @staticmethod
    def _create_part_root_bone(context: bpy.types.Context, armature_obj: bpy.types.ArmatureObject) -> None:
        context.view_layer.objects.active = armature_obj
        bpy.ops.object.mode_set(mode="EDIT")
        root_bone = armature_obj.data.edit_bones.new("<PART_ROOT>")
        base_edit_bone_length = context.scene.flver_import_settings.base_edit_bone_length
        root_bone.tail = (0, base_edit_bone_length, 0)
        root_bone.use_connect = False
        root_bone.use_local_location = True
        root_bone.inherit_scale = "NONE"
        for bone in armature_obj.data.edit_bones:
            if not bone.parent:
                bone.parent = root_bone
        bpy.ops.object.mode_set(mode="OBJECT")
