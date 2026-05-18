"""Blender's FLVER class.

This class is so big and complicated, and does so much, that its main methods are 'implemented' in adjacent private
modules with underscore-prefixed names, to keep the main class file clean and readable.
"""
from __future__ import annotations

__all__ = [
    "BlenderFLVER",
]

import time
import traceback
import typing as tp
from pathlib import Path

import bpy

from soulstruct.flver import FLVER
from soulstruct.utilities.text import natural_keys

import pyrelink.core as pyre
import pyrelink.flver as pyre_flver

from .....base.operators import *
from .....base.soulstruct_object import BaseBlenderSoulstructObject, add_auto_type_props
from .....exceptions import *
from .....flver.image.types import DDSTextureCollection
from .....flver.material.types import BlenderFLVERMaterial
from .....flver.models.properties import *
from .....types import *
from .....utilities import *
from ..bl_flver_dummy import BlenderFLVERDummy
from ..enums import FLVERModelType, FLVERBoneDataType

# Private implementation modules:
from ._create_materials import CreatedFLVERMaterials, create_materials
from ._deep_rename import deep_rename
from ._duplicate import *
from ._export import create_flver_from_bl_flver
from ._import import create_bl_flver_from_flver

if tp.TYPE_CHECKING:
    from .....flver.image.image_import_manager import ImageImportManager


class BlenderFLVER(BaseBlenderSoulstructObject[FLVER, FLVERProps]):
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
    BL_OBJ_TYPE = ObjectType.MESH

    __slots__ = []
    obj: MeshObject  # type override
    data: bpy.types.Mesh  # type override

    AUTO_FLVER_PROPS: tp.ClassVar[list[str]] = [
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
    def armature(self) -> ArmatureObject | None:
        """Detect parent Armature of wrapped Mesh object."""
        if self.obj.parent and self.obj.parent.type == "ARMATURE":
            # noinspection PyTypeChecker
            return self.obj.parent
        return None

    @classmethod
    def from_armature_or_mesh(cls, obj: bpy.types.Object | None) -> tp.Self:
        """FLVER models can be parsed from a Mesh obj or its optional Armature parent."""
        if not obj:
            raise SoulstructTypeError("No Object given.")
        _, mesh = cls.parse_flver_obj(obj)
        return cls(mesh)

    @property
    def mesh(self) -> MeshObject:
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
        """Find all FLVER Dummy (empty children of Armature parent, i.e. siblings of Mesh, with expected name).

        If `operator` is provided, warnings will be logged for any Empty children that do not match the expected name
        pattern.
        """
        if not self.armature:
            return []  # Dummies require a FLVER Armature parent

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
        child_mesh_obj: MeshObject,
        as_data_instance=False,
        copy_pose=False,
    ) -> ArmatureObject:
        """Duplicate just the `armature` of this FLVER model. Mostly used internally during full duplication.

        If `child_mesh_obj` is given (e.g. one just created/duplicated), it is parented to the new Armature and rigged
        with an Armature modifier.

        Also duplicates all dummy children.

        Does not rename anything.
        """
        new_armature_obj = duplicate_armature(self, context, child_mesh_obj, as_data_instance)
        if copy_pose and (armature := self.armature):
            context.view_layer.update()  # SLOW
            copy_armature_pose(armature, new_armature_obj)
        return new_armature_obj

    def duplicate_dummies(self) -> list[bpy.types.Object]:
        """Duplicate all FLVER Dummies of this model to new Empty objects in the same collections."""
        return duplicate_dummies(self)

    def duplicate(
        self,
        context: bpy.types.Context,
        collections: tp.Sequence[bpy.types.Collection] = None,
        make_materials_single_user=True,
        copy_pose=False,
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
        copy_pose=False,
    ) -> BlenderFLVER:
        """Duplicate to a new FLVER model, but in Edit Mode, taking only the selected vertices/edges/faces of Mesh.

        As with `duplicate()`, nothing is renamed; the caller can do that as desired.
        """
        return duplicate_edit_mode(self, context, make_materials_single_user, copy_pose)

    def sync_msb_part_armatures(self, context: bpy.types.Context) -> list[MeshObject]:
        """Find all MSB Part instances that use this FLVER as their model, and sync their Armatures to this FLVER's
        Armature. This may involve creating a new Armature for the Part."""

        if not (armature := self.armature):
            return []  # nothing to sync if no Armature (we don't delete out-of-sync MSB Part armatures)
        bl_msb_part_users = self.find_msb_part_users()
        if not bl_msb_part_users:
            return []

        # First pass: create any missing Armatures.
        bl_msb_part_armatures = []
        for bl_msb_part in bl_msb_part_users:
            if bl_msb_part.parent and bl_msb_part.parent.type == "ARMATURE":
                bl_msb_part_arma = bl_msb_part.parent
                bl_msb_part_arma.data = armature.data  # assign new Armature data to existing Armature object
            else:
                if self.bone_data_type != FLVERBoneDataType.CUSTOM:
                    # TODO: Baked policy: only create new Armatures for CUSTOM bone data (e.g. static Map Piece pose).
                    continue

                # Create Armature, name it, and move Part's transform from Mesh to it.
                bl_msb_part_arma = self.duplicate_armature(context, bl_msb_part, as_data_instance=True, copy_pose=False)
                bl_msb_part_arma.name = f"{bl_msb_part.name} Armature"
                bl_msb_part_arma.location = bl_msb_part.location
                bl_msb_part.location = (0, 0, 0)
                bl_msb_part_arma.rotation_euler = bl_msb_part.rotation_euler
                bl_msb_part.rotation_euler = (0, 0, 0)
                bl_msb_part_arma.scale = bl_msb_part.scale
                bl_msb_part.scale = (1, 1, 1)

            bl_msb_part_armatures.append(bl_msb_part_arma)
        if bl_msb_part_armatures:
            # Update view layer ONCE to capture any newly-created armatures.
            context.view_layer.update()  # SLOW
        for bl_msb_part_arma in bl_msb_part_armatures:
            copy_armature_pose(armature, bl_msb_part_arma)
        return bl_msb_part_users

    def find_msb_part_users(self) -> list[MeshObject]:
        """Find all MSB Part objects using this FLVER's mesh as their data block."""
        # noinspection PyTypeChecker
        return [
            obj for obj in bpy.data.objects
            if obj.soulstruct_type == SoulstructType.MSB_PART and obj.data is self.data
        ]

    @staticmethod
    def create_default_armature_parent(
        context: bpy.types.Context,
        model_name: str,
        mesh_child_obj: MeshObject = None,
    ) -> ArmatureObject:
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
        soulstruct_obj: FLVER,
        name: str,
        collection: bpy.types.Collection = None,
        *,
        image_import_manager: ImageImportManager | None = None,
        texture_finder: pyre_flver.TextureFinder | None = None,
        existing_bl_materials: tp.Sequence[BlenderFLVERMaterial] = None,
        existing_mesh_bl_material_indices: tp.Sequence[int] = None,
    ) -> BlenderFLVER:
        """Read a FLVER into a managed Blender Armature/Mesh.

        If the FLVER has only a single bone with all-default properties for this game, and no Dummies, no Armature will
        be created and the Mesh will be the root object. This is useful for simple static models like map pieces.

        Merged Mesh may be cached in advance (e.g. in parallel) on `FLVER` instance. If so, `existing_bl_materials` and
        `existing_mesh_bl_material_indices` must also be given, and should have been created in advance to get the
        `MergedMesh` arguments anyway.

        NOTE: FLVER (for DS1 at least) supports a maximum of 38 bones per sub-mesh. When this maximum is reached, a new
        FLVER sub-mesh is created. All of these sub-meshes are unified in Blender under the same material slot, and will
        be split again on export as needed.

        Some FLVER meshes also use the same material, but have different `Mesh` or `FaceSet` properties such as
        `use_backface_culling`. Backface culling is a material option in Blender, so these meshes will use different
        Blender material 'variants' even though they use the same FLVER material. The FLVER exporter will start by
        creating a FLVER material for every Blender material slot, then unify any identical FLVER material instances and
        redirect any differences like `use_backface_culling` or `is_dynamic` to the FLVER mesh.

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
            cls,
            operator,
            context,
            flver=soulstruct_obj,
            name=name,
            collection=collection,
            image_import_manager=image_import_manager,
            texture_finder=texture_finder,
            existing_bl_materials=existing_bl_materials,
            existing_mesh_bl_material_indices=existing_mesh_bl_material_indices,
        )

    @classmethod
    def new_batch_from_soulstruct_objs(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        flver_path_sources: dict[str, Path] = None,
        flver_binder_sources: dict[str, tuple[pyre.BinderEntry, pyre.Binder]] = None,
        texture_finder_callback: tp.Callable[[pyre_flver.TextureFinder, pyre_flver.FLVER, pyre.BinderEntry | Path, pyre.Binder | None], None] = None,
        flver_model_category: str = "",
        collection: bpy.types.Collection | None = None,
    ) -> dict[str, tp.Self]:
        """Primary multi-FLVER importer with efficient Blender material construction and texture retrieval.

        FLVERs should already be parsed into dictionaries of Path sources and (BinderEntry, Binder) sources.

        Returns a dictionary of FLVERs keyed by model stem. FLVERs that have import errors are logged and ignored.
        """

        # Format category spacing for easier message formatting (one trailing space).
        flver_model_category = f"{flver_model_category.rstrip()} " if flver_model_category else ""

        settings = context.scene.soulstruct_settings
        flver_import_settings = context.scene.flver_import_settings

        flver_path_sources = flver_path_sources or {}
        flver_binder_sources = flver_binder_sources or {}
        flvers = {}  # type: dict[str, FLVER | pyre_flver.FLVER]

        operator.info(
            f"Importing {len(flver_binder_sources) + len(flver_path_sources)} "
            f"{flver_model_category}FLVERs in parallel.",
            report=True,
        )

        p = time.perf_counter()

        # STEPS: FLVER import + Texture registration + Material creation + BlenderFLVER creation, per FLVER
        steps = 5 * (len(flver_path_sources) + len(flver_binder_sources))
        if context.window_manager:
            context.window_manager.progress_begin(0, steps)

        def progress(s: int) -> None:
            if context.window_manager:
                context.window_manager.progress_update(s)

        if settings.use_pyrelink_flver:
            # Use C++ acceleration.
            flvers_from_paths = pyre_flver.FLVER.from_paths_parallel(list(flver_path_sources.values()))
            flvers_from_binders = pyre_flver.FLVER.from_bytes_parallel(
                [entry.get_uncompressed_data() for entry, _ in flver_binder_sources.values()]
            )
            for flver, (entry, _) in zip(flvers_from_binders, flver_binder_sources.values(), strict=True):
                # Set FLVER path manually to BinderEntry name (not full path).
                flver.path = entry.name
        else:
            # Use pure Python FLVER.
            flvers_from_paths = FLVER.from_paths_parallel(list(flver_path_sources.values()))
            flvers_from_binders = FLVER.from_binder_entries_parallel(
                [entry for entry, _ in flver_binder_sources.values()]
            )

        progress(steps // 5)

        for (name, _), flver_from_path in zip(flver_path_sources.items(), flvers_from_paths, strict=True):
            if flver_from_path:
                flvers[name] = flver_from_path
        for (name, _), flver_from_binder in zip(flver_binder_sources.items(), flvers_from_binders, strict=True):
            if name in flvers:
                # FLVER loaded from both Path and BinderEntry.
                operator.warning(
                    f"FLVER '{name}' loaded from both Path and BinderEntry sources. Using Path source and ignoring "
                    f"BinderEntry source."
                )
            elif flver_from_binder:
                flvers[name] = flver_from_binder

        operator.info(
            f"Imported {len(flvers)} {flver_model_category}FLVERs in {time.perf_counter() - p:.2f} seconds."
        )
        p = time.perf_counter()

        if flver_import_settings.import_textures:

            step = steps // 5
            if settings.pyrelink_game_type == pyre.GameType.Bloodborne:
                # TODO: pyrelink TextureFinder cannot deswizzle PS4 textures yet.
                image_import_manager = ImageImportManager(operator, context)
                texture_finder = None

                # Find textures for all loaded FLVERs.
                for model_name, flver in flvers.items():
                    _, source_binder = flver_binder_sources.get(model_name, (None, None))
                    image_import_manager.find_flver_textures(
                        source_binder.path if source_binder else flver.path,
                        source_binder,
                    )
                    progress(step)
                    step += 1
            else:
                image_import_manager = None
                texture_finder = settings.create_texture_finder()

                # Find textures for all loaded FLVERs.
                reg_p = time.perf_counter()
                for model_name, flver in flvers.items():
                    _, source_binder = flver_binder_sources.get(model_name, (None, None))
                    texture_finder.register_flver_sources(
                        str(source_binder.path if source_binder else flver.path),
                        source_binder,
                    )
                    if texture_finder_callback:
                        # Logical assertion: FLVER source must be Path or BinderEntry in one of these.
                        flver_source = flver_path_sources[model_name] or flver_binder_sources[model_name][0]
                        texture_finder_callback(
                            texture_finder,
                            flver,
                            flver_source,
                            flver_binder_sources.get(model_name, (None, None))[1],
                        )
                    progress(step)
                    step += 1
                operator.info(
                    f"Registered FLVER texture sources for {len(flvers)} in {time.perf_counter() - reg_p:.2f} s."
                )
        else:
            image_import_manager = None
            texture_finder = None
            progress(2 * steps // 5)

        # Brief non-parallel excursion: create Blender materials and `MergedMesh` arguments for each `FLVER`.
        flver_bl_materials = {}  # type: dict[str, tuple[BlenderFLVERMaterial, ...]]
        flver_mesh_bl_material_indices = {}  # type: dict[str, tuple[int, ...]]
        flver_names_to_merge = []

        # Arguments for parallel MergedMesh cache:
        flvers_to_merge = []
        flvers_mesh_material_indices = []
        flvers_bl_material_uv_layer_names = []

        bl_materials_by_matdef_name = {}  # can re-use cache across all FLVERs!
        step = 2 * steps // 5
        for model_name, flver in tuple(flvers.items()):
            if not flver.meshes:
                # FLVER has no meshes. No materials or merging.
                continue

            try:
                mat_p = time.perf_counter()
                bl_materials, mesh_bl_material_indices, bl_material_uv_layer_names = BlenderFLVER.create_materials(
                    operator,
                    context,
                    flver,
                    model_name,
                    material_blend_mode=flver_import_settings.material_blend_mode,
                    image_import_manager=image_import_manager,
                    texture_finder=texture_finder,
                    bl_materials_by_matdef_name=bl_materials_by_matdef_name,
                )
                progress(step)
                step += 1
                operator.info(
                    f"Created Blender materials for FLVER in {time.perf_counter() - mat_p:.3f} s: {model_name}"
                )
            except Exception as ex:
                operator.error(f"(Batch) Cannot import FLVER: {flver.path_name}. Material creation error: {ex}")
                flvers.pop(model_name)  # drop failed FLVER
                continue

            flver_bl_materials[model_name] = bl_materials
            flver_mesh_bl_material_indices[model_name] = mesh_bl_material_indices

            flver_names_to_merge.append(model_name)
            flvers_to_merge.append(flver)
            flvers_mesh_material_indices.append(mesh_bl_material_indices)
            flvers_bl_material_uv_layer_names.append(bl_material_uv_layer_names)

        operator.info(
            f"Created materials for {len(flvers)} {flver_model_category}FLVERs in {time.perf_counter() - p:.2f} "
            f"seconds."
        )
        p = time.perf_counter()

        # Merge meshes in parallel. Empty meshes will be `None`.
        # API is the same for Python and C++ FLVER.
        if settings.use_pyrelink_flver:
            merge_successes = pyre_flver.FLVER.update_cached_merged_meshes_parallel(
                flvers_to_merge,
                flvers_mesh_material_indices,
                flvers_bl_material_uv_layer_names,
                [flver_import_settings.merge_mesh_vertices] * len(flvers_to_merge),  # type: list[bool]
            )
        else:
            merge_successes = FLVER.update_cached_merged_meshes_parallel(
                flvers_to_merge,
                flvers_mesh_material_indices,
                flvers_bl_material_uv_layer_names,
                [flver_import_settings.merge_mesh_vertices] * len(flvers_to_merge),  # type: list[bool]
            )
        step = 4 * steps // 5
        progress(step)

        operator.info(
            f"Merged {len(flvers)} {flver_model_category}FLVERs in {time.perf_counter() - p:.2f} s (C++)."
        )
        flver_merge_successes = {
            model_name: success
            for model_name, success in zip(flver_names_to_merge, merge_successes, strict=True)
        }

        p = time.perf_counter()

        if collection is None:
            collection = find_or_create_collection(
                context.scene.collection,
                "Models",
                "Game Models",
            )

        bl_flvers = {}

        # Construction of BlenderFLVER cannot be parallelized, unfortunately.
        for model_name, flver in flvers.items():

            if flver.meshes:
                # Check for errors in merging and/or material creation.
                if not flver_merge_successes[model_name] and flver_bl_materials[model_name] is not None:
                    operator.error(f"Cannot import FLVER '{model_name}' ({flver.path_name}) due to `MergedMesh` error.")
                    continue
                if flver_bl_materials[model_name] is None and flver_merge_successes[model_name]:
                    operator.error(f"Cannot import FLVER: '{model_name}' ({flver.path_name}) due to material error.")
                    continue
                bl_materials = flver_bl_materials[model_name]
                mesh_bl_material_indices = flver_mesh_bl_material_indices[model_name]
            else:
                bl_materials = None
                mesh_bl_material_indices = None

            try:
                bl_flver = BlenderFLVER.new_from_soulstruct_obj(
                    operator,
                    context,
                    flver,
                    name=model_name,
                    texture_finder=texture_finder,
                    collection=collection,
                    existing_bl_materials=bl_materials,
                    existing_mesh_bl_material_indices=mesh_bl_material_indices,
                )
                progress(step)
                step += 1
            except Exception as ex:
                traceback.print_exc()  # for inspection in Blender console
                operator.error(f"Cannot import {flver_model_category}FLVER: {flver.path_name}. Error: {ex}")
            else:
                bl_flvers[model_name] = bl_flver

        if context.window_manager:
            context.window_manager.progress_end()

        operator.info(
            f"Imported {len(flvers)} {flver_model_category}FLVERs in {time.perf_counter() - p:.2f} seconds."
        )

        return bl_flvers

    @classmethod
    def create_materials(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        flver: FLVER,
        model_name: str,
        material_blend_mode: str,
        image_import_manager: ImageImportManager | None = None,
        texture_finder: pyre_flver.TextureFinder | None = None,
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
            operator,
            context,
            flver,
            model_name,
            material_blend_mode=material_blend_mode,
            image_import_manager=image_import_manager,
            texture_finder=texture_finder,
            bl_materials_by_matdef_name=bl_materials_by_matdef_name,
        )

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        texture_collection: DDSTextureCollection = None,
        flver_model_type=FLVERModelType.Unknown,
    ) -> FLVER:
        return create_flver_from_bl_flver(operator, context, self, texture_collection, flver_model_type)

    @property
    def game_name(self) -> str:
        """Splits on spaces and periods after removing dupe suffix."""
        return get_model_name(self.obj.name)

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
    def parse_flver_obj(obj: bpy.types.Object) -> tuple[ArmatureObject | None, MeshObject]:
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


add_auto_type_props(BlenderFLVER, *BlenderFLVER.AUTO_FLVER_PROPS)
