from __future__ import annotations

__all__ = [
    "BlenderFLVER",
    "BlenderFLVERDummy",
]

import re
import typing as tp

import bpy
from mathutils import Matrix, Vector

from soulstruct.base.models.flver import FLVER, Dummy, Version
from soulstruct.utilities.maths import Vector3
from soulstruct.utilities.text import natural_keys

from io_soulstruct.exceptions import FLVERError
from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities import (
    LoggingOperator, remove_dupe_suffix, new_mesh_object, new_armature_object, new_empty_object, copy_obj_property_group
)
from io_soulstruct.utilities.conversion import GAME_TO_BL_VECTOR, game_forward_up_vectors_to_bl_euler
from .properties import *

if tp.TYPE_CHECKING:
    from io_soulstruct.general import SoulstructSettings, GAME_CONFIG


class BlenderFLVERDummy:

    obj: bpy.types.Object

    # Captures anything else after the `[reference_id]` in name, including Blender dupe suffix like '.001'.
    DUMMY_NAME_RE: tp.ClassVar[re.Pattern] = re.compile(
        r"^(?P<model_name>.+)? *[Dd]ummy(?P<index><\d+>)? *(?P<reference_id>\[\d+\]) *(\.\d+)?$"
    )

    def __init__(self, obj: bpy.types.Object):
        if obj.type != "EMPTY":
            raise TypeError(f"Wrapped FLVER Dummy object in Blender must be an Empty, not a {obj.type}.")
        self.obj = obj
    
    @classmethod
    def new_from_dummy(
        cls,
        model_name: str,
        index: int,
        dummy: Dummy,
        armature: bpy.types.ArmatureObject,
    ) -> BlenderFLVERDummy:
        """Create a wrapped Blender Dummy empty object from FLVER `Dummy`.
        
        Created Dummy will be parented to `Armature` via its attach bone index, and will also record its internal parent
        bone (for its space).
        """
        name = cls._format_name(model_name, index, dummy.reference_id, suffix=None)
        obj = bpy.data.objects.new(name, None)  # empty
        obj.soulstruct_type = SoulstructType.DUMMY

        # noinspection PyTypeChecker
        bl_dummy = cls(obj)
        bl_dummy.color_rgba = dummy.color_rgba
        bl_dummy.flag_1 = dummy.flag_1
        bl_dummy.use_upward_vector = dummy.use_upward_vector
        bl_dummy.unk_x30 = dummy.unk_x30
        bl_dummy.unk_x34 = dummy.unk_x34
        
        bl_dummy.parent = armature
        # Default appearance:
        bl_dummy.empty_display_type = "ARROWS"  # best display type/size I've found (single arrow not sufficient)
        bl_dummy.empty_display_size = 0.05
        
        if dummy.use_upward_vector:
            bl_rotation_euler = game_forward_up_vectors_to_bl_euler(dummy.forward, dummy.upward)
        else:  # TODO: I assume this is right (up-ignoring dummies only rotate around vertical axis)
            bl_rotation_euler = game_forward_up_vectors_to_bl_euler(dummy.forward, Vector3((0, 1, 0)))

        if dummy.parent_bone_index != -1:
            # Bone's FLVER translate is in the space of (i.e. relative to) this parent bone.
            # NOTE: This is NOT the same as the 'attach' bone, which is used as the actual Blender parent and
            # controls how the dummy moves during armature animations.
            bl_dummy.parent_bone = armature.data[dummy.parent_bone_index]
            bl_parent_bone_matrix = armature.data[dummy.parent_bone_index].matrix_local
            bl_location = bl_parent_bone_matrix @ GAME_TO_BL_VECTOR(dummy.translate)
        else:
            # Bone's location is in armature space. Leave `parent_bone` as None.
            bl_location = GAME_TO_BL_VECTOR(dummy.translate)

        # Dummy moves with this bone during animations.
        if dummy.attach_bone_index != -1:
            # Set true Blender parent.
            bl_dummy.obj.parent_bone = armature.data[dummy.attach_bone_index]
            bl_dummy.parent_type = "BONE"

        # We need to set the dummy's world matrix, rather than its local matrix, to bypass its possible bone
        # attachment above.
        bl_dummy.matrix_world = Matrix.LocRotScale(bl_location, bl_rotation_euler, Vector((1.0, 1.0, 1.0)))
        
        return bl_dummy

    @property
    def name(self):
        return self.obj.name

    @name.setter
    def name(self, value):
        raise ValueError(
            "Cannot set name of FLVER Dummy object directly. Use `model_name`, `index`, and `reference_id` properties."
        )

    @property
    def flver_dummy(self) -> FLVERDummyProps:
        return self.obj.flver_dummy

    # region Properties

    @property
    def parent_bone(self) -> bpy.types.Bone | None:
        return self.obj.flver_dummy.parent_bone

    @parent_bone.setter
    def parent_bone(self, value: bpy.types.Bone | None):
        self.obj.flver_dummy.parent_bone = value

    @property
    def color_rgba(self) -> tuple[int, int, int, int]:
        return self.obj.flver_dummy.color_rgba

    @color_rgba.setter
    def color_rgba(self, value: tuple[int, int, int, int]):
        self.obj.flver_dummy.color_rgba = value

    @property
    def flag_1(self) -> bool:
        return self.obj.flver_dummy.flag_1

    @flag_1.setter
    def flag_1(self, value: bool):
        self.obj.flver_dummy.flag_1 = value

    @property
    def use_upward_vector(self) -> bool:
        return self.obj.flver_dummy.use_upward_vector

    @use_upward_vector.setter
    def use_upward_vector(self, value: bool):
        self.obj.flver_dummy.use_upward_vector = value

    @property
    def unk_x30(self) -> int:
        return self.obj.flver_dummy.unk_x30

    @unk_x30.setter
    def unk_x30(self, value: int):
        self.obj.flver_dummy.unk_x30 = value

    @property
    def unk_x34(self) -> int:
        return self.obj.flver_dummy.unk_x34

    @unk_x34.setter
    def unk_x34(self, value: int):
        self.obj.flver_dummy.unk_x34 = value

    # endregion

    # region Dummy Name Components

    @staticmethod
    def _format_name(
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
        self.name = self._format_name(
            model_name=value,
            index=int(match.group(2)[1:-1]) if match.group(2) is not None else None,
            reference_id=int(match.group(3)[1:-1]),
            suffix=match.group(4),
        )

    def set_index(self, index: int):
        match = self.DUMMY_NAME_RE.match(self.name)
        if match is None:
            raise ValueError(f"FLVER Dummy object name does not match expected pattern: {self.name}")
        self.name = self._format_name(
            model_name=match.group(1),
            index=index,
            reference_id=int(match.group(3)[1:-1]),
            suffix=match.group(4),
        )

    @property
    def reference_id(self) -> int:
        match = self.DUMMY_NAME_RE.match(self.name)
        if match is None:
            raise ValueError(f"FLVER Dummy object name does not match expected pattern: {self.name}")
        try:
            return int(match.group(3))
        except ValueError:
            raise ValueError(f"FLVER Dummy object name does not match expected pattern: {self.name}")

    @reference_id.setter
    def reference_id(self, value: int):
        match = self.DUMMY_NAME_RE.match(self.name)
        if match is None:
            raise ValueError(f"FLVER Dummy object name does not match expected pattern: {self.name}")
        self.name = self._format_name(
            model_name=match.group(1),
            index=int(match.group(2)[1:-1]) if match.group(2) else None,
            reference_id=value,
            suffix=match.group(4),
        )

    # endregion


class BlenderFLVER:
    """Wrapper for a Blender object hierarchy that represents a `FLVER` model.

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

    armature: bpy.types.ArmatureObject | None  # optional for models with one entirely default bone (most Map Pieces)
    mesh: bpy.types.MeshObject

    def __init__(self, armature: bpy.types.ArmatureObject | None, mesh: bpy.types.MeshObject):
        self.armature = armature
        self.mesh = mesh

    @classmethod
    def from_bl_obj(cls, obj: bpy.types.Object, operator: LoggingOperator | None = None):
        armature, mesh = cls.parse_flver_obj(obj)
        if mesh.soulstruct_type != SoulstructType.FLVER:
            raise FLVERError(f"Selected object '{obj.name}' is not a FLVER model. (It may be an MSB Part only.)")

        if armature:
            armature_stem = armature.name.split(".")[0].split(" ")[0]
            mesh_stem = mesh.name.split(".")[0].split(" ")[0]
            if armature_stem != mesh_stem:
                operator.warning(f"Armature '{armature.name}' and Mesh '{mesh.name}' do not share a FLVER stem.")

        return cls(armature, mesh)

    def get_dummies(self, operator: LoggingOperator | None = None) -> list[BlenderFLVERDummy]:
        """Find all FLVER Dummy (empty children of root object with expected name).

        If `operator` is provided, warnings will be logged for any Empty children that do not match the expected name
        pattern.
        """
        dummies = []
        for child in self.root_obj.children:
            if child.type != "EMPTY":
                continue
            if BlenderFLVERDummy.DUMMY_NAME_RE.match(child.name):
                dummies.append(BlenderFLVERDummy(child))
            elif operator:
                operator.warning(f"Ignoring FLVER Empty child with non-Dummy name: '{child.name}'")
        return sorted(dummies, key=lambda d: natural_keys(d.name))

    def rename(self, new_name: str, old_name=""):
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

        old_name = old_name or self.flver_stem

        if self.armature:
            if self.armature.data.name == self.armature.name:
                # Source model. Rename Armature data-block.
                self.armature.data.name = new_name
                self.mesh.data.name = f"{new_name} Mesh"
            self.armature.name = new_name
            self.mesh.name = f"{new_name} Mesh"
        else:
            if self.mesh.data.name == self.mesh.name:
                # Source model. Rename Mesh data-block.
                self.mesh.data.name = new_name
            self.mesh.name = new_name

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

    def duplicate(
        self,
        context: bpy.types.Context,
        collections: list[bpy.types.Collection] = None,
        copy_pose=False,
    ):
        """Duplicate ALL objects, data-blocks, and materials of this FLVER model to a new one.

        Nothing is renamed; the caller can do that as desired. By default, names of new objects/data-blocks will
        obviously gain Blender '.001' dupe suffixes, but `.rename()` will remove these.
        """
        collections = collections or [context.scene.collection]

        # noinspection PyTypeChecker
        new_mesh_obj = new_mesh_object(self.mesh.name, self.mesh.data.copy())
        new_mesh_obj.soulstruct_type = SoulstructType.FLVER
        copy_obj_property_group(self.mesh, new_mesh_obj, "flver")
        for collection in collections:
            collection.objects.link(new_mesh_obj)

        # Duplicate materials.
        for i, mat in enumerate(tuple(new_mesh_obj.data.materials)):
            new_mesh_obj.data.materials[i] = mat.copy()

        new_armature_obj = None
        if self.armature:
            new_armature_obj = new_armature_object(self.armature.name, data=self.armature.data.copy())
            for collection in collections:
                collection.objects.link(new_armature_obj)
            # No properties taken from Armature.
            context.view_layer.objects.active = new_armature_obj

            if copy_pose:
                # Copy pose bone transforms.
                context.view_layer.update()  # need Blender to create `linked_armature_obj.pose` now
                for pose_bone in new_armature_obj.pose.bones:
                    source_bone = self.armature.pose.bones[pose_bone.name]
                    pose_bone.rotation_mode = "QUATERNION"  # should be default but being explicit
                    pose_bone.location = source_bone.location
                    pose_bone.rotation_quaternion = source_bone.rotation_quaternion
                    pose_bone.scale = source_bone.scale

            new_mesh_obj.parent = new_armature_obj
            if bpy.ops.object.select_all.poll():
                bpy.ops.object.select_all(action="DESELECT")
            # Create Armature modifier on Mesh.
            new_mesh_obj.select_set(True)
            context.view_layer.objects.active = new_mesh_obj
            bpy.ops.object.modifier_add(type="ARMATURE")
            armature_mod = new_mesh_obj.modifiers["Armature"]
            armature_mod.object = new_armature_obj
            armature_mod.show_in_editmode = True
            armature_mod.show_on_cage = True

            for dummy in self.get_dummies():
                new_dummy_obj = new_empty_object(dummy.name)
                new_dummy_obj.soulstruct_type = SoulstructType.DUMMY
                copy_obj_property_group(dummy.obj, new_dummy_obj, "flver_dummy")
                new_dummy_obj.parent = new_armature_obj
                for collection in collections:
                    collection.objects.link(new_dummy_obj)

        return self.__class__(new_armature_obj, new_mesh_obj)

    @property
    def root_obj(self) -> bpy.types.ArmatureObject | bpy.types.MeshObject:
        """Get root object of FLVER model, which is either the Armature (if present) or the Mesh."""
        return self.armature or self.mesh

    @property
    def flver_props(self) -> FLVERObjectProps:
        # noinspection PyUnresolvedReferences
        return self.root_obj.flver

    @property
    def name(self):
        return self.root_obj.name

    @name.setter
    def name(self, value: str):
        if self.armature:
            self.armature.name = value
            self.mesh.name = f"{value} Mesh"
        else:
            self.mesh.name = value

    @property
    def flver_stem(self):
        return self.name.split(".")[0].split(" ")[0]

    def to_empty_flver(self, settings: SoulstructSettings) -> FLVER:
        """Create a new `FLVER` with header properties set only."""
        props = self.flver_props

        if props.version == "DEFAULT":
            # Default is game-dependent.
            game = settings.game
            try:
                version = GAME_CONFIG[game].flver_default_version
            except KeyError:
                raise ValueError(
                    f"Do not know default FLVER Version for game {game}. You must set 'Version' yourself on FLVER "
                    f"object '{self.name}' before exporting."
                )
        else:
            try:
                version = Version[props.version]
            except KeyError:
                raise ValueError(f"Invalid FLVER Version: '{props.version}'. Please report this bug to Grimrukh!")

        # TODO: Any other guessable game fields?
        return FLVER(
            big_endian=props.big_endian,
            version=version,
            unicode=props.unicode,
            unk_x4a=props.unk_x4a,
            unk_x4c=props.unk_x4c,
            unk_x5c=props.unk_x5c,
            unk_x5d=props.unk_x5d,
            unk_x68=props.unk_x68,
        )

    def guess_bone_read_type(self, operator: LoggingOperator = None) -> str:
        """Detect whether bone data should be read from EditBones or PoseBones.

        TODO: Best hack I can come up with, currently. I'm still not 100% sure if it's safe to assume that Submesh
         `is_bind_pose` is consistent (or SHOULD be consistent) across all submeshes in a single FLVER. Objects in
         particular could possibly lie somewhere between map pieces (False) and characters (True).
        """
        read_bone_type = ""
        warn_partial_bind_pose = False
        for bl_material in self.mesh.data.materials:
            if bl_material.flver_material.is_bind_pose:  # typically: characters, objects, parts
                if not read_bone_type:
                    read_bone_type = "EDIT"  # write bone transforms from EditBones
                elif read_bone_type == "POSE":
                    warn_partial_bind_pose = True
                    read_bone_type = "EDIT"
                    break
            else:  # typically: map pieces
                if not read_bone_type:
                    read_bone_type = "POSE"  # write bone transforms from PoseBones
                elif read_bone_type == "EDIT":
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
    def get_selected_flver(cls, context) -> BlenderFLVER:
        """Get the Mesh and (optional) Armature components of a single selected FLVER object of either type."""
        if not context.selected_objects:
            raise FLVERError("No FLVER Mesh or Armature selected.")
        elif len(context.selected_objects) > 1:
            raise FLVERError("Multiple objects selected. Exactly one FLVER Mesh or Armature must be selected.")
        obj = context.selected_objects[0]
        return cls.from_bl_obj(obj)

    @classmethod
    def get_selected_flvers(cls, context) -> list[BlenderFLVER]:
        """Get the Mesh and (optional) Armature components of ALL selected FLVER objects of either type."""
        if not context.selected_objects:
            raise FLVERError("No FLVER Meshes or Armatures selected.")
        return [cls.from_bl_obj(obj) for obj in context.selected_objects]

    @classmethod
    def test_obj(cls, obj: bpy.types.Object):
        try:
            cls.from_bl_obj(obj)
        except FLVERError:
            return False
        return True

    @staticmethod
    def parse_flver_obj(obj: bpy.types.Object) -> tuple[bpy.types.ArmatureObject | None, bpy.types.MeshObject]:
        """Parse a Blender object into a Mesh and (optional) Armature object."""
        if obj.type == "MESH":
            mesh = obj
            armature = mesh.parent if mesh.parent is not None and mesh.parent.type == "ARMATURE" else None
        elif obj.type == "ARMATURE":
            armature = obj
            mesh_name = f"{obj.name} Mesh"
            mesh_children = [child for child in armature.children if child.type == "MESH" and child.name == mesh_name]
            if not mesh_children:
                raise FLVERError(
                    f"Armature '{armature.name}' has no Mesh child '{mesh_name}'. Please create it, even if empty, "
                    f"and assign it any required FLVER custom properties such as 'Version', 'Unicode', etc."
                )
            mesh = mesh_children[0]
        else:
            raise FLVERError(f"Selected object '{obj.name}' is not a Mesh or Armature. Cannot parse as FLVER.")

        return armature, mesh
