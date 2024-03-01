from __future__ import annotations

__all__ = ["FLVERImporter"]

import math
import numpy as np
import time
import typing as tp
from dataclasses import dataclass, field
from pathlib import Path

import bmesh
import bpy
import bpy.ops
from mathutils import Vector, Matrix

from soulstruct.base.models.flver import FLVER, FLVERBone, FLVERBoneUsageFlags, Dummy, Material
from soulstruct.base.models.flver.mesh_tools import MergedMesh
from soulstruct.containers.tpf import TPFTexture, batch_get_tpf_texture_png_data
from soulstruct.games import *
from soulstruct.utilities.maths import Vector3

from io_soulstruct.utilities import *
from io_soulstruct.flver.materials import *
from io_soulstruct.flver.textures.import_textures import TextureImportManager, import_png_as_image
from io_soulstruct.flver.utilities import *

if tp.TYPE_CHECKING:
    from soulstruct.base.models.mtd import MTDBND as BaseMTDBND
    from soulstruct.eldenring.models.matbin import MATBINBND
    from io_soulstruct.general import SoulstructSettings
    from .settings import FLVERImportSettings


@dataclass(slots=True)
class FLVERImporter:
    """Manages imports for a batch of FLVER files using the same settings.

    Call `import_flver()` to import a single FLVER file.
    """

    operator: LoggingOperator
    context: bpy.types.Context
    settings: SoulstructSettings
    texture_import_manager: TextureImportManager | None = None
    collection: bpy.types.Collection | None = None

    # Loaded from `settings` if not given.
    mtdbnd: BaseMTDBND | None = None
    matbinbnd: MATBINBND | None = None

    # Per-FLVER settings.
    flver: FLVER | None = None  # current FLVER being imported
    name: str = ""  # name of root Blender mesh object that will be created
    bl_bone_names: list[str] = field(default_factory=list)  # list of Blender bone names in order of FLVER bones
    new_objs: list[bpy.types.Object] = field(default_factory=list)  # all new objects created during import
    new_images: list[bpy.types.Image] = field(default_factory=list)  # all new images created during import
    new_materials: list[bpy.types.Material] = field(default_factory=list)  # all new materials created during import

    def __post_init__(self):
        if self.mtdbnd is None:
            self.mtdbnd = self.settings.get_mtdbnd(self.operator)
        if self.matbinbnd is None:
            self.matbinbnd = self.settings.get_matbinbnd(self.operator)
        if self.collection is None:
            self.collection = self.context.scene.collection

    def abort_import(self):
        """Delete all Blender objects, images, and materials created during this import."""
        for obj in self.new_objs:
            try:
                bpy.data.objects.remove(obj)
            except ReferenceError:
                pass
        for img in self.new_images:
            try:
                bpy.data.images.remove(img)
            except ReferenceError:
                pass
        for mat in self.new_materials:
            try:
                bpy.data.materials.remove(mat)
            except ReferenceError:
                pass
        self.flver = None
        self.name = ""
        self.bl_bone_names.clear()
        self.new_objs.clear()
        self.new_images.clear()
        self.new_materials.clear()

    def import_flver(self, flver: FLVER, name: str) -> tuple[bpy.types.ArmatureObject, bpy.types.MeshObject]:
        """Read a FLVER into a Blender Armature and child Mesh."""

        self.flver = flver
        self.name = name
        self.bl_bone_names.clear()
        self.new_objs.clear()
        self.new_images.clear()
        self.new_materials.clear()

        # Create FLVER bone index -> Blender bone name dictionary. (Blender names are UTF-8.)
        # This is done even when `existing_armature` is given, as the order of bones in this new FLVER may be different
        # and the vertex weight indices need to be directed to the names of bones in `existing_armature` correctly.
        for bone in flver.bones:
            # Just using actual bone names to avoid the need for parsing rules on export. However, duplicate names
            # need to be handled with suffixes.
            bl_bone_name = f"{bone.name} <DUPE>" if bone.name in self.bl_bone_names else bone.name
            self.bl_bone_names.append(bl_bone_name)

        import_settings = self.context.scene.flver_import_settings  # type: FLVERImportSettings

        bl_armature_obj = self.create_armature(import_settings.base_edit_bone_length)
        self.new_objs.append(bl_armature_obj)

        submesh_bl_material_indices, bl_material_uv_layer_names = self.create_materials(
            flver, import_settings.material_blend_mode
        )

        bl_flver_mesh = self.create_flver_mesh(
            flver, self.name, submesh_bl_material_indices, bl_material_uv_layer_names
        )

        # Assign basic FLVER header information as custom props on the Armature.
        bl_armature_obj["Is Big Endian"] = flver.big_endian  # bool
        bl_armature_obj["Version"] = flver.version.name  # str
        bl_armature_obj["Unicode"] = flver.unicode  # bool
        bl_armature_obj["Unk x4a"] = flver.unk_x4a  # bool
        bl_armature_obj["Unk x4c"] = flver.unk_x4c  # int
        bl_armature_obj["Unk x5c"] = flver.unk_x5c  # int
        bl_armature_obj["Unk x5d"] = flver.unk_x5d  # int
        bl_armature_obj["Unk x68"] = flver.unk_x68  # int

        # Parent mesh to armature. This is critical for proper animation behavior (especially with root motion).
        bl_flver_mesh.parent = bl_armature_obj
        self.create_mesh_armature_modifier(bl_flver_mesh, bl_armature_obj)

        for i, dummy in enumerate(flver.dummies):
            self.create_dummy(dummy, index=i, bl_armature=bl_armature_obj)

        # self.operator.info(f"Created FLVER Blender mesh '{name}' in {time.perf_counter() - start_time:.3f} seconds.")

        return bl_armature_obj, bl_flver_mesh  # might be used by other importers

    def create_mesh_armature_modifier(self, bl_mesh: bpy.types.MeshObject, bl_armature: bpy.types.ArmatureObject):
        self.operator.set_active_obj(bl_mesh)
        bpy.ops.object.modifier_add(type="ARMATURE")
        armature_mod = bl_mesh.modifiers["Armature"]
        armature_mod.object = bl_armature
        armature_mod.show_in_editmode = True
        armature_mod.show_on_cage = True

    def create_materials(
        self,
        flver: FLVER,
        material_blend_mode: str,
    ) -> tuple[list[int], list[list[str]]]:
        """Create Blender materials needed for `flver`.

        Returns a list of Blender material indices for each submesh, and a list of UV layer names for each Blender
        material (NOT each submesh).
        """
        # Submesh-matched list of dictionaries mapping sample/texture type to texture path (only name matters).
        all_submesh_texture_stems = self.get_submesh_flver_textures()

        if self.texture_import_manager or self.settings.png_cache_directory:
            p = time.perf_counter()
            all_texture_stems = {v for submesh_textures in all_submesh_texture_stems for v in submesh_textures.values()}
            self.new_images = self.load_texture_images(all_texture_stems, self.texture_import_manager)
            if self.new_images:
                self.operator.info(f"Loaded {len(self.new_images)} textures in {time.perf_counter() - p:.3f} seconds.")
        else:
            self.operator.info("No imported textures or PNG cache folder given. No textures loaded for FLVER.")

        # Maps FLVER submeshes to their Blender material index to store per-face in the merged mesh.
        # Submeshes that originally indexed the same FLVER material may have different Blender 'variant' materials that
        # hold certain Submesh/FaceSet properties like `use_backface_culling`.
        # Conversely, Submeshes that only serve to handle per-submesh bone maximums (e.g. 38 in DS1) will use the same
        # Blender material and be split again automatically on export (but likely not in an indentical way!).
        submesh_bl_material_indices = []
        # UV layer names used by each Blender material index (NOT each FLVER submesh).
        bl_material_uv_layer_names = []  # type: list[list[str]]

        # Map FLVER material hashes to the indices of variant Blender materials sourced from them, which hold distinct
        # Submesh/FaceSet properties.
        flver_material_hash_variants = {}

        # Map FLVER material hashes to their material info.
        flver_material_infos = {}  # type: dict[int, BaseMaterialShaderInfo]
        for submesh in flver.submeshes:
            material_hash = hash(submesh.material)  # TODO: should hash ignore material name?
            if material_hash in flver_material_infos:
                continue  # material already created (used by a previous submesh)

            if self.settings.is_game(DARK_SOULS_PTDE, DARK_SOULS_DSR):
                material_info = DS1MaterialShaderInfo.from_mtdbnd_or_name(
                    self.operator, submesh.material.mat_def_name, self.mtdbnd
                )
            elif self.settings.is_game(BLOODBORNE):
                material_info = BBMaterialShaderInfo.from_mtdbnd_or_name(
                    self.operator, submesh.material.mat_def_name, self.mtdbnd
                )
            elif self.settings.is_game(ELDEN_RING):
                material_info = ERMaterialShaderInfo.from_matbin_name_or_matbinbnd(
                    self.operator, submesh.material.mat_def_name, self.matbinbnd
                )
            else:
                raise FLVERImportError(f"FLVER material creation not implemented for game {self.settings.game.name}.")
            flver_material_infos[material_hash] = material_info

        self.new_materials = []
        for submesh, submesh_textures in zip(flver.submeshes, all_submesh_texture_stems, strict=True):
            material = submesh.material  # type: Material
            material_hash = hash(material)  # NOTE: if there are duplicate FLVER materials, this will combine them
            vertex_color_count = len([f for f in submesh.vertices.dtype.names if "color" in f])

            if material_hash not in flver_material_hash_variants:
                # First time this FLVER material has been encountered. Create it in Blender now.
                # NOTE: Vanilla material names are unused and essentially worthless. They can also be the same for
                #  materials that actually use different lightmaps, EVEN INSIDE the same FLVER model. Names are changed
                #  here to just reflect the index. The original name is NOT kept to avoid stacking up formatting on
                #  export/import and because it is so useless anyway.
                flver_material_index = len(flver_material_hash_variants)
                bl_material_index = len(self.new_materials)
                material_info = flver_material_infos[material_hash]

                # Create a relatively informative material name.
                bl_material_name = (
                    f"{self.name} {flver_material_index} {material.mat_def_stem} ({material_info.shader_stem})"
                )

                bl_material = create_submesh_blender_material(
                    self.operator,
                    material,
                    submesh_textures,
                    material_name=bl_material_name,
                    material_info=material_info,
                    submesh=submesh,
                    vertex_color_count=vertex_color_count,
                    blend_mode=material_blend_mode,
                    warn_missing_textures=self.texture_import_manager is not None,
                )  # type: bpy.types.Material

                submesh_bl_material_indices.append(bl_material_index)
                flver_material_hash_variants[material_hash] = [bl_material_index]

                self.new_materials.append(bl_material)
                bl_material_uv_layer_names.append(
                    [layer.name for layer in flver_material_infos[material_hash].used_uv_layers]
                )
                continue

            existing_variant_bl_indices = flver_material_hash_variants[material_hash]

            # Check if Blender material needs to be duplicated as a variant with different Mesh properties.
            found_existing_material = False
            for existing_bl_material_index in existing_variant_bl_indices:
                # NOTE: We do not care about enforcing any maximum submesh local bone count in Blender! The FLVER
                # exporter will create additional split submeshes as necessary for that.
                existing_bl_material = self.new_materials[existing_bl_material_index]
                if (
                    bool(existing_bl_material["Is Bind Pose"]) == submesh.is_bind_pose
                    and existing_bl_material["Default Bone Index"] == submesh.default_bone_index
                    and existing_bl_material["Face Set Count"] == len(submesh.face_sets)
                    and existing_bl_material.use_backface_culling == submesh.use_backface_culling
                ):
                    # Blender material already exists with the same Mesh properties. No new variant neeed.
                    submesh_bl_material_indices.append(existing_bl_material_index)
                    found_existing_material = True
                    break

            if found_existing_material:
                continue

            # No match found. New Blender material variant is needed to hold unique submesh data.
            variant_index = len(existing_variant_bl_indices)
            first_material = self.new_materials[existing_variant_bl_indices[0]]
            variant_name = first_material.name + f" <V{variant_index}>"
            bl_material = create_submesh_blender_material(
                self.operator,
                material,
                submesh_textures,
                material_name=variant_name,
                material_info=flver_material_infos[material_hash],
                submesh=submesh,
                vertex_color_count=vertex_color_count,
                blend_mode=material_blend_mode,
            )  # type: bpy.types.Material

            new_bl_material_index = len(self.new_materials)
            submesh_bl_material_indices.append(new_bl_material_index)
            flver_material_hash_variants[material_hash].append(new_bl_material_index)
            self.new_materials.append(bl_material)
            bl_material_uv_layer_names.append(
                [layer.name for layer in flver_material_infos[material_hash].used_uv_layers]
            )

        return submesh_bl_material_indices, bl_material_uv_layer_names

    def get_submesh_flver_textures(self) -> list[dict[str, str]]:
        """For each submesh, get a dictionary mapping sampler names (e.g. 'g_Diffuse') to texture path names (e.g.
        'c2000_fur').

        These paths may come from the FLVER material (older games) or MATBIN (newer games). In the latter case, FLVER
        material paths are usually empty, but will be accepted as overrides if given.
        """
        all_submesh_texture_names = []
        for submesh in self.flver.submeshes:
            submesh_texture_stems = {}
            if self.matbinbnd:
                try:
                    matbin = self.matbinbnd.get_matbin(submesh.material.mat_def_name)
                except KeyError:
                    pass  # missing
                else:
                    submesh_texture_stems |= matbin.get_all_sampler_stems()
            for texture in submesh.material.textures:
                if texture.path:
                    # FLVER texture path can also override MATBIN path.
                    submesh_texture_stems[texture.texture_type] = texture.stem
            all_submesh_texture_names.append(submesh_texture_stems)

        return all_submesh_texture_names

    def create_armature(self, base_edit_bone_length: float) -> bpy.types.ArmatureObject:
        """Create a new Blender armature to serve as the parent object for the entire FLVER."""

        self.operator.to_object_mode()
        self.operator.deselect_all()

        bl_armature_data = bpy.data.armatures.new(f"{self.name} Armature")
        bl_armature_obj = self.create_obj(f"{self.name}", bl_armature_data)
        self.create_bones(bl_armature_obj, base_edit_bone_length)

        # noinspection PyTypeChecker
        return bl_armature_obj

    def load_texture_images(
        self,
        texture_stems: set[str],
        texture_manager: TextureImportManager = None,
    ) -> list[bpy.types.Image]:
        """Load texture images from either `png_cache` folder or TPFs found with `texture_import_manager`.

        Will NEVER load an image that is already in Blender's data, regardless of image type (identified by stem only).
        """
        bl_image_stems = set()
        image_stems_to_replace = set()
        for image in bpy.data.images:
            stem = Path(image.name).stem
            if image.size[:] == (1, 1) and image.pixels[:] == (1.0, 0.0, 1.0, 1.0):
                image_stems_to_replace.add(stem)
            else:
                bl_image_stems.add(stem)
        new_loaded_images = []

        textures_to_load = {}  # type: dict[str, TPFTexture]
        for texture_stem in texture_stems:
            if texture_stem in bl_image_stems:
                continue  # already loaded
            if texture_stem in textures_to_load:
                continue  # already queued to load below

            if self.settings.read_cached_pngs and self.settings.png_cache_directory:
                png_path = Path(self.settings.png_cache_directory, f"{texture_stem}.png")
                if png_path.is_file():
                    bl_image = bpy.data.images.load(str(png_path))
                    new_loaded_images.append(bl_image)
                    bl_image_stems.add(texture_stem)
                    continue

            if texture_manager:
                try:
                    texture = texture_manager.get_flver_texture(texture_stem)
                except KeyError as ex:
                    self.warning(str(ex))
                else:
                    textures_to_load[texture_stem] = texture
                    continue

            self.warning(f"Could not find TPF or cached PNG '{texture_stem}' for FLVER '{self.name}'.")

        if textures_to_load:
            for texture_stem in textures_to_load:
                self.operator.info(f"Loading texture into Blender: {texture_stem}")
            from time import perf_counter
            t = perf_counter()
            all_png_data = batch_get_tpf_texture_png_data(list(textures_to_load.values()))
            if self.settings.png_cache_directory and self.settings.write_cached_pngs:
                write_png_directory = Path(self.settings.png_cache_directory)
            else:
                write_png_directory = None
            self.operator.info(
                f"Converted images in {perf_counter() - t} s (cached = {self.settings.write_cached_pngs})"
            )
            for texture_stem, png_data in zip(textures_to_load.keys(), all_png_data):
                if png_data is None:
                    continue  # failed to convert this texture
                bl_image = import_png_as_image(
                    texture_stem,
                    png_data,
                    write_png_directory,
                    replace_existing=texture_stem in image_stems_to_replace,
                )
                new_loaded_images.append(bl_image)

        return new_loaded_images

    def create_flver_mesh(
        self,
        flver: FLVER,
        name: str,
        submesh_bl_material_indices: list[int],
        bl_material_uv_layer_names: list[list[str]],
    ) -> bpy.types.MeshObject:
        """Create a single Blender mesh that combines all FLVER submeshes, using multiple material slots.

        NOTE: FLVER (for DS1 at least) supports a maximum of 38 bones per sub-mesh. When this maximum is reached, a new
        FLVER submesh is created. All of these sub-meshes are unified in Blender under the same material slot, and will
        be split again on export as needed.

        Some FLVER submeshes also use the same material, but have different `Mesh` or `FaceSet` properties such as
        `use_backface_culling`. Backface culling is a material option in Blender, so these submeshes will use different
        Blender material 'variants' even though they use the same FLVER material. The FLVER exporter will start by
        creating a FLVER material for every Blender material slot, then unify any identical FLVER material instances and
        redirect any differences like `use_backface_culling` or `is_bind_pose` to the FLVER mesh.

        Breakdown:
            - Blender stores POSITION, BONE WEIGHTS, and BONE INDICES on vertices. Any differences here will require
            genuine vertex duplication in Blender. (Of course, vertices at the same position in the same sub-mesh should
            essentially ALWAYS have the same bone weights and indices.)
            - Blender stores MATERIAL SLOT INDEX on faces. This is how different FLVER submeshes are represented.
            - Blender stores UV COORDINATES, VERTEX COLORS, and NORMALS on face loops ('vertex instances'). This gels
            with what FLVER meshes want to do.
            - Blender does not import tangents or bitangents. These are calculated on export.
        """
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        # Armature parent object uses simply `name`. Mesh data/object has 'Mesh' suffix.
        bl_mesh = bpy.data.meshes.new(name=f"{name} Mesh")

        for material in self.new_materials:
            bl_mesh.materials.append(material)

        if not flver.submeshes:
            # FLVER has no meshes (e.g. c0000). Leave empty.
            # noinspection PyTypeChecker
            return self.create_obj(f"{name} Mesh <EMPTY>", bl_mesh)

        if any(mesh.invalid_layout for mesh in flver.submeshes):
            # Corrupted submeshes (e.g. some DS1R map pieces). Leave empty.
            # noinspection PyTypeChecker
            return self.create_obj(f"{name} Mesh <INVALID>", bl_mesh)

        # p = time.perf_counter()
        # Create merged mesh.
        merged_mesh = MergedMesh.from_flver(
            flver,
            submesh_bl_material_indices,
            material_uv_layer_names=bl_material_uv_layer_names,
        )
        # self.operator.info(f"Merged FLVER submeshes in {time.perf_counter() - p} s")

        bl_vert_bone_weights, bl_vert_bone_indices = self.create_bm_mesh(bl_mesh, merged_mesh)

        # noinspection PyTypeChecker
        bl_mesh_obj = self.create_obj(f"{name} Mesh", bl_mesh)  # type: bpy.types.MeshObject

        self.create_bone_vertex_groups(bl_mesh_obj, bl_vert_bone_weights, bl_vert_bone_indices)

        return bl_mesh_obj

    def create_bm_mesh(self, bl_mesh: bpy.types.Mesh, merged_mesh: MergedMesh) -> tuple[np.ndarray, np.ndarray]:
        """BMesh is more efficient for mesh construction and loop data layer assignment.

        Returns two arrays of bone indices and bone weights for the created Blender vertices.
        """

        # p = time.perf_counter()

        merged_mesh.swap_vertex_yz(tangents=False, bitangents=False)
        merged_mesh.invert_vertex_uv(invert_u=False, invert_v=True)
        merged_mesh.normalize_normals()

        bm = bmesh.new()
        bm.from_mesh(bl_mesh)  # bring over UV and vertex color data layers

        if len(merged_mesh.loop_vertex_colors) > 1:
            self.warning("More than one vertex color layer detected. Only the first will be imported into Blender!")

        # CREATE BLENDER VERTICES
        for position in merged_mesh.vertex_data["position"]:
            bm.verts.new(position)
        bm.verts.ensure_lookup_table()

        # Loop indices of `merged_mesh` that actually make it into Blender, as degenerate/duplicate faces are ignored.
        # TODO: I think `MergedMesh` already removes all duplicate faces now, so if I also used it to remove degenerate
        #  faces, I wouldn't have to keep track here.
        valid_loop_indices = []
        # TODO: go back to reporting occurrences per-submesh (`faces[:, 3]`)?
        duplicate_face_count = 0
        degenerate_face_count = 0

        for face in merged_mesh.faces:

            loop_indices = face[:3]
            vertex_indices = merged_mesh.loop_vertex_indices[loop_indices]
            bm_verts = [bm.verts[v_i] for v_i in vertex_indices]

            try:
                bm_face = bm.faces.new(bm_verts)
            except ValueError as ex:
                if "face already exists" in str(ex):
                    # This is a duplicate face (happens rarely in vanilla FLVERs). We can ignore it.
                    # No lasting harm done as, by assertion, no new BMesh vertices were created above. We just need
                    # to remove the last three normals.
                    duplicate_face_count += 1
                    continue
                if "found the same (BMVert) used multiple times" in str(ex):
                    # Degenerate FLVER face (e.g. a line or point). These are not supported by Blender.
                    degenerate_face_count += 1
                    continue

                print(f"Unhandled error for BMFace. Vertices: {[v.co for v in bm_verts]}")
                raise ex

            bm_face.material_index = face[3]
            valid_loop_indices.extend(loop_indices)

        # self.operator.info(f"Created Blender mesh in {time.perf_counter() - p} s")

        if degenerate_face_count or duplicate_face_count:
            self.warning(
                f"{degenerate_face_count} degenerate and {duplicate_face_count} duplicate faces were ignored during "
                f"FLVER import."
            )

        # TODO: Delete all unused vertices at this point (i.e. vertices that were only used by degen faces)?

        bm.to_mesh(bl_mesh)
        bm.free()

        # Create and populate UV and vertex color data layers.
        for i, (uv_layer_name, merged_loop_uv_array) in enumerate(merged_mesh.loop_uvs.items()):
            self.operator.info(f"Creating UV layer {i}: {uv_layer_name}")
            uv_layer = bl_mesh.uv_layers.new(name=uv_layer_name, do_init=False)
            loop_uv_data = merged_loop_uv_array[valid_loop_indices].ravel()
            uv_layer.data.foreach_set("uv", loop_uv_data)
        for i, merged_color_array in enumerate(merged_mesh.loop_vertex_colors):
            self.operator.info(f"Creating Vertex Colors layer {i}: VertexColors{i}")
            color_layer = bl_mesh.vertex_colors.new(name=f"VertexColors{i}")
            loop_color_data = merged_color_array[valid_loop_indices].ravel()
            color_layer.data.foreach_set("color", loop_color_data)

        # Enable custom split normals and assign them.
        loop_normal_data = merged_mesh.loop_normals[valid_loop_indices]  # NOT raveled
        bl_mesh.create_normals_split()
        bl_mesh.normals_split_custom_set(loop_normal_data)  # one normal per loop
        bl_mesh.use_auto_smooth = True  # required for custom split normals to actually be used (rather than just face)
        bl_mesh.calc_normals_split()  # copy custom split normal data into API mesh loops

        bl_mesh.update()

        return merged_mesh.vertex_data["bone_weights"], merged_mesh.vertex_data["bone_indices"]

    def create_bone_vertex_groups(
        self,
        bl_mesh_obj: bpy.types.MeshObject,
        bl_vert_bone_weights: np.ndarray,
        bl_vert_bone_indices: np.ndarray,
    ):
        # Naming a vertex group after a Blender bone will automatically link it in the Armature modifier below.
        # NOTE: For imports that use an existing Armature (e.g. equipment), invalid bone names such as the root dummy
        # equipment bones have already been removed from `bl_bone_names` here.
        bone_vertex_groups = [
            bl_mesh_obj.vertex_groups.new(name=bone_name)
            for bone_name in self.bl_bone_names
        ]  # type: list[bpy.types.VertexGroup]

        # Awkwardly, we need a separate call to `VertexGroups[bone_index].add(indices, weight)` for each combination
        # of `bone_index` and `weight`, so the dictionary keys constructed above are a tuple of those two to minimize
        # the number of Blender group `add()` calls needed at the end of this function.
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

    def create_bones(
        self,
        bl_armature_obj: bpy.types.Object,
        base_edit_bone_length: float,
    ):
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
        """

        write_bone_type = ""
        warn_partial_bind_pose = False
        for mesh in self.flver.submeshes:
            if mesh.is_bind_pose:  # characters, objects, parts
                if not write_bone_type:
                    write_bone_type = "EDIT"  # write bone transforms to EditBones
                elif write_bone_type == "POSE":
                    warn_partial_bind_pose = True
                    write_bone_type = "EDIT"
                    break
            else:  # map pieces
                if not write_bone_type:
                    write_bone_type = "POSE"  # write bone transforms to PoseBones
                elif write_bone_type == "EDIT":
                    warn_partial_bind_pose = True
                    break  # keep EDIT default

        if not write_bone_type:
            # TODO: FLVER has no submeshes?
            self.warning(f"FLVER {self.name} has no submeshes. Bones written to EditBones.")
            write_bone_type = "EDIT"

        if warn_partial_bind_pose:
            self.warning(
                f"Some meshes in FLVER {self.name} use `is_bind_pose` (bone data written to EditBones) and some do not "
                f"(bone data written to PoseBones). Writing all bone data to EditBones."
            )

        # TODO: Theoretically, we could handled mixed bind pose/non-bind pose meshes IF AND ONLY IF they did not use the
        #  same bones. The bind pose bones could have their data written to EditBones, and the non-bind pose bones could
        #  have their data written to PoseBones. The 'is_bind_pose' custom property of each mesh can likewise be used on
        #  export, once it's confirmed that the same bone does not appear in both types of mesh.

        self.context.view_layer.objects.active = bl_armature_obj
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="EDIT", toggle=False)

        # noinspection PyTypeChecker
        armature_data = bl_armature_obj.data  # type: bpy.types.Armature
        # Create all edit bones. Head/tail are not set yet (depends on `write_bone_type` below).
        edit_bones = self.create_edit_bones(armature_data)

        # NOTE: Bones that have no vertices weighted to them are left as 'unused' root bones in the FLVER skeleton.
        # They may be animated by HKX animations (and will affect their children appropriately) but will not actually
        # affect any vertices in the mesh.

        if write_bone_type == "EDIT":
            self.write_data_to_edit_bones(edit_bones, base_edit_bone_length)
            del edit_bones  # clear references to edit bones as we exit EDIT mode
            if bpy.ops.object.mode_set.poll():
                bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        elif write_bone_type == "POSE":
            # This method will change back to OBJECT mode internally before setting pose bone data.
            self.write_data_to_pose_bones(bl_armature_obj, edit_bones, base_edit_bone_length)
        else:
            # Should not be possible to reach.
            raise ValueError(f"Invalid `write_bone_type`: {write_bone_type}")

    def create_edit_bones(self, bl_armature_data: bpy.types.Armature) -> list[bpy.types.EditBone]:
        """Create all edit bones from FLVER bones in `bl_armature`."""
        edit_bones = []  # all bones
        for game_bone, bl_bone_name in zip(self.flver.bones, self.bl_bone_names, strict=True):
            game_bone: FLVERBone
            edit_bone = bl_armature_data.edit_bones.new(bl_bone_name)  # '<DUPE>' suffixes already added to names
            edit_bone: bpy.types.EditBone

            # Storing 'Unused' flag for now. TODO: If later games' other flags can't be safely auto-detected, store too.
            edit_bone["Is Unused"] = bool(game_bone.usage_flags & FLVERBoneUsageFlags.UNUSED)

            # If this is `False`, then a bone's rest pose rotation will NOT affect its relative pose basis translation.
            # That is, pose basis translation will be interpreted as being in parent space (or object for root bones)
            # rather than in the 'rest pose space' of this bone. We don't want such behavior, particularly for FLVER
            # root bones like 'Pelvis'.
            edit_bone.use_local_location = True

            # FLVER bones never inherit scale.
            edit_bone.inherit_scale = "NONE"

            # We don't bother storing child or sibling bones. They are generated from parents on export.
            edit_bones.append(edit_bone)
        return edit_bones

    def write_data_to_edit_bones(self, edit_bones: list[bpy.types.EditBone], base_edit_bone_length: float):

        game_arma_transforms = self.flver.get_bone_armature_space_transforms()

        for game_bone, edit_bone, game_arma_transform in zip(
            self.flver.bones, edit_bones, game_arma_transforms, strict=True
        ):
            game_bone: FLVERBone
            game_translate, game_rotmat, game_scale = game_arma_transform

            if not is_uniform(game_scale, rel_tol=0.001):
                self.warning(f"Bone {game_bone.name} has non-uniform scale: {game_scale}. Left as identity.")
                bone_length = base_edit_bone_length
            elif any(c < 0.0 for c in game_scale):
                self.warning(f"Bone {game_bone.name} has negative scale: {game_scale}. Left as identity.")
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
                parent_bone_index = game_bone.parent_bone.get_bone_index(self.flver.bones)
                parent_edit_bone = edit_bones[parent_bone_index]
                edit_bone.parent = parent_edit_bone
                # edit_bone.use_connect = True

    def write_data_to_pose_bones(
        self,
        bl_armature_obj: bpy.types.Object,
        edit_bones: list[bpy.types.EditBone],
        base_edit_bone_length: float,
    ):
        for game_bone, edit_bone in zip(self.flver.bones, edit_bones, strict=True):
            # All edit bones are just Blender-Y-direction ("forward") stubs of base length.
            # This rigging makes map piece 'pose' bone data transform as expected for showing accurate vertex positions.
            edit_bone.head = Vector((0, 0, 0))
            edit_bone.tail = Vector((0, base_edit_bone_length, 0))

        del edit_bones  # clear references to edit bones as we exit EDIT mode
        self.operator.to_object_mode()

        pose_bones = bl_armature_obj.pose.bones
        for game_bone, pose_bone in zip(self.flver.bones, pose_bones):
            # TODO: Pose bone transforms are relative to parent (in both FLVER and Blender).
            #  Confirm map pieces still behave as expected, though (they shouldn't even have child bones).
            pose_bone.rotation_mode = "QUATERNION"  # should already be default, but being explicit
            game_translate, game_bone_rotate = game_bone.translate, game_bone.rotate
            pose_bone.location = GAME_TO_BL_VECTOR(game_translate)
            pose_bone.rotation_quaternion = GAME_TO_BL_EULER(game_bone_rotate).to_quaternion()
            pose_bone.scale = GAME_TO_BL_VECTOR(game_bone.scale)

    def create_dummy(
        self, game_dummy: Dummy, index: int, bl_armature: bpy.types.ArmatureObject
    ) -> bpy.types.Object:
        """Create an empty object that represents a FLVER 'dummy' (a generic 3D point).

        The reference ID of the dummy (the value used to refer to it in other game files/code) is included in the name,
        so that it can be easily modified. The format of the dummy name should therefore not be changed. (Note that the
        order of dummies does not matter, and multiple dummies can have the same reference ID.)

        All dummies are children of the armature, and most are children of a specific bone given in 'attach_bone_name'.
        As much as I'd like to nest them under another empty object, to properly attach them to the armature, they have
        to be direct children.
        """
        name = f"{self.name} Dummy<{index}> [{game_dummy.reference_id}]"
        bl_dummy = self.create_obj(name)  # no data (Empty)
        bl_dummy.parent = bl_armature
        bl_dummy.empty_display_type = "ARROWS"  # best display type/size I've found (single arrow not sufficient)
        bl_dummy.empty_display_size = 0.05

        if game_dummy.use_upward_vector:
            bl_rotation_euler = game_forward_up_vectors_to_bl_euler(game_dummy.forward, game_dummy.upward)
        else:  # TODO: I assume this is right (up-ignoring dummies only rotate around vertical axis)
            bl_rotation_euler = game_forward_up_vectors_to_bl_euler(game_dummy.forward, Vector3((0, 1, 0)))

        if game_dummy.parent_bone_index != -1:
            # Bone's FLVER translate is in the space of (i.e. relative to) this parent bone.
            # NOTE: This is NOT the same as the 'attach' bone, which is used as the actual Blender parent and
            # controls how the dummy moves during armature animations.
            bl_bone_name = self.bl_bone_names[game_dummy.parent_bone_index]
            bl_dummy["Parent Bone Name"] = bl_bone_name
            bl_parent_bone_matrix = bl_armature.data.bones[bl_bone_name].matrix_local
            bl_location = bl_parent_bone_matrix @ GAME_TO_BL_VECTOR(game_dummy.translate)
        else:
            # Bone's location is in armature space.
            bl_dummy["Parent Bone Name"] = ""
            bl_location = GAME_TO_BL_VECTOR(game_dummy.translate)

        # Dummy moves with this bone during animations.
        if game_dummy.attach_bone_index != -1:
            bl_dummy.parent_bone = self.bl_bone_names[game_dummy.attach_bone_index]
            bl_dummy.parent_type = "BONE"

        # We need to set the dummy's world matrix, rather than its local matrix, to bypass its possible bone
        # attachment above.
        bl_dummy.matrix_world = Matrix.LocRotScale(bl_location, bl_rotation_euler, Vector((1.0, 1.0, 1.0)))

        # NOTE: Reference ID not included as a property.
        # bl_dummy["reference_id"] = dummy.reference_id  # int
        bl_dummy["Color RGBA"] = game_dummy.color_rgba  # RGBA  # TODO: Use in actual display somehow?
        bl_dummy["Flag 1"] = game_dummy.flag_1  # bool
        bl_dummy["Use Upward Vector"] = game_dummy.use_upward_vector  # bool
        # NOTE: These two properties are only ever non-zero in Sekiro (and probably Elden Ring).
        bl_dummy["Unk x30"] = game_dummy.unk_x30  # int
        bl_dummy["Unk x34"] = game_dummy.unk_x34  # int

        return bl_dummy

    def create_obj(self, name: str, data=None):
        """Create a new Blender object with given `data` and link it to the scene's object collection."""
        obj = bpy.data.objects.new(name, data)
        self.collection.objects.link(obj)
        self.new_objs.append(obj)
        return obj

    def warning(self, msg: str):
        self.operator.warning(msg)
