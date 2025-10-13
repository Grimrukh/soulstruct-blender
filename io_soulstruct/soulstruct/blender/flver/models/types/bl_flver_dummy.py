from __future__ import annotations

__all__ = [
    "BlenderFLVERDummy",
]

import re
import typing as tp

import bpy
from mathutils import Matrix

from soulstruct.flver import *
from soulstruct.utilities.maths import Vector3

from soulstruct.blender.exceptions import *
from soulstruct.blender.types import *
from soulstruct.blender.utilities import *
from soulstruct.blender.flver.utilities import (
    BONE_CoB_4x4,
    game_forward_up_vectors_to_bl_euler,
    bl_rotmat_to_game_forward_up_vectors,
)

from ..properties import *


class BlenderFLVERDummy(BaseBlenderSoulstructObject[Dummy, FLVERDummyProps]):

    __slots__ = []

    TYPE = SoulstructType.FLVER_DUMMY
    BL_OBJ_TYPE = ObjectType.EMPTY

    # Captures anything else after the `[reference_id]` in name, including Blender dupe suffix like '.001'.
    DUMMY_NAME_RE: tp.ClassVar[re.Pattern] = re.compile(
        r"^(?P<model_name>.+)? *[Dd]ummy(?P<index><\d+>)? *(?P<reference_id>\[\d+\]) *(\.\d+)?$"
    )

    AUTO_DUMMY_PROPS: tp.ClassVar[list[str]] = [
        "color_rgba",
        "follows_attach_bone",
        "use_upward_vector",
        "unk_x30",
        "unk_x34"
    ]

    @property
    def parent_bone(self) -> bpy.types.Bone:
        """NOTE: Parent bone CANNOT be set as a Pointer property. We have to use a StringProperty name.

        This property uses the attached name to get the actual Bone object from the Armature, and raises a KeyError if
        that bone name is missing.
        """
        if not self.parent or self.parent.type != "ARMATURE":
            raise ValueError("Cannot get parent bone of Dummy without an Armature parent.")
        # noinspection PyTypeChecker
        armature = self.parent  # type: bpy.types.ArmatureObject
        try:
            return armature.data.bones[self.type_properties.parent_bone_name]
        except KeyError:
            raise KeyError(f"Parent bone '{self.type_properties.parent_bone_name}' of Dummy not found in Armature.")

    @parent_bone.setter
    def parent_bone(self, value: bpy.types.Bone | str):
        """Set Dummy's parent bone either with a direct Bone object, or name thereof.

        If a string name is given, that Bone name must exist in the parent Armature.
        """
        if not self.parent or self.parent.type != "ARMATURE":
            raise ValueError("Cannot set parent bone of Dummy without an Armature parent.")
        # noinspection PyTypeChecker
        armature = self.parent  # type: bpy.types.ArmatureObject
        if isinstance(value, bpy.types.Bone):
            self.type_properties.parent_bone_name = value.name
        elif isinstance(value, str):
            if value not in armature.data.bones:
                raise ValueError(f"Bone '{value}' not found in Armature of Dummy.")
            self.type_properties.parent_bone_name = value
        else:
            raise TypeError(f"Parent bone must be a Bone or string, not {type(value)}.")

    color_rgba: tuple[int, int, int, int]  # must be immutable to convey that `bl_dummy.color_rgba.r = X` has no effect
    follows_attach_bone: bool
    use_upward_vector: bool
    unk_x30: int
    unk_x34: int

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: Dummy,
        name: str,
        armature: bpy.types.ArmatureObject = None,
        collection: bpy.types.Collection = None,
    ) -> BlenderFLVERDummy:
        """Create a wrapped Blender Dummy empty object from FLVER `Dummy`.

        Created Dummy will be parented to `Armature` via its attach bone index, and will also record its internal parent
        bone (used to determine the space of its FLVER transform).
        """
        if armature is None:
            raise FLVERImportError("Cannot create Blender Dummy without an Armature object.")

        # noinspection PyTypeChecker
        bl_dummy = cls.new(name, data=None, collection=collection)  # type: BlenderFLVERDummy
        bl_dummy.parent = armature
        bl_dummy.obj.empty_display_type = "ARROWS"  # best display type/size I've found (single arrow not sufficient)
        bl_dummy.obj.empty_display_size = 0.05

        bl_dummy.color_rgba = (
            soulstruct_obj.color_rgba.r,
            soulstruct_obj.color_rgba.g,
            soulstruct_obj.color_rgba.b,
            soulstruct_obj.color_rgba.a,
        )
        bl_dummy.follows_attach_bone = soulstruct_obj.follows_attach_bone
        bl_dummy.use_upward_vector = soulstruct_obj.use_upward_vector
        bl_dummy.unk_x30 = soulstruct_obj.unk_x30
        bl_dummy.unk_x34 = soulstruct_obj.unk_x34

        if soulstruct_obj.use_upward_vector:
            bl_euler = game_forward_up_vectors_to_bl_euler(soulstruct_obj.forward, soulstruct_obj.upward)
        else:  # use default upward
            bl_euler = game_forward_up_vectors_to_bl_euler(soulstruct_obj.forward, Vector3((0, 1, 0)))

        bl_location = to_blender(soulstruct_obj.translate)
        # This initial transform may still be in 'parent bone' space.
        bl_dummy_transform = Matrix.LocRotScale(bl_location, bl_euler, (1, 1, 1))

        if soulstruct_obj.parent_bone_index != -1:
            # Bone's FLVER transform is in the space of (i.e. relative to) this parent bone.
            # NOTE: This is NOT the same as the 'attach' bone, which is used as the actual Blender parent and
            # controls how the dummy moves during armature animations. This Dummy 'parent bone' is more for grouping and
            # is generally a non-animated bone like 'Model_dmy' or 'Sfx'.
            bl_parent_bone = armature.data.bones[soulstruct_obj.parent_bone_index]
            bl_dummy.parent_bone = bl_parent_bone  # custom Soulstruct property
            bl_parent_bone_matrix = bl_parent_bone.matrix_local @ BONE_CoB_4x4  # undo bone CoB (self-inverse)
            bl_dummy_transform = bl_parent_bone_matrix @ bl_dummy_transform

        # Dummy moves with this bone during animations.
        if soulstruct_obj.attach_bone_index != -1:
            # Set true Blender parent. We manually compute the `matrix_local` of the Dummy to be relative to this bone.
            bl_attach_bone = armature.data.bones[soulstruct_obj.attach_bone_index]
            bl_attach_bone_matrix = bl_attach_bone.matrix_local @ BONE_CoB_4x4  # undo bone CoB (self-inverse)
            bl_dummy_transform = bl_attach_bone_matrix.inverted() @ bl_dummy_transform
            bl_dummy.obj.parent_bone = bl_attach_bone.name  # true Blender property (note *name*, not Bone itself)
            bl_dummy.obj.parent_type = "BONE"

        bl_dummy.obj.matrix_local = bl_dummy_transform

        return bl_dummy

    def _create_soulstruct_obj(self) -> Dummy:
        return Dummy(
            reference_id=self.reference_id,  # stored in dummy name for editing convenience
            color_rgba=ColorRGBA(*self.color_rgba),
            follows_attach_bone=self.follows_attach_bone,
            use_upward_vector=self.use_upward_vector,
            unk_x30=self.unk_x30,
            unk_x34=self.unk_x34,
        )

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        armature: bpy.types.ArmatureObject = None,
    ) -> Dummy:
        """Create a new `Dummy`."""
        if not armature:
            raise ValueError("Cannot convert Blender Dummy to FLVER Dummy without an Armature object.")

        dummy = self._create_soulstruct_obj()

        # Dummy transforms are slightly complicated to manage. Most Dummies are parented to a specific FLVER bone in
        # Blender (their 'attach bone'). However, Dummy transforms in FLVER files are given in the space of a DIFFERENT
        # bone (their 'parent bone', if given), which is generally a more 'categorical' bone like 'Model_dmy' or
        # 'Sfx' that is not used in animations. So to calculate the FLVER transform, we need to calculate:
        #     parent_bone_transform_inv @ attach_bone_transform @ dummy_local_transform
        # where each of the two bone transforms are just identity matrices if unused.

        # Start with Dummy local transform in Blender, which will be relative to its attach bone if set:
        bl_dummy_transform = self.obj.matrix_local

        if self.obj.parent_type == "BONE":  # NOTE: only possible for dummies parented to the Armature
            # Dummy has an 'attach bone' that is its Blender parent.
            try:
                attach_bone_index = armature.data.bones.find(self.obj.parent_bone)
            except ValueError:
                raise FLVERExportError(
                    f"Dummy '{self.name}' attach bone (Blender parent) '{self.obj.parent_bone}' "
                    f"not in Armature."
                )
            dummy.attach_bone_index = attach_bone_index
            # Use attach bone transform to convert Dummy transform to Armature space. We do this even if
            # `follows_attach_bone` is False, because this is resolving a genuine Blender parent-child relation.
            bl_attach_bone = armature.data.bones[attach_bone_index]
            bl_attach_bone_matrix = bl_attach_bone.matrix_local @ BONE_CoB_4x4  # undo bone CoB (self-inverse)
            bl_dummy_transform = bl_attach_bone_matrix @ bl_dummy_transform
        else:
            # Dummy has no attach bone.
            dummy.attach_bone_index = -1

        # NOTE: This 'Dummy parent bone' is NOT the bone it is parented to in Blender. That's the 'attach bone' above.
        parent_bone = self.parent_bone

        if parent_bone:
            # Dummy's Blender 'world' translate is actually given in the space of this bone in the FLVER file.
            try:
                parent_bone_index = armature.data.bones.find(parent_bone.name)
            except ValueError:
                raise FLVERExportError(f"Dummy '{self.name}' parent bone '{parent_bone.name}' not in Armature.")
            dummy.parent_bone_index = parent_bone_index
            # Make Dummy transform relative to parent bone transform:
            bl_parent_bone = armature.data.bones[parent_bone_index]
            bl_parent_bone_matrix = bl_parent_bone.matrix_local @ BONE_CoB_4x4  # undo bone CoB (self-inverse)
            bl_dummy_transform = bl_parent_bone_matrix.inverted() @ bl_dummy_transform
        else:
            # Dummy has no parent bone. Its FLVER transform will be in the model space.
            dummy.parent_bone_index = -1

        # Extract translation and rotation from final transform.
        dummy.translate = to_game(bl_dummy_transform.translation)
        forward, up = bl_rotmat_to_game_forward_up_vectors(bl_dummy_transform.to_3x3())
        dummy.forward = forward
        dummy.upward = up if dummy.use_upward_vector else Vector3.zero()

        return dummy

    def update_parent_bone_name(self, update_dict: dict[str, str]):
        """Update Dummy's parent bone name if it is in `update_dict`.

        Called at the same time as Armature bone names are updated, as the `parent_bone_name` property here will NOT
        update automatically.
        """
        if self.type_properties.parent_bone_name and self.type_properties.parent_bone_name in update_dict:
            self.type_properties.parent_bone_name = update_dict[self.type_properties.parent_bone_name]

    @property
    def name(self):
        return self.obj.name

    @name.setter
    def name(self, value):
        raise ValueError(
            "Cannot set name of Blender Dummy object directly. Use `model_name`, `index`, and `reference_id` "
            "properties, which will update the wrapped object name appropriately."
        )

    # region Dummy Name Components

    @staticmethod
    def format_name(
        model_name: str | None,
        index: int | None,
        reference_id: int,
        suffix: str | None
    ) -> str:
        if index is not None:
            name = f"Dummy<{index}> [{reference_id}]"
        else:
            name = f"Dummy [{reference_id}]"
        if model_name:
            name = f"{model_name} {name}"
        if suffix:
            name += f" {suffix}"
        return name

    @property
    def model_name(self) -> str:
        match = self.DUMMY_NAME_RE.match(self.name)
        if match is None:
            raise ValueError(f"FLVER Dummy object name does not match expected pattern: {self.name}")
        if match.group(1) is None:
            return ""  # no model name in name (lazy)
        return match.group(1).split()[0]

    @model_name.setter
    def model_name(self, value: str):
        match = self.DUMMY_NAME_RE.match(self.name)
        if match is None:
            raise ValueError(f"FLVER Dummy object name does not match expected pattern: {self.name}")
        self.obj.name = self.format_name(
            model_name=value,
            index=int(match.group(2)[1:-1]) if match.group(2) is not None else None,
            reference_id=int(match.group(3)[1:-1]),  # remove brackets
            suffix=match.group(4),
        )

    def set_index(self, index: int):
        match = self.DUMMY_NAME_RE.match(self.name)
        if match is None:
            raise ValueError(f"FLVER Dummy object name does not match expected pattern: {self.name}")
        self.obj.name = self.format_name(
            model_name=match.group(1),
            index=index,
            reference_id=int(match.group(3)[1:-1]),  # remove brackets
            suffix=match.group(4),
        )

    @property
    def reference_id(self) -> int:
        match = self.DUMMY_NAME_RE.match(self.name)
        if match is None:
            raise ValueError(f"FLVER Dummy object name does not match expected pattern: {self.name}")
        try:
            return int(match.group(3)[1:-1])  # remove brackets
        except ValueError:
            raise ValueError(f"FLVER Dummy object name does not match expected pattern: {self.name}")

    @reference_id.setter
    def reference_id(self, value: int):
        match = self.DUMMY_NAME_RE.match(self.name)
        if match is None:
            raise ValueError(f"FLVER Dummy object name does not match expected pattern: {self.name}")
        self.obj.name = self.format_name(
            model_name=match.group(1),
            index=int(match.group(2)[1:-1]) if match.group(2) else None,
            reference_id=value,
            suffix=match.group(4),
        )

    # endregion


add_auto_type_props(BlenderFLVERDummy, *BlenderFLVERDummy.AUTO_DUMMY_PROPS)
