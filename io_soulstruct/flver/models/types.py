from __future__ import annotations

__all__ = [
    "BlenderFLVER",
    "BlenderFLVERDummy",
]

import math
import re
import time
import typing as tp
from enum import StrEnum
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

from soulstruct.base.models.flver import *
from soulstruct.base.models.shaders import MatDef, MatDefError
from soulstruct.containers.tpf import TPFTexture
from soulstruct.games import DEMONS_SOULS
from soulstruct.utilities.maths import Vector3, Matrix3
from soulstruct.utilities.text import natural_keys

from io_soulstruct.exceptions import *
from io_soulstruct.flver.material.types import BlenderFLVERMaterial
from io_soulstruct.general.enums import BlenderImageFormat
from io_soulstruct.flver.image.import_operators import *
from io_soulstruct.flver.image.image_import_manager import ImageImportManager
from io_soulstruct.flver.image.types import DDSTexture, DDSTextureCollection
from io_soulstruct.general import GAME_CONFIG
from io_soulstruct.general.cached import get_cached_mtdbnd, get_cached_matbinbnd
from io_soulstruct.types import *
from io_soulstruct.utilities import *
from .properties import *

if tp.TYPE_CHECKING:
    from soulstruct.base.models.matbin import MATBINBND
    from io_soulstruct.general import SoulstructSettings


class BlenderFLVERDummy(SoulstructObject[Dummy, FLVERDummyProps]):

    __slots__ = []

    TYPE = SoulstructType.FLVER_DUMMY
    OBJ_DATA_TYPE = SoulstructDataType.EMPTY

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
    def parent_bone(self):
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

    color_rgba: tuple[int, int, int, int]
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

        bl_dummy.color_rgba = soulstruct_obj.color_rgba
        bl_dummy.follows_attach_bone = soulstruct_obj.follows_attach_bone
        bl_dummy.use_upward_vector = soulstruct_obj.use_upward_vector
        bl_dummy.unk_x30 = soulstruct_obj.unk_x30
        bl_dummy.unk_x34 = soulstruct_obj.unk_x34
        
        if soulstruct_obj.use_upward_vector:
            bl_euler = GAME_FORWARD_UP_VECTORS_TO_BL_EULER(soulstruct_obj.forward, soulstruct_obj.upward)
        else:  # use default upward
            bl_euler = GAME_FORWARD_UP_VECTORS_TO_BL_EULER(soulstruct_obj.forward, Vector3((0, 1, 0)))

        bl_location = GAME_TO_BL_VECTOR(soulstruct_obj.translate)
        # This initial transform may still be in 'parent bone' space.
        bl_dummy_transform = Matrix.LocRotScale(bl_location, bl_euler, (1, 1, 1))

        if soulstruct_obj.parent_bone_index != -1:
            # Bone's FLVER transform is in the space of (i.e. relative to) this parent bone.
            # NOTE: This is NOT the same as the 'attach' bone, which is used as the actual Blender parent and
            # controls how the dummy moves during armature animations. This Dummy 'parent bone' is more for grouping and
            # is generally a non-animated bone like 'Model_dmy' or 'Sfx'.
            bl_parent_bone = armature.data.bones[soulstruct_obj.parent_bone_index]
            bl_dummy.parent_bone = bl_parent_bone
            bl_parent_bone_matrix = bl_parent_bone.matrix_local
            bl_dummy_transform = bl_parent_bone_matrix @ bl_dummy_transform

        # Dummy moves with this bone during animations.
        if soulstruct_obj.attach_bone_index != -1:
            # Set true Blender parent. We manually compute the `matrix_local` of the Dummy to be relative to this bone.
            bl_attach_bone = armature.data.bones[soulstruct_obj.attach_bone_index]
            bl_dummy_transform = bl_attach_bone.matrix_local.inverted() @ bl_dummy_transform
            bl_dummy.obj.parent_bone = bl_attach_bone.name  # note NAME, not Bone itself
            bl_dummy.obj.parent_type = "BONE"

        bl_dummy.obj.matrix_local = bl_dummy_transform
        
        return bl_dummy

    def _create_soulstruct_obj(self) -> Dummy:
        return Dummy(
            reference_id=self.reference_id,  # stored in dummy name for editing convenience
            color_rgba=list(self.color_rgba),
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
            bl_dummy_transform = bl_attach_bone.matrix_local @ bl_dummy_transform
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
            bl_dummy_transform = bl_parent_bone.matrix_local.inverted() @ bl_dummy_transform
        else:
            # Dummy has no parent bone. Its FLVER transform will be in the model space.
            dummy.parent_bone_index = -1

        # Extract translation and rotation from final transform.
        dummy.translate = BL_TO_GAME_VECTOR3(bl_dummy_transform.translation)
        forward, up = BL_ROTMAT_TO_GAME_FORWARD_UP_VECTORS(bl_dummy_transform.to_3x3())
        dummy.forward = forward
        dummy.upward = up if dummy.use_upward_vector else Vector3.zero()

        return dummy

    @property
    def name(self):
        return self.obj.name

    @name.setter
    def name(self, value):
        raise ValueError(
            "Cannot set name of Blender Dummy object directly. Use `model_name`, `index`, and `reference_id` "
            "properties."
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
        self.name = self.format_name(
            model_name=value,
            index=int(match.group(2)[1:-1]) if match.group(2) is not None else None,
            reference_id=int(match.group(3)[1:-1]),  # remove brackets
            suffix=match.group(4),
        )

    def set_index(self, index: int):
        match = self.DUMMY_NAME_RE.match(self.name)
        if match is None:
            raise ValueError(f"FLVER Dummy object name does not match expected pattern: {self.name}")
        self.name = self.format_name(
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
        self.name = self.format_name(
            model_name=match.group(1),
            index=int(match.group(2)[1:-1]) if match.group(2) else None,
            reference_id=value,
            suffix=match.group(4),
        )

    # endregion


BlenderFLVERDummy.add_auto_type_props(*BlenderFLVERDummy.AUTO_DUMMY_PROPS)


class BlenderFLVER(SoulstructObject[FLVER, FLVERProps]):
    """Wrapper for a Blender object hierarchy that represents a `FLVER` or `FLVER0` model.

    Exposes convenience methods that access and/or modify different FLVER attributes.

    Components:
        - Armature Object: Contains all bones, which each have `flver_bone` properties.
            - Mesh Object: Contains mesh data and `flver` properties (header/format properties).
                - Materials: Contain shader data and each have `flver_material` properties.
                - Vertex Groups: Contains bone weights.
                - UV Maps: Contains UV data.
                - Vertex Colors: Contains vertex color data.
            - Dummy Objects: Empties with `flver_dummy` properties.

    Alternatively, the Mesh object can be the root object (and parent of Dummies, though these are rare for unrigged
    FLVERs), which implies that the FLVER Armature should be just a single bone (named for the model) at the origin.
    This is standard for Map Pieces, except older ones that (annoyingly) use other bones as simple transform parents for
    certain sets of vertices.

    The root object, whether Armature or Mesh, should be named for the model (unless it is an MSB Part instance). The
    `name` property here handles this automatically. If the Armature is the root object, the Mesh child is named
    '{model} Mesh'.
    """
    class BoneDataType(StrEnum):
        """Bone types used when reading FLVER data."""
        NONE = ""
        EDIT = "EditBone"
        POSE = "PoseBone"

    TYPE = SoulstructType.FLVER
    OBJ_DATA_TYPE = SoulstructDataType.MESH
    EXPORT_TIGHT_NAME = True

    __slots__ = []
    obj: bpy.types.MeshObject  # type override
    data: bpy.types.Mesh  # type override

    AUTO_FLVER_PROPS: tp.ClassVar[str] = [
        "big_endian",
        "version",
        "unicode",
        "f2_unk_x4a",
        "f2_unk_x4c",
        "f2_unk_x5c",
        "f2_unk_x5d",
        "f2_unk_x68",
        "f0_unk_x4a",
        "f0_unk_x4b",
        "f0_unk_x4c",
        "f0_unk_x5c",
    ]

    big_endian: bool
    version: str  # `Version` enum name
    unicode: bool

    # `FLVER` unknowns:
    f2_unk_x4a: bool
    f2_unk_x4c: int
    f2_unk_x5c: int
    f2_unk_x5d: int
    f2_unk_x68: int

    # `FLVER0` unknowns:
    f0_unk_x4a: int
    f0_unk_x4b: int
    f0_unk_x4c: int
    f0_unk_x5c: int

    @property
    def mesh_vertices_merged(self) -> bool:
        return self.type_properties.mesh_vertices_merged

    @mesh_vertices_merged.setter
    def mesh_vertices_merged(self, value: bool):
        self.type_properties.mesh_vertices_merged = value

    @property
    def bone_data_type(self) -> BoneDataType:
        return self.BoneDataType(self.type_properties.bone_data_type)

    @bone_data_type.setter
    def bone_data_type(self, value: BoneDataType):
        self.type_properties.bone_data_type = self.BoneDataType(value)

    @property
    def armature(self) -> bpy.types.ArmatureObject | None:
        """Detect parent Armature of wrapped Mesh object."""
        if self.obj.parent and self.obj.parent.type == "ARMATURE":
            # noinspection PyTypeChecker
            return self.obj.parent
        return None

    @classmethod
    def from_armature_or_mesh(cls, obj: bpy.types.Object) -> BlenderFLVER:
        if not obj:
            raise SoulstructTypeError("No Object given.")
        _, mesh = cls.parse_flver_obj(obj)
        return cls(mesh)

    @property
    def mesh(self) -> bpy.types.MeshObject:
        """Alias for `obj` that makes the type clear."""
        return self.obj

    @property
    def name(self):
        return self.obj.name

    @name.setter
    def name(self, new_name: str):
        """Calls full `deep_rename()` on all dummies, materials, bones, etc."""
        self.deep_rename(new_name)

    def get_dummies(self, operator: LoggingOperator | None = None) -> list[BlenderFLVERDummy]:
        """Find all FLVER Dummy (empty children of root object with expected name).

        If `operator` is provided, warnings will be logged for any Empty children that do not match the expected name
        pattern.
        """
        if not self.armature:
            return []

        dummies = []
        for child in self.armature.children:
            if child.type != "EMPTY":
                continue
            if BlenderFLVERDummy.DUMMY_NAME_RE.match(child.name):
                dummies.append(BlenderFLVERDummy(child))
            elif operator:
                operator.warning(f"Ignoring FLVER Empty child with non-Dummy name: '{child.name}'")
        return sorted(dummies, key=lambda d: natural_keys(d.name))

    def get_materials(self) -> list[BlenderFLVERMaterial]:
        """Get all Mesh materials as `BlenderFLVERMaterial` objects."""
        return [BlenderFLVERMaterial(mat) for mat in self.mesh.data.materials]

    # region Utility Methods

    def deep_rename(self, new_name: str, old_name=""):
        """Rename all components of given FLVER object (Armature, Mesh, materials, bones, dummies):

        The FLVER model name appears in numerous places in different ways throughout the object hierarchy. By default,
        names are processed by this method as though they conform to standard imported templates:

        - If Armature exists, it is named `new_name` and Mesh child is named `{new_name} Mesh`.
            - Otherwise, root Mesh is named `new_name`.
        - Each Dummy has its `model_name` name component replaced with `new_name`.
        - Each Material and Bone has a full `str.replace()` of current model `name` with `new_name`.
            - If only a single default origin bone exists, its name is set to `new_name` directly.

        The data-blocks of Armature (if present) and Mesh are ONLY renamed if they CURRENTLY match the name of the
        Armature/Mesh object itself, which indicates that they are true models and not just MSB Part instances.

        You can pass `old_name` to do the renaming as though its current name was `old_name`.

        Blender's duplicate suffix, e.g. '.001', is stripped prior to the renaming of all components.
        """

        old_name = old_name or self.export_name

        if self.armature:
            self.armature.name = f"{new_name} Armature"
            self.armature.data.name = f"{new_name} Armature"
        self.mesh.name = new_name
        self.mesh.data.name = new_name

        for mat in self.mesh.data.materials:
            # Replace all string occurrences.
            old_mat_name = remove_dupe_suffix(mat.name)
            mat.name = old_mat_name.replace(old_name, new_name)

        if self.armature:
            bone_renaming = {}
            for bone in self.armature.data.bones:
                # Replace all string occurrences.
                old_bone_name = remove_dupe_suffix(bone.name)
                bone.name = bone_renaming[bone.name] = old_bone_name.replace(old_name, new_name)
            # Vertex group names need to be updated manually, unlike when you edit bone names in the GUI.
            for vertex_group in self.mesh.vertex_groups:
                if vertex_group.name in bone_renaming:
                    vertex_group.name = bone_renaming[vertex_group.name]
            for dummy in self.get_dummies():
                dummy.model_name = new_name
                # Dummy `parent_bone` pointer will take care of itself, if set.

    def select_mesh(self, deselect_all=True):
        if deselect_all:
            bpy.ops.object.select_all(action="DESELECT")
        self.mesh.select_set(True)
        bpy.context.view_layer.objects.active = self.mesh

    def select_armature(self, deselect_all=True):
        if not self.armature:
            raise FLVERError("No Armature found for FLVER model.")
        if deselect_all:
            bpy.ops.object.select_all(action="DESELECT")
        self.armature.select_set(True)
        bpy.context.view_layer.objects.active = self.armature

    def duplicate_armature(
        self,
        context: bpy.types.Context,
        child_mesh_obj: bpy.types.MeshObject,
        copy_pose=False,
    ) -> bpy.types.ArmatureObject:
        """Duplicate just the `armature` of this FLVER model. Mostly used internally during full duplication.

        If `child_mesh_obj` is given (e.g. one just created/duplicated), it is parented to the new Armature and rigged
        with an Armature modifier.

        Also duplicates all dummy children.

        Does not rename anything.
        """
        if not self.armature:
            # TODO: Could copy 'implicit Armature' by creating a single-bone Armature with the same name as the model.
            raise FLVERError("No Armature to duplicate for FLVER model.")

        new_armature_obj = new_armature_object(self.armature.name, data=self.armature.data.copy())
        for collection in child_mesh_obj.users_collection:
            collection.objects.link(new_armature_obj)
        # No properties taken from Armature.
        context.view_layer.objects.active = new_armature_obj

        if copy_pose:
            # Copy pose bone transforms.
            context.view_layer.update()  # need Blender to create `linked_armature_obj.pose` now
            for new_pose_bone in new_armature_obj.pose.bones:
                source_bone = self.armature.pose.bones[new_pose_bone.name]
                new_pose_bone.rotation_mode = "QUATERNION"  # should be default but being explicit
                new_pose_bone.location = source_bone.location
                new_pose_bone.rotation_quaternion = source_bone.rotation_quaternion
                new_pose_bone.scale = source_bone.scale

        if child_mesh_obj:
            child_mesh_obj.parent = new_armature_obj
            armature_mod = child_mesh_obj.modifiers.new(name="FLVER Armature", type="ARMATURE")
            armature_mod.object = new_armature_obj
            armature_mod.show_in_editmode = True
            armature_mod.show_on_cage = True

        return new_armature_obj

    def duplicate_dummies(self) -> list[bpy.types.Object]:
        """Duplicate all FLVER Dummies of this model to new Empty objects in the same collections."""
        new_dummies = []
        for dummy in self.get_dummies():
            new_dummy_obj = new_empty_object(dummy.name)
            new_dummy_obj.soulstruct_type = SoulstructType.FLVER_DUMMY
            copy_obj_property_group(dummy.obj, new_dummy_obj, "flver_dummy")
            for collection in dummy.obj.users_collection:
                collection.objects.link(new_dummy_obj)
            new_dummies.append(new_dummy_obj)

        return new_dummies

    def duplicate(
        self,
        context: bpy.types.Context,
        collections: tp.Sequence[bpy.types.Collection] = None,
        make_materials_single_user=True,
        copy_pose=True,
    ):
        """Duplicate ALL objects, data-blocks, and materials of this FLVER model to a new one.

        Nothing is renamed; the caller can do that as desired. By default, names of new objects/data-blocks will
        obviously gain Blender '.001' dupe suffixes, but `.rename()` will remove these.
        """
        collections = collections or [context.scene.collection]

        # noinspection PyTypeChecker
        new_mesh_obj = new_mesh_object(self.mesh.name, self.mesh.data.copy())
        new_mesh_obj.soulstruct_type = SoulstructType.FLVER
        copy_obj_property_group(self.mesh, new_mesh_obj, "FLVER")
        for collection in collections:
            collection.objects.link(new_mesh_obj)

        if make_materials_single_user:
            # Duplicate materials.
            for i, mat in enumerate(tuple(new_mesh_obj.data.materials)):
                new_mesh_obj.data.materials[i] = mat.copy()

        if self.armature:
            new_armature_obj = self.duplicate_armature(context, new_mesh_obj, copy_pose)
        else:
            new_armature_obj = None

        new_dummies = self.duplicate_dummies()
        for dummy in new_dummies:
            dummy.parent = new_armature_obj or new_mesh_obj

        return self.__class__(new_mesh_obj)

    def duplicate_edit_mode(
        self,
        context: bpy.types.Context,
        make_materials_single_user=True,
        copy_pose=True,
    ) -> BlenderFLVER:
        """Duplicate to a new FLVER model, but in Edit Mode, taking only the selected vertices/edges/faces of Mesh.

        As with `duplicate()`, nothing is renamed; the caller can do that as desired.
        """
        if context.edit_object != self.mesh:
            raise FLVERError(f"Mesh of FLVER model '{self.name}' is not currently being edited in Edit Mode.")

        # Duplicate selected mesh data, then separate it into new object. Note that the `separate` operator will add the
        # new mesh to the same collection(s) automatically.
        bpy.ops.mesh.duplicate()
        bpy.ops.mesh.separate(type="SELECTED")  # new data-block; also copies properties, materials, data layers, etc.

        # noinspection PyTypeChecker
        new_mesh_obj = context.selected_objects[-1]  # type: bpy.types.MeshObject
        if not new_mesh_obj.name.startswith(self.mesh.name):
            # Tells us that `separate()` was unsuccessful.
            raise FLVERError(f"Could not duplicate and separate selected part of mesh into new object.")

        # Mesh is already added to same collections as this one, but also add to those manually specified (or scene).
        for collection in self.mesh.users_collection:
            # We'll get an error if we try to add to an existing collection, so check first.
            if collection not in new_mesh_obj.users_collection:
                collection.objects.link(new_mesh_obj)

        if make_materials_single_user:
            # Duplicate materials.
            for i, mat in enumerate(tuple(new_mesh_obj.data.materials)):
                new_mesh_obj.data.materials[i] = mat.copy()

        if self.armature:
            new_armature_obj = self.duplicate_armature(context, new_mesh_obj, copy_pose)
        else:
            new_armature_obj = None

        new_dummies = self.duplicate_dummies()
        for dummy in new_dummies:
            dummy.parent = new_armature_obj or new_mesh_obj

        return self.__class__(new_mesh_obj)

    @staticmethod
    def create_default_armature_parent(
        context: bpy.types.Context,
        model_name: str,
        mesh_child_obj: bpy.types.MeshObject = None,
    ) -> bpy.types.ArmatureObject:
        """Create a default Blender Armature for `mesh_child_obj` with a single default, origin, eponymous bone.

        This isn't needed for export, as the same Armature will be created for exported FLVER automatically.

        Raises a `ValueError` if the FLVER already has an Armature, which must be deleted first.
        """
        armature_name = f"{model_name} Armature"
        armature = new_armature_object(armature_name, bpy.data.armatures.new(armature_name))
        context.view_layer.objects.active = armature
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        edit_bone = armature.data.edit_bones.new(model_name)  # type: bpy.types.EditBone
        # Leave at origin. No usage flags set.
        edit_bone.use_local_location = True
        edit_bone.inherit_scale = "NONE"
        if mesh_child_obj:
            # Add Armature to same collections as Mesh.
            for collection in mesh_child_obj.users_collection:
                collection.objects.link(armature)
            mesh_child_obj.parent = armature
        return armature

    # endregion

    # region Import

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        flver: FLVER,
        name: str,
        image_import_manager: ImageImportManager | None = None,
        collection: bpy.types.Collection = None,
        merged_mesh: MergedMesh = None,
        bl_materials: tp.Sequence[BlenderFLVERMaterial] = None,
        force_bone_data_type: BoneDataType = None,
    ) -> BlenderFLVER:
        """Read a FLVER into a managed Blender Armature/Mesh.

        If the FLVER has only a single bone with all-default properties for this game, and no Dummies, no Armature will
        be created and the Mesh will be the root object. This is useful for simple static models like map pieces.

        `merged_mesh` can be created in advance (e.g. in parallel) and passed in directly for the corresponding `FLVER`.
        If so, `bl_materials` must also be given, and should have been created in advance to get the `MergedMesh`
        arguments anyway.

        NOTE: FLVER (for DS1 at least) supports a maximum of 38 bones per sub-mesh. When this maximum is reached, a new
        FLVER mesh is created. All of these sub-meshes are unified in Blender under the same material slot, and will
        be split again on export as needed.

        Some FLVER meshes also use the same material, but have different `Mesh` or `FaceSet` properties such as
        `use_backface_culling`. Backface culling is a material option in Blender, so these meshes will use different
        Blender material 'variants' even though they use the same FLVER material. The FLVER exporter will start by
        creating a FLVER material for every Blender material slot, then unify any identical FLVER material instances and
        redirect any differences like `use_backface_culling` or `is_bind_pose` to the FLVER mesh.

        Breakdown:
            - Blender stores POSITION, BONE WEIGHTS, and BONE INDICES on vertices. Any differences here will require
            genuine vertex duplication in Blender. (Of course, vertices at the same position in the same sub-mesh should
            essentially ALWAYS have the same bone weights and indices.)
            - Blender stores MATERIAL SLOT INDEX on faces. This is how different to FLVER meshes are represented; in
            a FLVER, faces that use different materials have already been split up into different meshes for rendering.
            - Blender stores UV COORDINATES, VERTEX COLORS, and NORMALS on face loops (corners, or 'vertex instances').
            This gels with what FLVER meshes want to do.
            - Blender does NOT import vertex tangents. These are calculated on export from the normals and UVs, with
            face UV sign taken into account (e.g. mirrored parts of a model will have mirrored tangents).
        """
        if merged_mesh and not bl_materials:
            raise ValueError("If `merged_mesh` is given, `bl_materials` must also be given.")
        elif not merged_mesh and bl_materials:
            raise ValueError("If `bl_materials` are given, `merged_mesh` must also be given.")

        collection = collection or context.scene.collection
        import_settings = context.scene.flver_import_settings
        bl_bone_names = []

        if (
            import_settings.omit_default_bone
            and not flver.dummies
            and len(flver.bones) == 1
            and flver.bones[0].is_default_origin
        ):
            # Single default bone can be auto-created on export. No Blender Armature parent needed/created.
            armature = None
            write_bone_type = force_bone_data_type or cls.BoneDataType.POSE  # guess Map Piece (but won't matter)
        else:
            # Create FLVER bone index -> Blender bone name dictionary. (Blender names are UTF-8.)
            # This is done even when `existing_armature` is given, as the order of bones in this new FLVER may be
            # different and the vertex weight indices need to be directed to the names of bones in `existing_armature`
            # correctly.
            for bone in flver.bones:
                # Just using actual bone names to avoid the need for parsing rules on export. However, duplicate names
                # need to be handled with suffixes.
                bl_bone_name = f"{bone.name} <DUPE>" if bone.name in bl_bone_names else bone.name
                bl_bone_names.append(bl_bone_name)

            # Create Blender Armature. We have to do this first so mesh vertices can be weighted to its bones.
            operator.to_object_mode()
            operator.deselect_all()
            armature = new_armature_object(f"{name} Armature", bpy.data.armatures.new(f"{name} Armature"))
            collection.objects.link(armature)  # needed before creating EditBones!
            write_bone_type = cls.create_bl_bones(
                operator,
                context,
                flver,
                armature,
                bl_bone_names,
                import_settings.base_edit_bone_length,
                force_bone_data_type,
            )

        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        mesh_data = bpy.data.meshes.new(name=name)

        if not flver.meshes:
            # FLVER has no meshes (e.g. c0000). Leave empty.
            mesh = new_mesh_object(f"{name} <EMPTY>", mesh_data, SoulstructType.FLVER)
            bl_materials = []
        elif any(mesh.invalid_layout for mesh in flver.meshes):
            # Corrupted meshes (e.g. some DS1R map pieces) that couldn't be fixed by `FLVER` class. Leave empty.
            mesh = new_mesh_object(f"{name} <INVALID>", mesh_data, SoulstructType.FLVER)
            bl_materials = []
        elif merged_mesh:
            # Merged mesh already given. Implies that Blender materials are handled manually as well.
            bl_vert_bone_weights, bl_vert_bone_indices = cls.create_bl_mesh(operator, mesh_data, merged_mesh)
            mesh = new_mesh_object(name, mesh_data, SoulstructType.FLVER)
            if armature:
                cls.create_bone_vertex_groups(mesh, bl_bone_names, bl_vert_bone_weights, bl_vert_bone_indices)
        else:
            # Create materials and `MergedMesh` now.
            try:
                bl_materials, mesh_bl_material_indices, bl_material_uv_layer_names = cls.create_materials(
                    operator,
                    context,
                    flver,
                    model_name=name,
                    material_blend_mode=import_settings.material_blend_mode,
                    image_import_manager=image_import_manager,
                    # No cached MatDef materials to pass in.
                )

            except MatDefError:
                # No materials will be created! TODO: Surely not.
                bl_materials = []
                mesh_bl_material_indices = ()
                bl_material_uv_layer_names = ()

            p = time.perf_counter()
            # Create merged mesh.
            merged_mesh = flver.to_merged_mesh(
                mesh_bl_material_indices,
                material_uv_layer_names=bl_material_uv_layer_names,
                merge_vertices=import_settings.merge_mesh_vertices,
            )
            operator.info(f"Merged FLVER meshes in {time.perf_counter() - p} s")
            if import_settings.merge_mesh_vertices:
                # Report vertex reduction.
                total_vertices = sum(len(mesh.vertices) for mesh in flver.meshes)
                total_merged_vertices = merged_mesh.vertex_data.shape[0]
                operator.info(
                    f"Merging reduced {total_vertices} vertices to {total_merged_vertices} "
                    f"({100 - 100 * total_merged_vertices / total_vertices:.2f}% reduction)"
                )
            bl_vert_bone_weights, bl_vert_bone_indices = cls.create_bl_mesh(operator, mesh_data, merged_mesh)
            mesh = new_mesh_object(name, mesh_data, SoulstructType.FLVER)
            if armature:
                cls.create_bone_vertex_groups(mesh, bl_bone_names, bl_vert_bone_weights, bl_vert_bone_indices)

        collection.objects.link(mesh)
        for bl_material in bl_materials:
            mesh.data.materials.append(bl_material.material)

        if armature:
            # Parent mesh to armature. This is critical for proper animation behavior (especially with root motion).
            mesh.parent = armature
            cls.create_mesh_armature_modifier(mesh, armature)

            # Armature is always created if there are Dummies, so we can safely create them here.
            for i, dummy in enumerate(flver.dummies):
                dummy_name = BlenderFLVERDummy.format_name(name, i, dummy.reference_id, suffix=None)
                BlenderFLVERDummy.new_from_soulstruct_obj(operator, context, dummy, dummy_name, armature, collection)

        # operator.info(f"Created FLVER Blender mesh '{name}' in {time.perf_counter() - start_time:.3f} seconds.")

        bl_flver = BlenderFLVER(mesh)
        bl_flver.obj.FLVER.bone_data_type = write_bone_type.value

        # Assign FLVER header properties.
        bl_flver.big_endian = flver.big_endian

        if flver.version in {FLVERVersion.DemonsSouls_0x10, FLVERVersion.DemonsSouls_0x14}:
            # We convert this to "DemonsSouls", since we can't export non-strip triangles for old versions (AFAIK).
            # Obviously, Demon's Souls can handle the newer version and you probably want it anyway.
            bl_flver.version = FLVERVersion.DemonsSouls.name
            operator.warning(
                f"Upgrading FLVER version {flver.version} to standard Demon's Souls version (0x15)."
            )
        else:
            try:
                bl_flver.version = flver.version.name
            except TypeError:
                operator.warning(f"FLVER version '{flver.version}' not recognized. Leaving as 'Selected Game'.")

        bl_flver.unicode = flver.unicode

        bl_flver.f0_unk_x4a = flver.f0_unk_x4a
        bl_flver.f0_unk_x4b = flver.f0_unk_x4b
        bl_flver.f0_unk_x4c = flver.f0_unk_x4c
        bl_flver.f0_unk_x5c = flver.f0_unk_x5c

        bl_flver.f2_unk_x4a = flver.f2_unk_x4a
        bl_flver.f2_unk_x4c = flver.f2_unk_x4c
        bl_flver.f2_unk_x5c = flver.f2_unk_x5c
        bl_flver.f2_unk_x5d = flver.f2_unk_x5d
        bl_flver.f2_unk_x68 = flver.f2_unk_x68

        bl_flver.mesh_vertices_merged = import_settings.merge_mesh_vertices

        return bl_flver  # might be used by other importers

    @staticmethod
    def create_mesh_armature_modifier(bl_mesh: bpy.types.MeshObject, bl_armature: bpy.types.ArmatureObject):
        armature_mod = bl_mesh.modifiers.new(name="FLVER Armature", type="ARMATURE")
        armature_mod.object = bl_armature
        armature_mod.show_in_editmode = True
        armature_mod.show_on_cage = True

    @classmethod
    def create_materials(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        flver: FLVER,
        model_name: str,
        material_blend_mode: str,
        image_import_manager: ImageImportManager | None = None,
        bl_materials_by_matdef_name: dict[str, bpy.types.Material] = None,
    ) -> tuple[tuple[BlenderFLVERMaterial, ...], tuple[int, ...], tuple[tuple[str, ...], ...]]:
        """Create Blender materials needed for `flver`.

        We need to scan the FLVER to actually parse which unique combinations of Material/Mesh properties exist.

        Returns a list of Blender material indices for each mesh, and a list of UV layer names for each Blender
        material (NOT each mesh).
        """

        # Mesh-matched list of dictionaries mapping sample/texture type to texture path (only name matters).
        settings = operator.settings(context)
        import_settings = context.scene.flver_import_settings
        mtdbnd = get_cached_mtdbnd(operator, settings) if not GAME_CONFIG[settings.game].uses_matbin else None
        matbinbnd = get_cached_matbinbnd(operator, settings) if GAME_CONFIG[settings.game].uses_matbin else None
        all_mesh_texture_stems = cls.get_mesh_flver_textures(flver, matbinbnd)
        bl_materials_by_matdef_name = bl_materials_by_matdef_name or {}  # still worthwhile within one FLVER

        if import_settings.import_textures:
            if image_import_manager or settings.str_image_cache_directory:
                p = time.perf_counter()
                all_texture_stems = {
                    v
                    for mesh_textures in all_mesh_texture_stems
                    for v in mesh_textures.values()
                    if v  # obviously ignore empty texture paths
                }
                texture_collection = cls.load_texture_images(
                    operator, context, model_name, all_texture_stems, image_import_manager
                )
                if texture_collection:
                    operator.info(f"Loaded {len(texture_collection)} textures in {time.perf_counter() - p:.3f} s.")
            else:
                operator.info("No imported textures or PNG cache folder given. No textures loaded for FLVER.")

        # Maps FLVER meshes to their Blender material index to store per-face in the merged mesh.
        # Meshes that originally indexed the same FLVER material may have different Blender 'variant' materials that
        # hold certain Mesh/FaceSet properties like `use_backface_culling`.
        # Conversely, Meshes that only serve to handle per-mesh bone maximums (e.g. 38 in DS1) will use the same
        # Blender material and be split again automatically on export (but likely not in an indentical way!).
        mesh_bl_material_indices = []
        # UV layer names used by each Blender material index (NOT each FLVER mesh).
        bl_material_uv_layer_names = []  # type: list[tuple[str, ...]]

        # Map FLVER material hashes to the indices of variant Blender materials sourced from them, which hold distinct
        # Mesh/FaceSet properties.
        flver_material_hash_variants = {}

        # Map FLVER material hashes to their generated `MatDef` instances.
        flver_matdefs = {}  # type: dict[int, MatDef | None]
        for mesh in flver.meshes:
            material_hash = hash(mesh.material)  # TODO: should hash ignore material name?
            if material_hash in flver_matdefs:
                continue  # material already created (used by a previous mesh)

            # Try to look up material info from MTD or MATBIN (Elden Ring).
            try:
                matdef_class = settings.get_game_matdef_class()
            except UnsupportedGameError:
                operator.warning(f"FLVER material shader creation not implemented for game {settings.game.name}.")
                matdef = None
            except MatDefError as ex:
                operator.warning(
                    f"Could not create `MatDef` for game material '{mesh.material.mat_def_name}'. Error:\n"
                    f"    {ex}"
                )
                matdef = None
            else:
                if GAME_CONFIG[settings.game].uses_matbin:
                    matdef = matdef_class.from_matbinbnd_or_name(mesh.material.mat_def_name, matbinbnd)
                else:
                    matdef = matdef_class.from_mtdbnd_or_name(mesh.material.mat_def_name, mtdbnd)

            flver_matdefs[material_hash] = matdef

        new_materials = []

        for mesh, mesh_textures in zip(flver.meshes, all_mesh_texture_stems, strict=True):
            material = mesh.material
            material_hash = hash(material)  # NOTE: if there are duplicate FLVER materials, this will combine them
            vertex_color_count = len([f for f in mesh.vertices.dtype.names if "color" in f])

            if material_hash not in flver_material_hash_variants:
                # First time this FLVER material has been encountered. Create it in Blender now.
                # NOTE: Vanilla material names are unused and essentially worthless. They can also be the same for
                #  materials that actually use different lightmaps, EVEN INSIDE the same FLVER model. Names are changed
                #  here to just reflect the index. The original name is NOT kept to avoid stacking up formatting on
                #  export/import and because it is so useless anyway.
                flver_material_index = len(flver_material_hash_variants)
                bl_material_index = len(new_materials)
                matdef = flver_matdefs[material_hash]

                # Create a relatively informative material name. We use material index, mat def, and model name as a
                # suffix to maximize the chances of a unique Blender name.
                bl_material_name = (
                    f"{material.name} [{flver_material_index} | {material.mat_def_stem} | {model_name}]"
                )

                bl_material = BlenderFLVERMaterial.new_from_flver_material(
                    operator,
                    context,
                    material,
                    flver_sampler_texture_stems=mesh_textures,
                    material_name=bl_material_name,
                    matdef=matdef,
                    mesh=mesh,
                    vertex_color_count=vertex_color_count,
                    blend_mode=material_blend_mode,
                    warn_missing_textures=image_import_manager is not None,
                    bl_materials_by_matdef_name=bl_materials_by_matdef_name,
                )

                mesh_bl_material_indices.append(bl_material_index)
                flver_material_hash_variants[material_hash] = [bl_material_index]

                new_materials.append(bl_material)
                if matdef:
                    used_uv_layers = matdef.get_used_uv_layers()
                    bl_material_uv_layer_names.append(tuple(layer.name for layer in used_uv_layers))
                else:
                    # UV layer names not known for this material. `MergedMesh` will just use index, which may cause
                    # conflicting types of UV data to occupy the same Blender UV slot.
                    bl_material_uv_layer_names.append(())
                continue

            existing_variant_bl_indices = flver_material_hash_variants[material_hash]

            # Check if Blender material needs to be duplicated as a variant with different Mesh properties.
            found_existing_material = False
            for existing_bl_material_index in existing_variant_bl_indices:
                # NOTE: We do not care about enforcing any maximum mesh local bone count in Blender! The FLVER
                # exporter will create additional split meshes as necessary for that.
                existing_bl_material = new_materials[existing_bl_material_index]
                if (
                    existing_bl_material.is_bind_pose == mesh.is_bind_pose
                    and existing_bl_material.default_bone_index == mesh.default_bone_index
                    and existing_bl_material.face_set_count == len(mesh.face_sets)
                    and existing_bl_material.use_backface_culling == mesh.use_backface_culling
                ):
                    # Blender material already exists with the same Mesh properties. No new variant neeed.
                    mesh_bl_material_indices.append(existing_bl_material_index)
                    found_existing_material = True
                    break

            if found_existing_material:
                continue

            # No match found. New Blender material variant is needed to hold unique mesh data.
            # Since the most common cause of a variant is backface culling being enabled vs. disabled, that difference
            # gets its own prefix: we add ' <BC>' to the end of whichever variant has backface culling enabled.
            variant_index = len(existing_variant_bl_indices)
            first_material = new_materials[existing_variant_bl_indices[0]]
            variant_name = first_material.name + f" <V{variant_index}>"  # may be replaced below

            if (
                first_material.is_bind_pose == mesh.is_bind_pose
                and first_material.default_bone_index == mesh.default_bone_index
                and first_material.face_set_count == len(mesh.face_sets)
                and first_material.use_backface_culling != mesh.use_backface_culling
            ):
                # Only difference is backface culling. We mark 'BC' on the one that has it enabled.
                if first_material.use_backface_culling:
                    variant_name = first_material.name  # swap with first material's name (no BC)
                    first_material.name += f" <V{variant_index}, BC>"
                else:
                    variant_name = first_material.name + f" <V{variant_index}, BC>"  # instead of just variant index

            bl_material = BlenderFLVERMaterial.new_from_flver_material(
                operator,
                context,
                material,
                mesh_textures,
                material_name=variant_name,
                matdef=flver_matdefs[material_hash],
                mesh=mesh,
                vertex_color_count=vertex_color_count,
                blend_mode=material_blend_mode,
                bl_materials_by_matdef_name=bl_materials_by_matdef_name,
            )

            new_bl_material_index = len(new_materials)
            mesh_bl_material_indices.append(new_bl_material_index)
            flver_material_hash_variants[material_hash].append(new_bl_material_index)
            new_materials.append(bl_material)
            if flver_matdefs[material_hash] is not None:
                bl_material_uv_layer_names.append(
                    tuple(layer.name for layer in flver_matdefs[material_hash].get_used_uv_layers())
                )
            else:
                bl_material_uv_layer_names.append(())

        return tuple(new_materials), tuple(mesh_bl_material_indices), tuple(bl_material_uv_layer_names)

    @staticmethod
    def get_mesh_flver_textures(
        flver: FLVER,
        matbinbnd: MATBINBND | None,
    ) -> list[dict[str, str]]:
        """For each mesh, get a dictionary mapping sampler names (e.g. 'g_Diffuse') to texture path names (e.g.
        'c2000_fur'). The texture path names are always lower-case.

        These paths may come from the FLVER material (older games) or MATBIN (newer games). In the latter case, FLVER
        material paths are usually empty, but will be accepted as overrides if given.
        """
        all_mesh_texture_names = []
        for mesh in flver.meshes:
            mesh_texture_stems = {}
            if matbinbnd:
                try:
                    matbin = matbinbnd.get_matbin(mesh.material.mat_def_name)
                except KeyError:
                    pass  # missing
                else:
                    mesh_texture_stems |= matbin.get_all_sampler_stems(lower=True)
            for texture in mesh.material.textures:
                if texture.path:
                    # FLVER texture path can also override MATBIN path.
                    mesh_texture_stems[texture.texture_type] = texture.stem.lower()
            all_mesh_texture_names.append(mesh_texture_stems)

        return all_mesh_texture_names

    @classmethod
    def create_bl_mesh(
        cls,
        operator: LoggingOperator,
        mesh_data: bpy.types.Mesh,
        merged_mesh: MergedMesh,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Create Blender Mesh with plenty of efficient `foreach_set()` calls to raveled `MergedMesh` arrays.

        Returns two arrays of bone indices and bone weights for the created Blender vertices.
        """

        # p = time.perf_counter()

        merged_mesh.swap_vertex_yz(tangents=False, bitangents=False)
        merged_mesh.invert_vertex_uv(invert_u=False, invert_v=True)
        merged_mesh.normalize_normals()

        # We can create vertices before `BMesh` easily.
        vertex_count = merged_mesh.vertex_data.shape[0]
        mesh_data.vertices.add(vertex_count)
        mesh_data.vertices.foreach_set("co", np.array(merged_mesh.vertex_data["position"]).ravel())

        all_faces = merged_mesh.faces[:, :3]  # drop material index column
        if merged_mesh.vertices_merged:
            # Retrieve true vertex indices used by each face loop indexed in `merged_mesh.faces`.
            face_vertex_indices = merged_mesh.loop_vertex_indices[all_faces]
        else:
            # No vertex merging occurred, so FLVER 'loops' and 'vertices' are still synonymous.
            face_vertex_indices = all_faces

        # Drop faces that don't use three unique vertex indices.
        # TODO: Try a vectorized approach that calculates the difference between each pair of the three columns, then
        #  takes the product of those differences. Any row that ends up with zero is degenerate.
        unique_mask = np.apply_along_axis(lambda row: len(np.unique(row)) == 3, 1, face_vertex_indices)
        valid_face_vertex_indices = face_vertex_indices[unique_mask]

        valid_face_count = valid_face_vertex_indices.shape[0]
        invalid_face_count = face_vertex_indices.shape[0] - valid_face_count
        if invalid_face_count > 0:
            operator.info(f"Removed {invalid_face_count} invalid/degenerate mesh faces from {mesh_data.name}.")

        # Directly assign face corner (loop) vertex indices.
        mesh_data.loops.add(valid_face_vertex_indices.size)
        mesh_data.loops.foreach_set("vertex_index", valid_face_vertex_indices.ravel())

        # Create triangle polygons.
        # Blender polygons are defined by loop start and count (total), which is entirely on-rails here for triangles.
        loop_starts = np.arange(0, valid_face_count * 3, 3, dtype=np.int32)  # just [0, 3, 6, ...]
        loop_totals = np.full(valid_face_count, 3, dtype=np.int32)  # all triangles (3)
        mesh_data.polygons.add(valid_face_count)
        mesh_data.polygons.foreach_set("loop_start", loop_starts)
        mesh_data.polygons.foreach_set("loop_total", loop_totals)
        mesh_data.polygons.foreach_set("material_index", merged_mesh.faces[:, 3])

        mesh_data.update(calc_edges=True)

        # self.operator.info(f"Created Blender mesh in {time.perf_counter() - p} s")

        valid_face_loop_indices = all_faces[unique_mask].ravel()

        # Create and populate UV and vertex color data layers (on loops).
        for i, (uv_layer_name, merged_loop_uv_array) in enumerate(merged_mesh.loop_uvs.items()):
            # self.operator.info(f"Creating UV layer {i}: {uv_layer_name}")
            uv_layer = mesh_data.uv_layers.new(name=uv_layer_name, do_init=False)
            loop_uv_data = merged_loop_uv_array[valid_face_loop_indices].ravel()
            uv_layer.data.foreach_set("uv", loop_uv_data)
        for i, merged_color_array in enumerate(merged_mesh.loop_vertex_colors):
            # self.operator.info(f"Creating Vertex Colors layer {i}: VertexColors{i}")
            # TODO: Apparently `vertex_colors` is deprecated in favor of "color attributes". Investigate.
            color_layer = mesh_data.vertex_colors.new(name=f"VertexColors{i}")
            loop_color_data = merged_color_array[valid_face_loop_indices].ravel()
            color_layer.data.foreach_set("color", loop_color_data)

        # Some FLVERs (e.g. c2120, 'Shadowlurker' in Demon's Souls) have materials that reference UV layers (with real
        # included textures) that are not actually used by any Mesh. The game's `MatDef` will handle these special cases
        # and ensure that Blender doesn't look for them on export, even if they appear in the shader's node tree.

        # NOTE: `Mesh.create_normals_split()` was removed in Blender 4.1, and I no longer support older versions than
        # that. New versions of Blender automatically create the `mesh.corner_normals` collection. We also don't need to
        # enable `use_auto_smooth` or call `calc_normals_split()` anymore.

        loop_normal_data = merged_mesh.loop_normals[valid_face_loop_indices]  # NOT raveled
        mesh_data.normals_split_custom_set(loop_normal_data)  # one normal per loop
        mesh_data.update()

        return merged_mesh.vertex_data["bone_weights"], merged_mesh.vertex_data["bone_indices"]

    @classmethod
    def create_bone_vertex_groups(
        cls,
        mesh: bpy.types.MeshObject,
        bl_bone_names: list[str],
        bl_vert_bone_weights: np.ndarray,
        bl_vert_bone_indices: np.ndarray,
    ):
        # Naming a vertex group after a Blender bone will automatically link it in the Armature modifier below.
        # NOTE: For imports that use an existing Armature (e.g. equipment), invalid bone names such as the root dummy
        # equipment bones have already been removed from `bl_bone_names` here. TODO: I think this note is outdated.
        bone_vertex_groups = [
            mesh.vertex_groups.new(name=bone_name)
            for bone_name in bl_bone_names
        ]  # type: list[bpy.types.VertexGroup]

        # Awkwardly, we need a separate call to `bone_vertex_groups[bone_index].add(indices, weight)` for each combo
        # of `bone_index` and `weight`, so the dictionary keys constructed below are a tuple of those two to minimize
        # the number of `VertexGroup.add()` calls needed at the end of this function.
        bone_vertex_group_indices = {}  # type: dict[tuple[int, float], list[int]]

        # p = time.perf_counter()
        # TODO: Can probably be vectorized better with NumPy.
        for v_i, (bone_indices, bone_weights) in enumerate(zip(bl_vert_bone_indices, bl_vert_bone_weights)):
            if all(weight == 0.0 for weight in bone_weights) and len(set(bone_indices)) == 1:
                # Map Piece FLVERs use a single duplicated index and no weights.
                # TODO: May be able to assert that this is ALWAYS true for ALL vertices in map pieces.
                v_bone_index = bone_indices[0]
                bone_vertex_group_indices.setdefault((v_bone_index, 1.0), []).append(v_i)
            else:
                # Standard multi-bone weighting.
                for v_bone_index, v_bone_weight in zip(bone_indices, bone_weights):
                    if v_bone_weight == 0.0:
                        continue
                    bone_vertex_group_indices.setdefault((v_bone_index, v_bone_weight), []).append(v_i)

        for (bone_index, bone_weight), bone_vertices in bone_vertex_group_indices.items():
            bone_vertex_groups[bone_index].add(bone_vertices, bone_weight, "ADD")

        # self.operator.info(f"Assigned Blender vertex groups to bones in {time.perf_counter() - p} s")

    @classmethod
    def create_bl_bones(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        flver: FLVER,
        armature: bpy.types.ArmatureObject,
        bl_bone_names: list[str],
        base_edit_bone_length: float,
        write_bone_type: BoneDataType = None,
    ) -> BoneDataType:
        """Create FLVER bones on given `bl_armature_obj` in Blender.

        Bones can be a little confusing in Blender. See:
            https://docs.blender.org/api/blender_python_api_2_71_release/info_gotcha.html#editbones-posebones-bone-bones

        The short story is that the "resting state" of each bone, including its head and tail position, is created in
        EDIT mode (as `EditBone` instances). This data defines the "zero deformation" state of the mesh with regard to
        bone weights, and will typically not be edited again when posing/animating a mesh that is rigged to this
        Armature. Instead, the bones are accessed as `PoseBone` instances in POSE mode, where they are treated like
        objects with transform data.

        If a FLVER bone has a parent bone, its FLVER transform is given relative to its parent's frame of reference.
        Determining the final position of any given bone in world space therefore requires all of its parents'
        transforms to be accumulated up to the root. (The same is true for HKX animation coordinates, which are local
        bone transformations in the same coordinate system.)

        Note that while bones are typically used for obvious animation cases in characters, objects, and parts (e.g.
        armor/weapons), they are also occasionally used in a fairly basic way by map pieces to position certain vertices
        in certain meshes. When this happens, so far, the bones have always been root bones, and basically function as
        shifted origins for the coordinates of certain vertices. I strongly suspect, but have not absolutely confirmed,
        that the `is_bind_pose` attribute of each mesh indicates whether FLVER bone data should be written to the
        EditBone (`is_bind_pose=True`) or PoseBone (`is_bind_pose=False`). Of course, we have to decide for each BONE,
        not each mesh, so currently I am enforcing that `is_bind_pose=False` for ALL meshes in order to write the bone
        transforms to PoseBone rather than EditBone. A warning will be logged if only some of them are `False`.

        The AABB of each bone is presumably generated to include all vertices that use that bone as a weight.

        The detected `BoneDataType` is returned, which indicates whether bone data was written to `EditBones` or
        `PoseBones`. This is saved to FLVER properties in Blender for export.
        """

        if not write_bone_type:
            write_bone_type = cls.BoneDataType.EDIT if flver.any_bind_pose() else cls.BoneDataType.POSE

        # We need edit mode to create `EditBones` below.
        context.view_layer.objects.active = armature
        operator.to_edit_mode()

        # Create all edit bones. Head/tail are not set yet (depends on `write_bone_type` below).
        edit_bones = cls.create_edit_bones(armature.data, flver, bl_bone_names)

        # NOTE: Bones that have no vertices weighted to them are left as 'unused' root bones in the FLVER skeleton.
        # They may be animated by HKX animations (and will affect their children appropriately) but will not actually
        # affect any vertices in the mesh.

        if write_bone_type == cls.BoneDataType.EDIT:
            cls.write_data_to_edit_bones(operator, flver, edit_bones, base_edit_bone_length)
            del edit_bones  # clear references to edit bones as we exit EDIT mode
            if bpy.ops.object.mode_set.poll():
                bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        elif write_bone_type == cls.BoneDataType.POSE:
            # This method will change back to OBJECT mode internally before setting pose bone data.
            cls.write_data_to_pose_bones(operator, flver, armature, edit_bones, base_edit_bone_length)
        else:
            # Should not be possible to reach.
            raise ValueError(f"Invalid `write_bone_type`: {write_bone_type}")

        return write_bone_type  # can only be EDIT or POSE

    @staticmethod
    def create_edit_bones(
        armature_data: bpy.types.Armature,
        flver: FLVER,
        bl_bone_names: list[str],
    ) -> list[bpy.types.EditBone]:
        """Create all edit bones from FLVER bones in `bl_armature`."""
        edit_bones = []  # all bones
        for game_bone, bl_bone_name in zip(flver.bones, bl_bone_names, strict=True):
            game_bone: FLVERBone
            edit_bone = armature_data.edit_bones.new(bl_bone_name)  # '<DUPE>' suffixes already added to names
            edit_bone: bpy.types.EditBone

            # Storing 'Unused' flag for now. TODO: If later games' other flags can't be safely auto-detected, store too.
            edit_bone.FLVER_BONE.is_unused = bool(game_bone.usage_flags & FLVERBoneUsageFlags.UNUSED)

            # If this is `False`, then a bone's rest pose rotation will NOT affect its relative pose basis translation.
            # That is, a standard TRS transform becomes an 'RTS' transform instead. We don't want such behavior,
            # particularly for FLVER root bones like 'Pelvis'.
            edit_bone.use_local_location = True

            # FLVER bones never inherit scale.
            edit_bone.inherit_scale = "NONE"

            # We don't bother storing child or sibling bones. They are generated from parents on export.
            edit_bones.append(edit_bone)
        return edit_bones

    @staticmethod
    def write_data_to_edit_bones(
        operator: LoggingOperator,
        flver: FLVER,
        edit_bones: list[bpy.types.EditBone],
        base_edit_bone_length: float,
    ):
        game_arma_transforms = flver.get_bone_armature_space_transforms()

        for game_bone, edit_bone, game_arma_transform in zip(
            flver.bones, edit_bones, game_arma_transforms, strict=True
        ):
            game_bone: FLVERBone
            game_translate, game_rotmat, game_scale = game_arma_transform

            if not is_uniform(game_scale, rel_tol=0.001):
                operator.warning(f"Bone {game_bone.name} has non-uniform scale: {game_scale}. Left as identity.")
                bone_length = base_edit_bone_length
            elif any(c < 0.0 for c in game_scale):
                operator.warning(f"Bone {game_bone.name} has negative scale: {game_scale}. Left as identity.")
                bone_length = base_edit_bone_length
            elif math.isclose(game_scale.x, 1.0, rel_tol=0.001):
                # Bone scale is ALMOST uniform and 1. Correct it.
                bone_length = base_edit_bone_length
            else:
                # Bone scale is uniform and not close to 1, which we can support (though it should be rare/never).
                bone_length = game_scale.x * base_edit_bone_length

            bl_translate = GAME_TO_BL_VECTOR(game_translate)
            # We need to set an initial head/tail position with non-zero length for the `matrix` setter to act upon.
            edit_bone.head = bl_translate
            edit_bone.tail = bl_translate + Vector((0.0, bone_length, 0.0))  # default tail position, rotated below

            bl_rot_mat3 = GAME_TO_BL_MAT3(game_rotmat)
            bl_lrs_mat = bl_rot_mat3.to_4x4()
            bl_lrs_mat.translation = bl_translate
            edit_bone.matrix = bl_lrs_mat
            edit_bone.length = bone_length  # does not interact with `matrix`

            if game_bone.parent_bone is not None:
                parent_bone_index = game_bone.parent_bone.get_bone_index(flver.bones)
                parent_edit_bone = edit_bones[parent_bone_index]
                edit_bone.parent = parent_edit_bone
                # edit_bone.use_connect = True

    @staticmethod
    def write_data_to_pose_bones(
        operator: LoggingOperator,
        flver: FLVER,
        armature: bpy.types.ArmatureObject,
        edit_bones: list[bpy.types.EditBone],
        base_edit_bone_length: float,
    ):
        for game_bone, edit_bone in zip(flver.bones, edit_bones, strict=True):
            # All edit bones are just Blender-Y-direction ("forward") stubs of base length.
            # This rigging makes map piece 'pose' bone data transform as expected for showing accurate vertex positions.
            edit_bone.head = Vector((0, 0, 0))
            edit_bone.tail = Vector((0, base_edit_bone_length, 0))

        del edit_bones  # clear references to edit bones as we exit EDIT mode
        operator.to_object_mode()

        pose_bones = armature.pose.bones
        for game_bone, pose_bone in zip(flver.bones, pose_bones):
            # TODO: Pose bone transforms are relative to parent (in both FLVER and Blender).
            #  Confirm map pieces still behave as expected, though (they shouldn't even have child bones).
            pose_bone.rotation_mode = "QUATERNION"  # should already be default, but being explicit
            game_translate, game_bone_rotate = game_bone.translate, game_bone.rotate
            pose_bone.location = GAME_TO_BL_VECTOR(game_translate)
            pose_bone.rotation_quaternion = GAME_TO_BL_EULER(game_bone_rotate).to_quaternion()
            pose_bone.scale = GAME_TO_BL_VECTOR(game_bone.scale)

    @staticmethod
    def load_texture_images(
        operator: LoggingOperator,
        context: bpy.types.Context,
        name: str,
        texture_stems: set[str],
        image_import_manager: ImageImportManager | None = None,
    ) -> DDSTextureCollection:
        """Load texture images from PNG cache directory or TPFs found with `image_import_manager`.

        Will NEVER load an image that is already in Blender's data, regardless of image type (identified by stem only).
        Note that these stems ARE case-sensitive, as I don't want them to change when a FLVER is imported and exported
        without any other modifications. (The cached images are also case-sensitive.)
        """
        settings = operator.settings(context)

        # TODO: I was checking every Image in Blender's data to find 1x1 magenta dummy textures to replace, but that's
        #  super slow as more and more textures are loaded.
        bl_image_stems = {image_name.split(".")[0] for image_name in bpy.data.images.keys()}

        new_texture_collection = DDSTextureCollection()

        tpf_textures_to_load = {}  # type: dict[str, TPFTexture]
        for texture_stem in texture_stems:
            if texture_stem in bl_image_stems:
                continue  # already loaded
            if texture_stem in tpf_textures_to_load:
                continue  # already queued to load below

            if settings.read_cached_images and settings.str_image_cache_directory:
                cached_path = settings.get_cached_image_path(texture_stem)
                if cached_path.is_file():
                    # Found cached image.
                    dds_texture = DDSTexture.new_from_image_path(cached_path, settings.pack_image_data)
                    new_texture_collection.add(dds_texture)
                    bl_image_stems.add(texture_stem)
                    continue

            if image_import_manager:
                try:
                    # Searching for original texture is NOT case-sensitive.
                    texture = image_import_manager.get_flver_texture(texture_stem, name)
                except KeyError as ex:
                    operator.warning(str(ex))
                else:
                    tpf_textures_to_load[texture_stem] = texture
                    continue

            operator.warning(f"Could not find TPF or cached image '{texture_stem}' for FLVER '{name}'.")

        if tpf_textures_to_load:
            for texture_stem in tpf_textures_to_load:
                operator.info(f"Loading texture into Blender: {texture_stem}")
            t = time.perf_counter()
            image_format = settings.bl_image_format
            deswizzle_platform = settings.game_config.swizzle_platform
            if image_format == BlenderImageFormat.TARGA:
                all_image_data = batch_get_tpf_texture_tga_data(
                    list(tpf_textures_to_load.values()), deswizzle_platform
                )
            elif image_format == BlenderImageFormat.PNG:
                all_image_data = batch_get_tpf_texture_png_data(
                    list(tpf_textures_to_load.values()), deswizzle_platform, fmt="rgba"
                )
            else:
                raise ValueError(f"Unsupported image format for DDS conversion: {image_format}")

            if settings.write_cached_images:
                write_image_directory = settings.image_cache_directory  # could be None
            else:
                write_image_directory = None
            operator.info(
                f"Converted images in {time.perf_counter() - t} s (cached = {settings.write_cached_images})"
            )
            for texture_stem, image_data in zip(tpf_textures_to_load.keys(), all_image_data):
                if image_data is None:
                    continue  # failed to convert this texture
                dds_texture = DDSTexture.new_from_image_data(
                    operator,
                    name=texture_stem,
                    image_format=image_format,
                    image_data=image_data,
                    image_cache_directory=write_image_directory,
                    replace_existing=False,  # not currently used
                    pack_image_data=settings.pack_image_data,
                )
                new_texture_collection.add(dds_texture)

        return new_texture_collection

    # endregion

    # region Export

    def _get_empty_flver(self, settings: SoulstructSettings) -> FLVER:

        if self.version == "DEFAULT":
            # Default is game-dependent.
            try:
                version = settings.game_config.flver_default_version
            except KeyError:
                raise ValueError(
                    f"Do not know default FLVER Version for game {settings.game}. You must set 'Version' yourself on "
                    f"FLVER object '{self.name}' before exporting."
                )
        else:
            try:
                version = FLVERVersion[self.version]
            except KeyError:
                raise ValueError(f"Invalid FLVER Version: '{self.version}'. Please report this bug to Grimrukh!")

        if version <= 0xFFFF:
            return FLVER(
                big_endian=self.big_endian,
                version=version,
                unicode=self.unicode,
                f0_unk_x4a=self.f0_unk_x4a,
                f0_unk_x4b=self.f0_unk_x4b,
                f0_unk_x4c=self.f0_unk_x4c,
                f0_unk_x5c=self.f0_unk_x5c,
            )

        return FLVER(
            big_endian=self.big_endian,
            version=version,
            unicode=self.unicode,
            f2_unk_x4a=self.f2_unk_x4a,
            f2_unk_x4c=self.f2_unk_x4c,
            f2_unk_x5c=self.f2_unk_x5c,
            f2_unk_x5d=self.f2_unk_x5d,
            f2_unk_x68=self.f2_unk_x68,
        )

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        texture_collection: DDSTextureCollection = None,
    ) -> FLVER:
        """Wraps actual method with temp FLVER management."""
        self.clear_temp_flver()
        try:
            return self._to_soulstruct_obj(operator, context, texture_collection)
        finally:
            self.clear_temp_flver()

    def _to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        texture_collection: DDSTextureCollection = None,
    ) -> FLVER:
        """`FLVER` exporter. By far the most complicated function in the add-on!"""

        # This is passed all the way through to the node inspection in FLVER materials to map texture stems to Images.
        if texture_collection is None:
            texture_collection = DDSTextureCollection()

        settings = operator.settings(context)
        flver = self._get_empty_flver(settings)  # could be `FLVER` or `FLVER0`

        export_settings = context.scene.flver_export_settings
        mtdbnd = get_cached_mtdbnd(operator, settings) if not GAME_CONFIG[settings.game].uses_matbin else None
        matbinbnd = get_cached_matbinbnd(operator, settings) if GAME_CONFIG[settings.game].uses_matbin else None

        if self.armature:
            bl_dummies = self.get_dummies(operator)
            read_bone_type = self.bone_data_type  # set on import and managed by user afterward
            # read_bone_type = self.guess_read_bone_type(operator)
            operator.info(f"Exporting FLVER '{self.name}' with bone data from {read_bone_type.capitalize()}Bones.")
        else:
            bl_dummies = []
            read_bone_type = self.BoneDataType.NONE

        if not self.armature or not self.armature.pose.bones:
            operator.info(  # not a warning
                f"No non-empty Armature to export. Creating FLVER skeleton with a single default bone at origin named "
                f"'{self.export_name}'."
             )
            default_bone = FLVERBone(name=self.export_name)  # default transform and other fields
            flver.bones.append(default_bone)
            bl_bone_names = [default_bone.name]
            using_default_bone = True
        else:
            flver.bones, bl_bone_names, bone_arma_transforms = self.create_flver_bones(
                operator, context, self.armature, read_bone_type,
            )
            flver.set_bone_children_siblings()  # only parents set in `create_bones`
            flver.set_bone_armature_space_transforms(bone_arma_transforms)
            using_default_bone = False

        # Make Mesh the active object again.
        context.view_layer.objects.active = self.mesh

        for bl_dummy in bl_dummies:
            flver_dummy = bl_dummy.to_soulstruct_obj(operator, context, self.armature)
            # Mark attach/parent bones as used. TODO: Set more specific flags in later games (2 here).
            if flver_dummy.attach_bone_index >= 0:
                flver.bones[flver_dummy.attach_bone_index].usage_flags &= ~1
            if flver_dummy.parent_bone_index >= 0:
                flver.bones[flver_dummy.parent_bone_index].usage_flags &= ~1
            flver.dummies.append(flver_dummy)

        # `MatDef` for each Blender material is needed to determine which Blender UV layers to use for which loops.
        try:
            matdef_class = settings.get_game_matdef_class()
        except UnsupportedGameError:
            raise UnsupportedGameError(f"Cannot yet export FLVERs for game {settings.game}. (No `MatDef` class.)")

        matdefs = []
        for bl_material in self.mesh.data.materials:
            mat_def_name = Path(bl_material.FLVER_MATERIAL.mat_def_path).name
            if GAME_CONFIG[settings.game].uses_matbin:
                matdef = matdef_class.from_matbinbnd_or_name(mat_def_name, matbinbnd)
            else:
                matdef = matdef_class.from_mtdbnd_or_name(mat_def_name, mtdbnd)
            matdefs.append(matdef)

        if not self.mesh.data.vertices:
            # No meshes in FLVER (e.g. c0000). We also leave all bounding boxes as their default max/min values.
            # We don't warn for expected empty FLVERs c0000 and c1000.
            if self.name[:5] not in {"c0000", "c1000"}:
                operator.warning(f"Exporting non-c0000/c1000 FLVER '{self.name}' with no mesh data.")
            return flver

        # TODO: Current choosing default vertex buffer layout (CHR vs. MAP PIECE) based on read bone type, which in
        #  turn depends on `mesh.is_bind_pose` at FLVER import. All a bit messily wired together...
        self.export_flver_meshes(
            operator,
            context,
            flver,
            bl_bone_names=bl_bone_names,
            use_chr_layout=read_bone_type == self.BoneDataType.EDIT,
            normal_tangent_dot_max=export_settings.normal_tangent_dot_max,
            create_lod_face_sets=export_settings.create_lod_face_sets,
            matdefs=matdefs,
            texture_collection=texture_collection,
            using_default_bone=using_default_bone,
        )

        # TODO: Bone bounding box space seems to be always local to the bone for characters and always in armature space
        #  for map pieces. Not sure about objects, could be some of each (haven't found any non-origin bones that any
        #  vertices are weighted to with `is_bind_pose=True`). This is my temporary hack since we are already using
        #  'read_bone_type == self.BoneDataType.POSE' as a marker for map pieces.
        # TODO: Better heuristic is likely to use the bone weights themselves (missing or all zero -> armature space).
        flver.refresh_bone_bounding_boxes(in_local_space=self.BoneDataType.EDIT)

        # Refresh `FLVERMesh` and FLVER-wide bounding boxes.
        # TODO: Partially redundant since splitter does this for meshes automatically. Only need FLVER-wide bounds.
        flver.refresh_bounding_boxes()

        # Should be called in `finally` block by caller anyway.
        self.clear_temp_flver()

        return flver

    def export_flver_meshes(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        flver: FLVER,
        bl_bone_names: list[str],
        use_chr_layout: bool,
        normal_tangent_dot_max: float,
        create_lod_face_sets: bool,
        matdefs: list[MatDef],
        texture_collection: DDSTextureCollection,
        using_default_bone: bool,
    ):
        """
        Construct a `MergedMesh` from Blender data, in a straightforward way (unfortunately using `for` loops over
        vertices, faces, and loops), then split it into `FLVERMesh` instances based on Blender materials.

        Also creates `Material` and `VertexArrayLayout` instances for each Blender material, and assigns them to the
        appropriate `FLVERMesh` instances. Any duplicate instances here will be merged when FLVER is packed.
        """
        settings = operator.settings(context)

        # 1. Create per-mesh info. Note that every Blender material index is guaranteed to be mapped to AT LEAST ONE
        #    split `FLVERMesh` in the exported FLVER (more if mesh bone maximum is exceeded). This allows the user to
        #    also split their meshes manually in Blender, if they wish.
        split_mesh_defs = []  # type: list[SplitMeshDef]

        bl_materials = self.get_materials()

        if settings.is_game(DEMONS_SOULS):
            # Use absolute texture path prefix, featuring model stem.
            texture_path_prefix = f"N:\\DemonsSoul\\data\\Model\\chr\\{self.export_name}\\tex\\"
        else:
            # Paths in later games are just naked file names.
            texture_path_prefix = ""

        for matdef, bl_material in zip(matdefs, bl_materials, strict=True):
            bl_material: BlenderFLVERMaterial
            split_mesh_def = bl_material.to_split_mesh_def(
                operator,
                context,
                create_lod_face_sets,
                matdef,
                use_chr_layout,
                texture_collection,
                texture_path_prefix,
            )
            split_mesh_defs.append(split_mesh_def)

        # 2. Validate UV layers: ensure all required material UV layer names are present, and warn if any unexpected
        #    Blender UV layers are present.
        bl_uv_layer_names = self.mesh.data.uv_layers.keys()
        remaining_bl_uv_layer_names = set(bl_uv_layer_names)
        used_uv_layer_names = set()
        for matdef, bl_material in zip(matdefs, self.mesh.data.materials):
            for used_layer in matdef.get_used_uv_layers():
                if used_layer.name not in bl_uv_layer_names:
                    raise FLVERExportError(
                        f"Material '{bl_material.name}' with def '{matdef.name}' (shader '{matdef.shader_stem}') "
                        f"requires UV layer '{used_layer.name}', which is missing in Blender."
                    )
                if used_layer.name in remaining_bl_uv_layer_names:
                    remaining_bl_uv_layer_names.remove(used_layer.name)
                used_uv_layer_names.add(used_layer.name)
        for remaining_bl_uv_layer_name in remaining_bl_uv_layer_names:
            operator.warning(
                f"UV layer '{remaining_bl_uv_layer_name}' is present in Blender mesh '{self.mesh.name}' but is not "
                f"used by any FLVER material shader. Ignoring it."
            )

        # 3. Create a triangulated copy of the mesh, so the user doesn't have to triangulate it themselves (though they
        #  may want to do this anyway for absolute approval of the final asset). Materials are copied over. Nothing else
        #  needs to be copied, as it is either done automatically by triangulation (e.g. UVs, vertex colors) or is part
        #  of the unchanged vertex data (e.g. bone weights) in the original mesh.
        tri_mesh_data = self.create_triangulated_mesh(context, do_data_transfer=False)

        # 4. Construct arrays from Blender data and pass into a new `MergedMesh` for splitting.

        # Slow part number 1: iterating over every Blender vertex to retrieve its position and bone weights/indices.
        # We at least know the size of the array in advance.
        vertex_count = len(tri_mesh_data.vertices)
        if not use_chr_layout and flver.version.map_pieces_use_normal_w_bones():
            # Bone weights/indices not in array. `normal_w` is used for single Map Piece bone.
            vertex_data_dtype = [
                ("position", "f", 3),
            ]
            use_normal_w_bone_index = True
        else:
            # Rigged FLVERs and older games' Map Pieces.
            vertex_data_dtype = [
                ("position", "f", 3),  # TODO: support 4D position (see, e.g., Rykard slime in ER: c4711)
                ("bone_weights", "f", 4),
                ("bone_indices", "i", 4),
            ]
            use_normal_w_bone_index = False

        vertex_data = np.empty(vertex_count, dtype=vertex_data_dtype)
        vertex_positions = np.empty((vertex_count, 3), dtype=np.float32)
        self.mesh.data.vertices.foreach_get("co", vertex_positions.ravel())
        vertex_bone_weights = np.zeros((vertex_count, 4), dtype=np.float32)  # default: 0.0
        vertex_bone_indices = np.full((vertex_count, 4), -1, dtype=np.int32)  # default: -1

        # Map bone names to their indices now to avoid `index()` calls in the loop.
        bone_name_indices = {bone_name: i for i, bone_name in enumerate(bl_bone_names)}
        # Map group indices to group objects for bone weights.
        vertex_groups_dict = {group.index: group for group in self.mesh.vertex_groups}
        no_bone_warning_done = False
        used_bone_indices = set()  # for marking unused bones in FLVER

        p = time.perf_counter()

        # Unfortunately, there is no way to retrieve the weighted bones of vertices without iterating over all vertices.
        # We iterate over the original, non-triangulated mesh, as the vertices should be the same and these vertices
        # have their bone vertex groups (which cannot easily be transferred to the triangulated copy).
        for i, vertex in enumerate(self.mesh.data.vertices):
            bone_indices = []  # global (splitter will make them local to mesh if appropriate)
            bone_weights = []
            for vertex_group in vertex.groups:  # only one for Map Pieces; max of 4 for other FLVER types
                mesh_group = vertex_groups_dict[vertex_group.group]
                try:
                    bone_index = bone_name_indices[mesh_group.name]
                except ValueError:
                    raise FLVERExportError(f"Vertex is weighted to invalid bone name: '{mesh_group.name}'.")
                bone_indices.append(bone_index)
                used_bone_indices.add(bone_index)
                # We don't waste time calling retrieval method `weight()` for map pieces.
                if use_chr_layout:
                    # TODO: `vertex_group` has `group` (int) and `weight` (float) on it already?
                    bone_weights.append(mesh_group.weight(i))

            if len(bone_indices) > 4:
                raise FLVERExportError(
                    f"Vertex {i} cannot be weighted to {len(bone_indices)} bones (max 1 for Map Pieces, 4 for others)."
                )
            elif len(bone_indices) == 0:
                if len(bl_bone_names) == 1 and not use_chr_layout:
                    # Omitted bone indices can be assumed to be the only bone in the skeleton.
                    # We issue a warning (once) unless this FLVER export is using a default bone (no Armature), in which
                    # case we obviously don't expect any vertices to be weighted to anything.
                    if not using_default_bone and not no_bone_warning_done:
                        operator.warning(
                            f"WARNING: At least one vertex in mesh '{self.mesh.name}' is not weighted to any bones. "
                            f"Weighting in 'Map Piece' mode to only bone in skeleton: '{bl_bone_names[0]}'"
                        )
                        no_bone_warning_done = True
                    bone_indices = [0]  # padded out below
                    used_bone_indices.add(0)
                    # Leave weights as zero.
                else:
                    # Can't guess which bone to weight to. Raise error.
                    raise FLVERExportError("Vertex is not weighted to any bones (cannot guess from multiple bones).")

            if use_chr_layout:
                # Pad out bone weights and (unused) indices for rigged meshes.
                while len(bone_weights) < 4:
                    bone_weights.append(0.0)
                while len(bone_indices) < 4:
                    # NOTE: we use -1 here to optimize the mesh splitting process; it will be changed to 0 for write.
                    bone_indices.append(-1)
            else:  # Map Pieces
                if len(bone_indices) == 1:
                    # Duplicate single-element list to four-element list.
                    # (This is done even for games that will write only a single Map Piece bone to `normal_w`.)
                    bone_indices *= 4
                else:
                    raise FLVERExportError(f"Non-CHR FLVER vertices must be weighted to exactly one bone (vertex {i}).")

            vertex_bone_indices[i] = bone_indices
            if bone_weights:  # rigged only
                vertex_bone_weights[i] = bone_weights

        for used_bone_index in used_bone_indices:
            flver.bones[used_bone_index].usage_flags &= ~1
            if settings.is_game("ELDEN_RING"):  # TODO: Probably started in an earlier game.
                flver.bones[used_bone_index].usage_flags |= 8

        vertex_data["position"] = vertex_positions
        if "bone_weights" in vertex_data.dtype.names:
            vertex_data["bone_weights"] = vertex_bone_weights
        if "bone_indices" in vertex_data.dtype.names:
            vertex_data["bone_indices"] = vertex_bone_indices

        operator.info(f"Constructed combined vertex array in {time.perf_counter() - p} s.")

        # NOTE: We now iterate over the faces of the triangulated copy. Material index has been properly triangulated.
        p = time.perf_counter()
        faces = np.empty((len(tri_mesh_data.polygons), 4), dtype=np.int32)
        # TODO: Again, due to the unfortunate need to access Python attributes one by one, we need a `for` loop.
        #  ...But, `foreach_get()` doesn't work for `loop_indices` and `material_index`?
        for i, face in enumerate(tri_mesh_data.polygons):
            # Since we've triangulated the mesh, no need to check face loop count here.
            faces[i] = [*face.loop_indices, face.material_index]

        operator.info(f"Constructed combined face array with {len(faces)} rows in {time.perf_counter() - p} s.")

        # Finally, we iterate over (triangulated) loops and construct their arrays. Note that loop UV and vertex color
        # data IS copied over during the triangulation. Obviously, we will just have more loops.
        p = time.perf_counter()
        loop_count = len(tri_mesh_data.loops)

        # TODO: Could check combined `dtype` now to skip any arrays not needed by ANY materials.

        # UV arrays correspond to FLVER-wide sorted UV layer names.
        # Default UV data is 0.0 (each material may only use a subset of UVs).
        loop_uv_array_dict = {
            uv_layer_name: np.zeros((loop_count, 2), dtype=np.float32)
            for uv_layer_name in used_uv_layer_names
        }

        # Retrieve vertex colors.
        # NOTE: Like UVs, it's extremely unlikely -- and probably untrue in any vanilla FLVER -- that NO FLVER material
        #  uses even one vertex color. In this case, though, the default black color generated here will simply never
        #  make it to any of the `MatDef`-based mesh array layouts after this.
        loop_color_arrays = []
        try:
            colors_layer_0 = tri_mesh_data.vertex_colors["VertexColors0"]
        except KeyError:
            operator.warning(f"FLVER mesh '{self.mesh.name}' has no 'VertexColors0' data layer. Using black.")
            colors_layer_0 = None
            # Default to black with alpha 1.
            black = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
            loop_color_arrays.append(np.tile(black, (loop_count, 1)))
        else:
            # Prepare for loop filling.
            loop_color_arrays.append(np.empty((loop_count, 4), dtype=np.float32))

        try:
            colors_layer_1 = tri_mesh_data.vertex_colors["VertexColors1"]
        except KeyError:
            # Fine. This mesh only uses one colors layer.
            colors_layer_1 = None
        else:
            # Prepare for loop filling.
            loop_color_arrays.append(np.empty((loop_count, 4), dtype=np.float32))
        # TODO: Check for arbitrary additional vertex colors? Or first, scan all layouts to check what's expected.

        loop_vertex_indices = np.empty(loop_count, dtype=np.int32)
        tri_mesh_data.loops.foreach_get("vertex_index", loop_vertex_indices)

        loop_normals = np.empty((loop_count, 3), dtype=np.float32)
        tri_mesh_data.loops.foreach_get("normal", loop_normals.ravel())
        if use_normal_w_bone_index:
            # New Map Pieces: single vertex bone index is stored in `normal_w` (as `uint8`).
            # TODO: Given that the default `normal_w` value in older games is 127, this may be signed, and so the max
            #  Map Piece bone count may actually be 127/128. Sticking with 256 for now.
            if (max_bone_index := vertex_bone_indices.max()) > 255:
                raise FLVERExportError(
                    f"Map Piece mode only supports up to 256 bones (8-bit index), not: {max_bone_index}"
                )
            loop_normals_w = vertex_bone_indices[:, 0][loop_vertex_indices].astype(np.uint8).reshape(-1, 1)
        else:
            # Rigged models or old Map Pieces: `normal_w` is unused and defaults to 127.
            loop_normals_w = np.full((loop_count, 1), 127, dtype=np.uint8)

        if colors_layer_0:
            colors_layer_0.data.foreach_get("color", loop_color_arrays[0].ravel())
        if colors_layer_1:
            colors_layer_1.data.foreach_get("color", loop_color_arrays[1].ravel())
        for uv_layer_name in used_uv_layer_names:
            uv_layer = tri_mesh_data.uv_layers[uv_layer_name]
            if len(uv_layer.data) == 0:
                raise FLVERExportError(f"UV layer {uv_layer.name} contains no data.")
            uv_layer.data.foreach_get("uv", loop_uv_array_dict[uv_layer_name].ravel())

        # 5. Calculate individual tangent arrays for each 'UVTexture*' UV layer.
        # TODO: Also need one for Bloodborne's 'UVBlood' layer.
        #  Maybe make the NON-tangent UVs start with name 'UVData_'...

        loop_tangent_arrays = []
        uv_texture_layer_names = sorted([
            name for name in bl_uv_layer_names
            if name.startswith("UVTexture")
            or use_chr_layout and name.startswith("UVBlood")
        ])
        for uv_name in uv_texture_layer_names:
            loop_tangents = self.get_tangents_for_uv_layer(
                operator, uv_name, loop_count, loop_normals, loop_uv_array_dict, tri_mesh_data,
            )
            loop_tangent_arrays.append(loop_tangents)

        # Assign second tangents array to bitangents in earlier games (DeS/DS1).
        # TODO: Not sure if DS2 uses bitangent field.
        # Bloodborne onwards properly use multiple tangent fields.
        if settings.is_game("DEMONS_SOULS", "DARK_SOULS_PTDE", "DARK_SOULS_DSR"):
            # Early games only support up to two tangent arrays, and put the second in "bitangent" vertex array data.
            if len(loop_tangent_arrays) > 2:
                operator.warning(
                    f"Game '{settings.game.name}' does not support more than two vertex tangent arrays (i.e. does not "
                    f"support more than two 'UVTexture#' UV layers). Only the first two tangent arrays will be used."
                )
            loop_bitangents = loop_tangent_arrays[1] if len(loop_tangent_arrays) > 1 else None
            loop_tangent_arrays = [loop_tangent_arrays[0]]
        else:
            # Later games support multiple vertex tangents and do not overload the bitangents.
            loop_bitangents = None

        operator.info(f"Constructed combined loop array in {time.perf_counter() - p} s.")

        merged_mesh_kwargs = dict(
            vertex_data=vertex_data,
            loop_vertex_indices=loop_vertex_indices,
            vertices_merged=True,
            loop_normals=loop_normals,
            loop_normals_w=loop_normals_w,
            loop_tangents=loop_tangent_arrays,
            loop_bitangents=loop_bitangents,
            loop_vertex_colors=loop_color_arrays,
            loop_uvs=loop_uv_array_dict,
            faces=faces,
        )

        merged_mesh = MergedMesh(**merged_mesh_kwargs)

        # Apply Blender -> FromSoft transformations.
        merged_mesh.swap_vertex_yz(tangents=True, bitangents=True)
        merged_mesh.invert_vertex_uv(invert_u=False, invert_v=True)

        p = time.perf_counter()
        flver.meshes = merged_mesh.split_mesh(
            split_mesh_defs,
            unused_bone_indices_are_minus_one=True,  # saves some time within the splitter (no ambiguous zeroes)
            normal_tangent_dot_threshold=normal_tangent_dot_max,
            **settings.get_game_split_mesh_kwargs(),
        )
        operator.info(f"Split Blender mesh into {len(flver.meshes)} FLVER meshes in {time.perf_counter() - p} s.")

    @classmethod
    def get_tangents_for_uv_layer(
        cls,
        operator: LoggingOperator,
        uv_name: str,
        loop_count: int,
        loop_normals: np.ndarray,
        loop_uvs: dict[str, np.ndarray],
        tri_mesh_data: bpy.types.Mesh,
    ) -> np.ndarray:
        try:
            tri_mesh_data.calc_tangents(uvmap=uv_name)
        except RuntimeError as ex:
            raise RuntimeError(
                f"Could not calculate vertex tangents from UV layer '{uv_name}'. "
                f"Make sure the mesh is triangulated and not empty (delete any empty mesh). Error: {ex}"
            )
        loop_tangents = np.empty((loop_count, 3), dtype=np.float32)
        tri_mesh_data.loops.foreach_get("tangent", loop_tangents.ravel())
        loop_tangents = np_cross(loop_tangents, loop_normals)
        # Add default `w` components to tangents and bitangents (-1). May be negated into 1 below.
        minus_one = np.full((loop_count, 1), -1, dtype=np.float32)
        loop_tangents = np.concatenate((loop_tangents, minus_one), axis=1)
        # We need to check the determinant of every face's loop UVs to determine if the tangent should be negated
        # due to mirrored UV mapping. Fortunately, we're already set up for vectorization here.
        loop_tangent_signs = cls.get_face_uv_tangent_signs(loop_uvs[uv_name])
        loop_tangents_reshaped = loop_tangents.reshape(-1, 3, 4)  # temporary reshape for easy negation
        loop_tangents_reshaped *= loop_tangent_signs[:, np.newaxis, np.newaxis]
        loop_tangents = loop_tangents_reshaped.reshape(-1, 4)
        operator.info(
            f"Detected {np.sum(loop_tangent_signs < 0)} / {loop_tangent_signs.size} face loops with mirrored UVs in "
            f"UV layer '{uv_name}' and negated their vertex tangents."
        )
        return loop_tangents

    @staticmethod
    def get_face_uv_tangent_signs(loop_uv_array: np.ndarray) -> np.ndarray:
        """Uses the determinant of the UV face to determine if the UV mapping is mirrored.

        Returns a 1D array matching face indices, with -1 indicating a mirrored face and 1 a non-mirrored face.
        """
        tangent_loop_uvs_reshaped = loop_uv_array.reshape(-1, 3, 2)  # every 3-row chunk now grouped by first dimension
        face_uv0 = tangent_loop_uvs_reshaped[:, 0, :]
        face_uv1 = tangent_loop_uvs_reshaped[:, 1, :]
        face_uv2 = tangent_loop_uvs_reshaped[:, 2, :]
        delta_u1 = face_uv1[:, 0] - face_uv0[:, 0]
        delta_v1 = face_uv1[:, 1] - face_uv0[:, 1]
        delta_u2 = face_uv2[:, 0] - face_uv0[:, 0]
        delta_v2 = face_uv2[:, 1] - face_uv0[:, 1]
        determinants = (delta_u1 * delta_v2) - (delta_u2 * delta_v1)
        return np.where(determinants < 0, -1, 1)

    def create_triangulated_mesh(self, context: bpy.types.Context, do_data_transfer: bool = False) -> bpy.types.Mesh:
        """Use `bmesh` and the Data Transfer Modifier to create a temporary triangulated copy of the mesh (required
        for FLVER models) that retains/interpolates critical information like custom split normals and vertex groups."""

        # Automatically triangulate the mesh.
        bm = bmesh.new()
        bm.from_mesh(self.mesh.data)
        bmesh.ops.triangulate(bm, faces=bm.faces, quad_method="BEAUTY", ngon_method="BEAUTY")
        tri_mesh_data = bpy.data.meshes.new("__TEMP_FLVER__")  # will be deleted during `finally` block of caller
        # Probably not necessary, but we copy material slots over, just case it causes `face.material_index` problems.
        for bl_mat in self.mesh.data.materials:
            tri_mesh_data.materials.append(bl_mat)
        bm.to_mesh(tri_mesh_data)
        bm.free()
        del bm

        # Create an object for the mesh so we can apply the Data Transfer modifier to it.
        # noinspection PyTypeChecker
        tri_mesh_obj = new_mesh_object("__TEMP_FLVER_OBJ__", tri_mesh_data)
        context.scene.collection.objects.link(tri_mesh_obj)

        if do_data_transfer:
            # Add the Data Transfer Modifier to the triangulated mesh object.
            # TODO: This requires the new triangulated mesh to EXACTLY overlap the original mesh, so we should set its
            #  transform. (Any parent offsets will be hard to deal with, though...)
            # noinspection PyTypeChecker
            data_transfer_mod = tri_mesh_obj.modifiers.new(
                name="__TEMP_FLVER_DATA_TRANSFER__", type="DATA_TRANSFER"
            )  # type: bpy.types.DataTransferModifier
            data_transfer_mod.object = self.mesh
            # Enable custom normal data transfer and set the appropriate options.
            data_transfer_mod.use_loop_data = True
            data_transfer_mod.data_types_loops = {"CUSTOM_NORMAL"}
            if len(tri_mesh_data.loops) == len(self.mesh.data.loops):
                # Triangulation did not change the number of loops, so we can map custom normals directly.
                # TODO: Do I even need to transfer any data? I think the triangulation will have done it all.
                data_transfer_mod.loop_mapping = "TOPOLOGY"
            else:
                data_transfer_mod.loop_mapping = "NEAREST_POLYNOR"  # best for simple triangulation
            # Apply the modifier.
            bpy.context.view_layer.objects.active = tri_mesh_obj  # set the triangulated mesh as active
            bpy.ops.object.modifier_apply(modifier=data_transfer_mod.name)

        # Return the mesh data.
        return tri_mesh_obj.data

    def create_flver_bones(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        armature: bpy.types.ArmatureObject,
        read_bone_type: BoneDataType,
    ) -> tuple[list[FLVERBone], list[str], list[tuple[Vector3, Matrix3, Vector3]]]:
        """Create `FLVER` bones from Blender `armature` bones and get their armature space transforms.

        Bone transform data may be read from either EDIT mode (typical for characters and objects) or POSE mode (typical
        for map pieces). This is inferred from all materials and specified by `read_bone_type`.
        """

        # We need `EditBone` mode to retrieve custom properties, even if reading the actual transforms from pose later.
        # TODO: Still true for extension properties?
        context.view_layer.objects.active = armature
        operator.to_edit_mode()

        edit_bone_names = [edit_bone.name for edit_bone in armature.data.edit_bones]

        game_bones = []
        game_bone_parent_indices = []  # type: list[int]
        game_arma_transforms = []  # type: list[tuple[Vector3, Matrix3, Vector3]]  # translate, rotate matrix, scale

        if len(set(edit_bone_names)) != len(edit_bone_names):
            raise FLVERExportError("Bone names in Blender Armature are not all unique.")

        export_settings = context.scene.flver_export_settings

        for edit_bone in armature.data.edit_bones:

            if edit_bone.name not in edit_bone_names:
                continue  # ignore this bone (e.g. c0000 bones not used by equipment FLVER being exported)

            game_bone_name = edit_bone.name
            while re.match(r".*\.\d\d\d$", game_bone_name):
                # Bone names can be repeated in the FLVER. Remove Blender duplicate suffixes.
                game_bone_name = game_bone_name[:-4]
            while game_bone_name.endswith(" <DUPE>"):
                # Bone names can be repeated in the FLVER.
                game_bone_name = game_bone_name.removesuffix(" <DUPE>")

            bone_usage_flags = edit_bone.FLVER_BONE.get_flags()
            if (bone_usage_flags & FLVERBoneUsageFlags.UNUSED) != 0 and bone_usage_flags != 1:
                raise FLVERExportError(
                    f"Bone '{edit_bone.name}' has 'Is Unused' enabled, but also has other usage flags set!"
                )
            game_bone = FLVERBone(name=game_bone_name, usage_flags=bone_usage_flags)

            if edit_bone.parent:
                parent_bone_name = edit_bone.parent.name
                parent_bone_index = edit_bone_names.index(parent_bone_name)
            else:
                parent_bone_index = -1

            if read_bone_type == self.BoneDataType.EDIT:
                # Get armature-space bone transform from rigged `EditBone` (characters and objects, typically).
                bl_translate = edit_bone.matrix.translation
                bl_rotmat = edit_bone.matrix.to_3x3()  # get rotation submatrix
                game_arma_translate = BL_TO_GAME_VECTOR3(bl_translate)
                game_arma_rotmat = BL_TO_GAME_MAT3(bl_rotmat)
                s = edit_bone.length / export_settings.base_edit_bone_length
                # NOTE: only uniform scale is supported for these "is_bind_pose" mesh bones
                game_arma_scale = s * Vector3.one()
                game_arma_transforms.append((game_arma_translate, game_arma_rotmat, game_arma_scale))

            game_bones.append(game_bone)
            game_bone_parent_indices.append(parent_bone_index)

        # Assign game bone parent references. Child and sibling bones are done by caller using FLVER method.
        for game_bone, parent_index in zip(game_bones, game_bone_parent_indices):
            game_bone.parent_bone = game_bones[parent_index] if parent_index >= 0 else None

        operator.to_object_mode()

        if read_bone_type == self.BoneDataType.POSE:
            # Get armature-space bone transform from PoseBone (map pieces).
            # Note that non-uniform bone scale is supported here (and is actually used in some old vanilla map pieces).
            for game_bone, bl_bone_name in zip(game_bones, edit_bone_names):

                pose_bone = self.armature.pose.bones[bl_bone_name]

                game_arma_translate = BL_TO_GAME_VECTOR3(pose_bone.location)
                if pose_bone.rotation_mode == "QUATERNION":
                    bl_rot_quat = pose_bone.rotation_quaternion
                    bl_rotmat = bl_rot_quat.to_matrix()
                    game_arma_rotmat = BL_TO_GAME_MAT3(bl_rotmat)
                elif pose_bone.rotation_mode == "XYZ":
                    # TODO: Could this cause the same weird Blender gimbal lock errors as I was seeing with characters?
                    #  If so, I may want to make sure I always set pose bone rotation to QUATERNION mode.
                    bl_rot_euler = pose_bone.rotation_euler
                    bl_rotmat = bl_rot_euler.to_matrix()
                    game_arma_rotmat = BL_TO_GAME_MAT3(bl_rotmat)
                else:
                    raise FLVERExportError(
                        f"Unsupported rotation mode '{pose_bone.rotation_mode}' for bone '{pose_bone.name}'. Must be "
                        f"'QUATERNION' or 'XYZ' (Euler)."
                    )
                game_arma_scale = BL_TO_GAME_VECTOR3(pose_bone.scale)  # can be non-uniform
                game_arma_transforms.append(
                    (
                        game_arma_translate,
                        game_arma_rotmat,
                        game_arma_scale,
                    )
                )

        return game_bones, edit_bone_names, game_arma_transforms

    def guess_read_bone_type(self, operator: LoggingOperator = None) -> BoneDataType:
        """Detect whether bone data should be read from EditBones or PoseBones.

        TODO: Best hack I can come up with, currently. I'm still not 100% sure if it's safe to assume that Mesh
         `is_bind_pose` is consistent (or SHOULD be consistent) across all meshes in a single FLVER. Objects in
         particular could possibly lie somewhere between map pieces (False) and characters (True). This would only be
         possible to represent in Blender if such meshes do NOT share any bones (and still a pain then).
        """
        read_bone_type = self.BoneDataType.NONE
        warn_partial_bind_pose = False
        for bl_material in self.mesh.data.materials:
            if bl_material.FLVER_MATERIAL.is_bind_pose:  # typically: characters, objects, parts
                if not read_bone_type:
                    read_bone_type = self.BoneDataType.EDIT  # write bone transforms from EditBones
                elif read_bone_type == self.BoneDataType.POSE:
                    warn_partial_bind_pose = True
                    read_bone_type = self.BoneDataType.EDIT
                    break
            else:  # typically: map pieces
                if not read_bone_type:
                    read_bone_type = self.BoneDataType.POSE  # write bone transforms from PoseBones
                elif read_bone_type == self.BoneDataType.EDIT:
                    warn_partial_bind_pose = True
                    break  # keep EDIT default
        if operator and warn_partial_bind_pose:
            operator.warning(
                f"Some materials in FLVER '{self.name}' use `Is Bind Pose = True` (bone data written to EditBones in "
                f"Blender; typical for objects/characters) and some do not (bone data written to PoseBones in Blender; "
                f"typical for map pieces). Soulstruct will read all bone data from EditBones for export."
            )
        return read_bone_type

    @classmethod
    def get_selected_flver(cls, context: bpy.types.Context) -> BlenderFLVER:
        """Get the Mesh and (optional) Armature components of a single selected FLVER object of either type."""
        if not context.selected_objects:
            raise FLVERError("No FLVER Mesh or Armature selected.")
        elif len(context.selected_objects) > 1:
            raise FLVERError("Multiple objects selected. Exactly one FLVER Mesh or Armature must be selected.")
        _, mesh = cls.parse_flver_obj(context.selected_objects[0])
        return cls(mesh)

    @classmethod
    def get_selected_flvers(cls, context: bpy.types.Context) -> list[BlenderFLVER]:
        """Get the Mesh and (optional) Armature components of ALL selected FLVER objects of either type."""
        if not context.selected_objects:
            raise SoulstructTypeError("No FLVER Meshes or Armatures selected.")
        flvers = []
        for obj in context.selected_objects:
            _, mesh = cls.parse_flver_obj(obj)
            flvers.append(cls(mesh))
        return flvers

    @classmethod
    def test_obj(cls, obj: bpy.types.Object) -> bool:
        try:
            cls.from_armature_or_mesh(obj)
        except SoulstructTypeError:
            return False
        return True

    @staticmethod
    def parse_flver_obj(obj: bpy.types.Object) -> tuple[bpy.types.ArmatureObject | None, bpy.types.MeshObject]:
        """Parse a Blender object into a Mesh and (optional) Armature object."""
        if obj.type == "MESH" and obj.soulstruct_type == SoulstructType.FLVER:
            mesh = obj
            armature = mesh.parent if mesh.parent is not None and mesh.parent.type == "ARMATURE" else None
        elif obj.type == "ARMATURE":
            armature = obj
            mesh_children = [child for child in armature.children if child.type == "MESH"]
            if not mesh_children or mesh_children[0].soulstruct_type != SoulstructType.FLVER:
                raise SoulstructTypeError(
                    f"Armature '{armature.name}' has no FLVER Mesh child. Please create it, even if empty, and set its "
                    f"Soulstruct object type to FLVER using the General Settings panel."
                )
            mesh = mesh_children[0]
        else:
            raise SoulstructTypeError(
                f"Given object '{obj.name}' is not a FLVER Mesh or Armature parent of such. Cannot parse as FLVER."
            )

        # noinspection PyTypeChecker
        return armature, mesh

    @staticmethod
    def clear_temp_flver():
        try:
            bpy.data.objects.remove(bpy.data.objects["__TEMP_FLVER_OBJ__"])
        except KeyError:
            pass

        try:
            bpy.data.meshes.remove(bpy.data.meshes["__TEMP_FLVER__"])
        except KeyError:
            pass

    # endregion


BlenderFLVER.add_auto_type_props(*BlenderFLVER.AUTO_FLVER_PROPS)
