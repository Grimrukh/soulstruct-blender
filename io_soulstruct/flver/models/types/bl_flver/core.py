"""Blender's FLVER class.

This class is so big and complicated, and does so much, that its main methods are 'implemented' in adjacent private
modules with underscore-prefixed names, to keep the main class file clean and readable.
"""
from __future__ import annotations

__all__ = [
    "BlenderFLVER",
]

import typing as tp

import bpy

from soulstruct.base.models.flver import *
from soulstruct.utilities.text import natural_keys

from io_soulstruct.exceptions import *
from io_soulstruct.flver.image.types import DDSTextureCollection
from io_soulstruct.flver.material.types import BlenderFLVERMaterial
from io_soulstruct.flver.models.properties import *
from io_soulstruct.types import *
from io_soulstruct.utilities import *
from ..bl_flver_dummy import BlenderFLVERDummy
from ..enums import FLVERModelType, FLVERBoneDataType

# Private implementation modules:
from ._create_materials import CreatedFLVERMaterials, create_materials
from ._deep_rename import deep_rename
from ._duplicate import *
from ._export import create_flver_from_bl_flver
from ._import import create_bl_flver_from_flver

if tp.TYPE_CHECKING:
    from io_soulstruct.flver.image.image_import_manager import ImageImportManager


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
    def bone_data_type(self) -> FLVERBoneDataType:
        return FLVERBoneDataType(self.type_properties.bone_data_type)

    @bone_data_type.setter
    def bone_data_type(self, value: FLVERBoneDataType):
        self.type_properties.bone_data_type = FLVERBoneDataType(value)

    @property
    def armature(self) -> bpy.types.ArmatureObject | None:
        """Detect parent Armature of wrapped Mesh object."""
        if self.obj.parent and self.obj.parent.type == "ARMATURE":
            # noinspection PyTypeChecker
            return self.obj.parent
        return None

    @classmethod
    def from_armature_or_mesh(cls, obj: bpy.types.Object) -> BlenderFLVER:
        """FLVER models can be parsed from a Mesh obj or its optional Armature parent."""
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

    def deep_rename(self, new_name: str, old_name=""):
        deep_rename(self, new_name, old_name)

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
        return duplicate_armature(self, context, child_mesh_obj, copy_pose)

    def duplicate_dummies(self) -> list[bpy.types.Object]:
        """Duplicate all FLVER Dummies of this model to new Empty objects in the same collections."""
        return duplicate_dummies(self)

    def duplicate(
        self,
        context: bpy.types.Context,
        collections: tp.Sequence[bpy.types.Collection] = None,
        make_materials_single_user=True,
        copy_pose=True,
    ) -> BlenderFLVER:
        """Duplicate ALL objects, data-blocks, and materials of this FLVER model to a new one.

        Nothing is renamed; the caller can do that as desired. By default, names of new objects/data-blocks will
        obviously gain Blender '.001' dupe suffixes, but `.rename()` will remove these.
        """
        return duplicate(self, context, collections, make_materials_single_user, copy_pose)

    def duplicate_edit_mode(
        self,
        context: bpy.types.Context,
        make_materials_single_user=True,
        copy_pose=True,
    ) -> BlenderFLVER:
        """Duplicate to a new FLVER model, but in Edit Mode, taking only the selected vertices/edges/faces of Mesh.

        As with `duplicate()`, nothing is renamed; the caller can do that as desired.
        """
        return duplicate_edit_mode(self, context, make_materials_single_user, copy_pose)

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

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        flver: FLVER,
        name: str,
        image_import_manager: ImageImportManager | None = None,
        collection: bpy.types.Collection = None,
        existing_merged_mesh: MergedMesh = None,
        existing_bl_materials: tp.Sequence[BlenderFLVERMaterial] = None,
        force_bone_data_type: FLVERBoneDataType | None = None,
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

        return create_bl_flver_from_flver(
            operator,
            context,
            flver,
            name,
            collection=collection,
            image_import_manager=image_import_manager,
            existing_merged_mesh=existing_merged_mesh,
            existing_bl_materials=existing_bl_materials,
            force_bone_data_type=force_bone_data_type,
        )

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
    ) -> CreatedFLVERMaterials:
        """Create Blender materials needed for `flver`.

        We need to scan the `FLVER` to actually parse which unique combinations of Material/Mesh properties exist.

        Returns a struct containing:
            - the Blender materials found or created
            - the Blender material indices for each FLVER mesh
            - a list of UV layer names for each Blender material (NOT for each mesh)
        """
        return create_materials(
            operator, context, flver, model_name, material_blend_mode, image_import_manager, bl_materials_by_matdef_name
        )

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        texture_collection: DDSTextureCollection = None,
        flver_model_type=FLVERModelType.Unknown,
    ) -> FLVER:
        return create_flver_from_bl_flver(operator, context, self, texture_collection, flver_model_type)

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
    def get_selected_flvers(cls, context: bpy.types.Context, sort=True) -> list[BlenderFLVER]:
        """Get the Mesh and (optional) Armature components of ALL selected FLVER objects of either type.

        If the Armature and Mesh of the same FLVER are selected, it will NOT be duplicated in the output list, so
        selecting entire hierarchies before using this is safe.
        """
        if not context.selected_objects:
            raise SoulstructTypeError("No FLVER Meshes or Armatures selected.")
        mesh_ids = []
        flvers = []
        for obj in context.selected_objects:
            _, mesh = cls.parse_flver_obj(obj)
            if id(mesh) not in mesh_ids:  # make sure we don't duplicate FLVERs
                flvers.append(cls(mesh))
                mesh_ids.append(id(mesh))
        if sort:  # sort by Blender name, so export order always matches outliner order
            flvers = sorted(flvers, key=lambda o: natural_keys(o.obj.name))
        return flvers

    @classmethod
    def is_obj_type(cls, obj: bpy.types.Object) -> bool:
        """For FLVER, Blender `obj` could be Mesh or Armature."""
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


BlenderFLVER.add_auto_type_props(*BlenderFLVER.AUTO_FLVER_PROPS)
