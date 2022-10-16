"""
Import FLVER files (with/without DCX) into Blender 3.3+ (Python 3.10+ scripting required).

The FLVER is imported as an Armature object with all FLVER sub-meshes as Mesh children. Critical FLVER information is
stored with custom properties as necessary.

Currently only thoroughly tested for DS1/DSR map pieces, including map pieces with multiple root bones. Models with real
bone hierarchies (i.e., basically everything except map pieces) will likely not be set up correctly. Non-map materials
that use non-[M] MTD shaders will likely also not appear correctly.
"""
from __future__ import annotations

__all__ = ["FLVERImporter"]

import os
import re
import typing as tp
from pathlib import Path

import bpy
import bpy_types
import bmesh
from mathutils import Vector

from .core import Transform, FLVERImportError

if tp.TYPE_CHECKING:
    from io_flver import ImportFLVER
    from soulstruct.base.models.flver import FLVER
    from soulstruct.containers.tpf import TPFTexture


# TODO: Turn into import settings.
NORMAL_MAP_STRENGTH = 0.4
ROUGHNESS = 0.75

ARMATURE_RE = re.compile(r"(.*) Armature Obj")


class FLVERImporter:
    """Manages imports for a batch of FLVER files imported simultaneously."""

    flver: tp.Optional[FLVER]
    name: str
    dds_images: dict[str, tp.Any]  # values can be string DDS paths or loaded Blender images

    def __init__(
        self,
        operator: ImportFLVER,
        context,
        texture_sources: dict[str, TPFTexture] = None,
        dds_dump_path: tp.Optional[Path] = None,
        enable_alpha_hashed=True,
    ):
        self.operator = operator
        self.context = context

        if texture_sources and dds_dump_path:
            self.warning("TPF sources *and* a DDS dump path were given. DDS dump path will be preferred.")
        self.dds_dump_path = dds_dump_path
        # These TPF sources and images are shared between all FLVER files imported with this `FLVERImporter` instance.
        self.texture_sources = texture_sources
        self.dds_images = {}
        self.enable_alpha_hashed = enable_alpha_hashed

        self.flver = None
        self.name = ""
        self.all_bl_objs = []
        self.materials = {}

    def import_flver(self, flver: FLVER, file_path: Path, transform: tp.Optional[Transform] = None):
        """Read a FLVER into a collection of Blender mesh objects (and one Armature).

        TODO: Currently designed only with map pieces in mind, not characters/objects.
        """
        self.flver = flver
        self.name = file_path.name.split(".")[0]  # drop all extensions

        # Set mode to OBJECT and deselect all objects.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action="DESELECT")
        bl_armature = self.create_bones()
        if bpy.ops.object.mode_set.poll():  # just to be safe
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        if transform is not None:
            bl_armature.location = transform.bl_translate
            bl_armature.rotation_euler = transform.bl_rotate
            bl_armature.scale = transform.bl_scale

        self.all_bl_objs = [bl_armature]
        self.materials = {}

        # TODO: Would be better to do some other basic FLVER validation here before loading the TPFs.
        if self.flver.gx_lists:
            self.warning(
                f"FLVER {self.name} has GX lists, which are not yet supported by the importer. They will be lost."
            )

        if self.dds_dump_path:
            for texture_path in self.flver.get_all_texture_paths():
                dds_path = self.dds_dump_path / f"{texture_path.stem}.dds"
                if dds_path.is_file():
                    # print(f"Loading dumped DDS: {dds_path}")
                    self.dds_images[str(texture_path)] = bpy.data.images.load(str(dds_path))
                else:
                    self.warning(f"Could not find DDS for texture '{texture_path}' in FLVER {self.name}.")

        if self.operator.load_map_piece_tpfs:
            temp_dir = Path(bpy.utils.resource_path("USER"))
            for texture_path in self.flver.get_all_texture_paths():
                if str(texture_path) in self.dds_images:
                    continue  # already loaded (or dumped DDS file found)
                try:
                    texture = self.texture_sources[texture_path.stem]  # without `tga` extension
                except KeyError:
                    self.warning(f"Could not find TPF with texture '{texture_path}' in FLVER {self.name}.")
                    continue
                dds_path = temp_dir / f"{texture_path.stem}.dds"
                try:
                    texture.write_dds(dds_path)
                    print(
                        f"Attempting to load texture {texture.name} with format {texture.get_dds_format()}..."
                    )
                    self.dds_images[str(texture_path)] = image = bpy.data.images.load(str(dds_path))
                    image.pack()  # embed DDS in `.blend` file so temporary DDS file can be deleted
                    # Note that the full interroot path is stored in the texture node name.
                finally:
                    if dds_path.exists():
                        os.remove(str(dds_path))

        # Note that materials with two sets of textures receive two BSDF nodes mixed 50/50.
        self.materials = {
            i: self.create_material(flver_material)
            for i, flver_material in enumerate(self.flver.materials)
        }

        for i, flver_mesh in enumerate(self.flver.meshes):
            mesh_name = f"{self.name} Mesh {i}"
            bl_obj = self.create_mesh_obj(flver_mesh, mesh_name)
            bl_obj["Face Set Count"] = len(flver_mesh.face_sets)  # custom property

    def create_material(self, flver_material, use_existing=True):
        """Create a Blender material that represents a single FLVER materials.

        FLVER materials with multiple texture slots are represented in Blender by a single Material, using vertex colors
        to drive a Mix Shader (appears as in-game). Currently, only two slots are supported; I don't thnk more are ever
        used in DS1.

        If only one material is present, its alpha will be set using vertex colors.

        Some FLVER materials also have a "g_Height" texture. This is represented by a material displacement map (rather
        than a bump map for one BDSF).

        If `use_existing=False`, a new material will be created with the FLVER's values even if a material with that
        name already exists in the Blender environment. Be wary of texture RAM usage in this case! Make sure you delete
        unneeded materials from Blender as you go.
        """
        # Material name (not important) and MTD path (important) are combined in Blender material name.
        material_name = f"{flver_material.name} | {flver_material.mtd_path}"

        existing_material = bpy.data.materials.get(material_name)
        if existing_material is not None:
            if use_existing:
                return existing_material
            # TODO: Should append '<i>' to duplicated name of new material...

        # TODO: Finesse node coordinates.

        bl_material = bpy.data.materials.new(name=material_name)
        bl_material.use_nodes = True
        nt = bl_material.node_tree
        nt.nodes.remove(nt.nodes["Principled BSDF"])
        bl_material["flags"] = str(flver_material.flags)  # custom property
        output_node = nt.nodes["Material Output"]

        bsdf_1 = self.create_bsdf_node(flver_material, nt, is_second_slot=False)

        vertex_colors_node = nt.nodes.new("ShaderNodeAttribute")
        vertex_colors_node.location = (-200, 430)
        vertex_colors_node.name = vertex_colors_node.attribute_name = "VertexColors"

        mix_shader = nt.nodes.new("ShaderNodeMixShader")
        mix_shader.location[1] += 300  # leaves room for possible displacement map node

        if any(texture.texture_type.endswith("_2") for texture in flver_material.textures):
            bsdf_2 = self.create_bsdf_node(flver_material, nt, is_second_slot=True)
            # Vertex colors are weights for blending between the two textures.
            nt.links.new(vertex_colors_node.outputs["Alpha"], mix_shader.inputs["Fac"])
            nt.links.new(bsdf_1.outputs["BSDF"], mix_shader.inputs[1])
            nt.links.new(bsdf_2.outputs["BSDF"], mix_shader.inputs[2])
            nt.links.new(mix_shader.outputs["Shader"], output_node.inputs["Surface"])
        else:
            holdout = nt.nodes.new("ShaderNodeHoldout")
            holdout.location = (-200, 150)
            # Vertex colors are weights for blending between Holdout and single texture.
            nt.links.new(vertex_colors_node.outputs["Alpha"], mix_shader.inputs["Fac"])
            nt.links.new(holdout.outputs["Holdout"], mix_shader.inputs[1])  # NOTE: zero `Fac` -> fully holdout
            nt.links.new(bsdf_1.outputs["BSDF"], mix_shader.inputs[2])
            nt.links.new(mix_shader.outputs["Shader"], output_node.inputs["Surface"])

            if self.enable_alpha_hashed:
                # TODO: Eevee viewport 'BLEND' isn't perfect, as it uses object position for rendering depth, but all
                #  FLVER submesh objects will have the same position. 'HASHED' is better, apparently.
                bl_material.blend_method = "HASHED"  # show alpha in viewport

        try:
            height_texture = next(texture for texture in flver_material.textures if texture.texture_type == "g_Height")
        except StopIteration:
            pass  # no height map
        else:
            height_node = nt.nodes.new("ShaderNodeTexImage")
            height_node.location = (-550, 345)
            height_node.name = f"{height_texture.texture_type} | {height_texture.path}"
            if self.dds_images:
                try:
                    height_node.image = self.dds_images[height_texture.path]
                except KeyError:
                    self.warning(f"Could not find TPF texture: {height_texture.path}")
            displace_node = nt.nodes.new("ShaderNodeDisplacement")
            displace_node.location[1] += 170
            nt.links.new(nt.nodes["UVMap1"].outputs["Vector"], height_node.inputs["Vector"])
            nt.links.new(height_node.outputs["Color"], displace_node.inputs["Normal"])
            nt.links.new(displace_node.outputs["Displacement"], output_node.inputs["Displacement"])

        # TODO: Should check for unexpected texture names, like "g_Height_2".
        # TODO: Should also confirm "g_DetailBumpmap" has no content.

        return bl_material

    def create_bsdf_node(self, flver_material, node_tree, is_second_slot: bool):
        bsdf = node_tree.nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location[1] = 0 if is_second_slot else 1000
        bsdf.inputs["Roughness"].default_value = ROUGHNESS

        textures = flver_material.get_texture_dict()
        slot = "_2" if is_second_slot else ""
        slot_y_offset = 0 if is_second_slot else 1000

        uv_attr = node_tree.nodes.new("ShaderNodeAttribute")
        uv_attr.name = uv_attr.attribute_name = "UVMap2" if is_second_slot else "UVMap1"
        uv_attr.location = (-750, 0 + slot_y_offset)

        if "g_Diffuse" + slot in textures:
            texture = textures["g_Diffuse" + slot]
            node = node_tree.nodes.new("ShaderNodeTexImage")
            node.location = (-550, 330 + slot_y_offset)
            node.name = f"g_Diffuse{slot} | {texture.path}"
            if self.dds_images:
                try:
                    node.image = self.dds_images[texture.path]
                except KeyError:
                    self.warning(f"Could not find TPF texture: {texture.path}")

            node_tree.links.new(uv_attr.outputs["Vector"], node.inputs["Vector"])
            node_tree.links.new(node.outputs["Color"], bsdf.inputs["Base Color"])
            node_tree.links.new(node.outputs["Alpha"], bsdf.inputs["Alpha"])

        if "g_Specular" + slot in textures:
            texture = textures["g_Specular" + slot]
            node = node_tree.nodes.new("ShaderNodeTexImage")
            node.location = (-550, 0 + slot_y_offset)
            node.name = f"g_Specular{slot} | {texture.path}"
            if self.dds_images:
                try:
                    node.image = self.dds_images[texture.path]
                except KeyError:
                    self.warning(f"Could not find TPF texture: {texture.path}")

            node_tree.links.new(uv_attr.outputs["Vector"], node.inputs["Vector"])
            node_tree.links.new(node.outputs["Color"], bsdf.inputs["Specular"])

        if "g_Bumpmap" + slot in textures:
            texture = textures["g_Bumpmap" + slot]

            node = node_tree.nodes.new("ShaderNodeTexImage")
            node.location = (-550, -330 + slot_y_offset)
            node.name = f"g_Bumpmap{slot} | {texture.path}"
            if self.dds_images:
                try:
                    node.image = self.dds_images[texture.path]
                except KeyError:
                    self.warning(f"Could not find TPF texture: {texture.path}")

            normal_map_node = node_tree.nodes.new("ShaderNodeNormalMap")
            normal_map_node.name = "NormalMap2" if is_second_slot else "NormalMap"
            normal_map_node.space = "TANGENT"
            normal_map_node.uv_map = "UVMap2" if is_second_slot else "UVMap1"
            normal_map_node.inputs["Strength"].default_value = NORMAL_MAP_STRENGTH
            normal_map_node.location = (-200, -400 + slot_y_offset)

            node_tree.links.new(uv_attr.outputs["Vector"], node.inputs["Vector"])
            node_tree.links.new(node.outputs["Color"], normal_map_node.inputs["Color"])
            node_tree.links.new(normal_map_node.outputs["Normal"], bsdf.inputs["Normal"])

        return bsdf

    def create_mesh_obj(
        self,
        flver_mesh: FLVER.Mesh,
        mesh_name: str,
    ):
        """Create a Blender mesh object.

        Data is stored in the following ways:
            vertices are simply `vertex.position` remapped as (-x, y, z)
            edges are not used
            faces are `face_set.get_triangles()`; only index 0 (maximum detail face set) is used
            normals are simply `vertex.normal` remapped as (-x, y, z)
                - note that normals are stored under loops, e.g. `mesh.loops[i].normal`
                - can iterate over loops and copy each normal to vertex `loop.vertex_index`

        Vertex groups are used to rig vertices to bones.
        """
        bl_mesh = bpy.data.meshes.new(name=f"{mesh_name} Data")

        if flver_mesh.invalid_vertex_size:
            # Corrupted mesh. Leave empty.
            return self.create_obj(f"{mesh_name} Obj <INVALID>", bl_mesh)

        uv_count = max(len(vertex.uvs) for vertex in flver_mesh.vertices)

        vertices = [(-v.position[0], -v.position[2], v.position[1]) for v in flver_mesh.vertices]
        edges = []  # no edges in FLVER
        faces = flver_mesh.face_sets[0].get_triangles(allow_primitive_restarts=False)

        bl_mesh.from_pydata(vertices, edges, faces)
        bl_mesh.materials.append(self.materials[flver_mesh.material_index])

        bm = bmesh.new()
        if bpy.context.mode == "EDIT_MESH":
            bm.from_edit_mesh(bl_mesh)
        else:
            bm.from_mesh(bl_mesh)

        # To create normals, we create custom "split" normals, and copy them to the loop normals.
        # There is no point setting the non-custom vertex normals; Blender recomputes them very aggressively. We use
        # `calc_normals_split()` on export and use the loop normals to get what we need.
        bl_mesh.create_normals_split()
        # NOTE: X is negated, but Y and Z are not swapped here, as the global mesh transformation below will do that.
        # (Unfortunately I only discovered this bug on 2021-08-08.)
        bl_vertex_normals = [(-v.normal[0], -v.normal[2], v.normal[1]) for v in flver_mesh.vertices]
        for loop in bl_mesh.loops:
            # I think vertex normals need to be copied to loop (vertex-per-face) normals.
            loop.normal[:] = bl_vertex_normals[loop.vertex_index]
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        bm.faces.index_update()
        bm.to_mesh(bl_mesh)

        # TODO: I need to store exactly which information is contained in each vertex, so I can reconstruct proper
        #  vertex buffers on export.

        # Note that we don't assign these UV and vertex color layers as they're created, because their address may
        # change as other layers are created, leading to random internal errors.
        for uv_index in range(uv_count):
            bl_mesh.uv_layers.new(name=f"UVMap{uv_index + 1}", do_init=False)
        bl_mesh.vertex_colors.new(name="VertexColors")

        # Access layers at their final addresses.
        uv_layers = []
        for uv_index in range(uv_count):
            uv_layers.append(bl_mesh.uv_layers[f"UVMap{uv_index + 1}"])
        vertex_colors = bl_mesh.vertex_colors["VertexColors"]

        # In Blender, UVs and vertex colors must be set per loop, whereas they are per vertex in FLVER. Every loop using
        # the same vertex will have the same UVs and vertex color, and this will also be enforced on export, so make
        # sure to preserve per-vertex data if you edit either property in Blender.
        for j, loop in enumerate(bl_mesh.loops):
            loop: bpy.types.MeshLoop
            vertex = flver_mesh.vertices[loop.vertex_index]
            for uv_index, uv in enumerate(vertex.uvs):
                uv_layers[uv_index].data[j].uv[:] = [uv[0], -uv[1]]  # Z axis discarded, Y axis inverted
            if len(vertex.colors) != 1:
                raise FLVERImportError(
                    f"Vertex {loop.vertex_index} in FLVER mesh {mesh_name} has {len(vertex.colors)} vertex colors. "
                    f"Expected exactly one."
                )
            vertex_colors.data[j].color[:] = vertex.colors[0]

        bl_mesh.update()
        bl_mesh.calc_normals_split()

        # Delete vertices not used in face set 0. We do this after setting UVs and other layers above.
        bm = bmesh.new()
        if bpy.context.mode == "EDIT_MESH":
            bm.from_edit_mesh(bl_mesh)
        else:
            bm.from_mesh(bl_mesh)
        bm.verts.ensure_lookup_table()
        used_vertex_indices = {i for face in faces for i in face}
        unused_vertex_indices = [i for i in range(len(bm.verts)) if i not in used_vertex_indices]
        bl_vertex_normals = [n for i, n in enumerate(bl_vertex_normals) if i in used_vertex_indices]
        for bm_vert in [bm.verts[i] for i in unused_vertex_indices]:
            bm.verts.remove(bm_vert)
        bm.verts.index_update()
        bm.faces.index_update()
        bm.to_mesh(bl_mesh)

        # noinspection PyTypeChecker
        bl_mesh.normals_split_custom_set_from_vertices(bl_vertex_normals)
        bl_mesh.use_auto_smooth = False  # modifies `calc_normals_split()` outcome upon export

        bl_mesh_obj = self.create_obj(f"{mesh_name} Obj", bl_mesh)
        self.context.view_layer.objects.active = bl_mesh_obj

        bone_vertex_groups = []  # type: list[bpy.types.VertexGroup]
        bone_vertex_group_indices = {}

        # TODO: I *believe* that vertex bone indices are global if and only if `mesh.bone_indices` is empty. (In DSR,
        #  it's never empty.)
        if flver_mesh.bone_indices:
            # print(f"Bone indices: {flver_mesh.bone_indices}")
            for mesh_bone_index in flver_mesh.bone_indices:
                group = bl_mesh_obj.vertex_groups.new(name=self.armature.pose.bones[mesh_bone_index].name)
                bone_vertex_groups.append(group)
            for i, fl_vert in enumerate(flver_mesh.vertices):
                # TODO: May be able to assert that this is ALWAYS true for ALL vertices in map pieces.
                if all(weight == 0.0 for weight in fl_vert.bone_weights) and len(set(fl_vert.bone_indices)) == 1:
                    # Map Piece FLVERs use a single duplicated index and no weights.
                    v_bone_index = fl_vert.bone_indices[0]
                    bone_vertex_group_indices.setdefault((v_bone_index, 1.0), []).append(i)
                else:
                    # Standard multi-bone weighting.
                    for v_bone_index, v_bone_weight in zip(fl_vert.bone_indices, fl_vert.bone_weights):
                        if v_bone_weight == 0.0:
                            continue
                        bone_vertex_group_indices.setdefault((v_bone_index, v_bone_weight), []).append(i)
        else:  # vertex bone indices are global...?
            for bone_index in range(len(self.armature.pose.bones)):
                group = bl_mesh_obj.vertex_groups.new(name=self.armature.pose.bones[bone_index].name)
                bone_vertex_groups.append(group)
            for i, fl_vert in enumerate(flver_mesh.vertices):
                for v_bone_index, v_bone_weight in zip(fl_vert.bone_indices, fl_vert.bone_weights):
                    if v_bone_weight == 0.0:
                        continue
                    bone_vertex_group_indices.setdefault((v_bone_index, v_bone_weight), []).append(i)

        # Awkwardly, we need a separate call to `VertexGroups[bone_index].add(indices, weight)` for each combination
        # of `bone_index` and `weight`, so the dictionary keys constructed below are a tuple of those two to
        # minimize the number of `add()` calls needed below.
        for (bone_index, bone_weight), bone_vertices in bone_vertex_group_indices.items():
            bone_vertex_groups[bone_index].add(bone_vertices, bone_weight, "ADD")

        bpy.ops.object.modifier_add(type="ARMATURE")
        armature_mod = bl_mesh_obj.modifiers["Armature"]
        armature_mod.object = self.armature
        armature_mod.show_in_editmode = True
        armature_mod.show_on_cage = True
        return bl_mesh_obj

    def create_bones(self):
        """Create FLVER bones in Blender.

        Bones are a little confusing in Blender. See:
            https://docs.blender.org/api/blender_python_api_2_71_release/info_gotcha.html#editbones-posebones-bone-bones

        The short story is that the "resting state" of each bone, including its head and tail position, is created in
        EDIT mode (as `EditBone` instances). This data will typically not be edited again when posing/animating a mesh
        that is rigged to those bones' Armature. Instead, the bones are accessed as `PoseBone` instances in POSE mode,
        where they are treated like objects with transform data.

        If a FLVER bone has a parent bone, its FLVER transform is given relative to its parent's frame of reference.
        Determining the final position of any given bone in world space therefore requires all of its parents'
        transforms to be accumulated from the root down.

        Note that while bones are typically used for characters, objects, and parts (e.g. armor/weapons), they are also
        occasionally used by map pieces to position elements (sometimes animated) like foliage, and even walls. When
        this happens, so far, the bones have always been root bones, and basically function as anchors for particular
        meshes of that FLVER, or even potentially just a subset of its vertices.

        NOTE: Because we want to see character models "unposed" (with EDIT BONE transforms set by the FLVER bone data),
        but we want to see map piece models "posed" (with POSE BONE transforms set by the FLVER bone data), bones are
        treated differently for the two model types. This is detected by checking vertex bone weights, which are always
        zero for map pieces (-> pose bones) and always have at least one non-zero value for characters (-> edit bones).

        The AABB of each bone is presumably generated to include all vertices that use that bone as a weight.
        """
        bl_armature = bpy.data.armatures.new(f"{self.name} Armature")
        bl_armature_obj = self.create_obj(f"FLVER {self.name}", bl_armature, parent_to_armature=False)

        use_pose_transforms = self.flver.check_if_all_zero_bone_weights()

        self.context.view_layer.objects.active = bl_armature_obj
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="EDIT", toggle=False)

        def get_bone_name(index_: int, flver_bone_name_: str):
            return f"{self.name} Bone {index_} {flver_bone_name_}"

        edit_bones = []  # all bones
        for i, flver_bone in enumerate(self.flver.bones):
            edit_bone = bl_armature_obj.data.edit_bones.new(f"{self.name} Bone {flver_bone.name}")
            edit_bone: bpy_types.EditBone
            if flver_bone.next_sibling_index != -1:
                next_b = self.flver.bones[flver_bone.next_sibling_index]
                edit_bone["Next Sibling Bone"] = get_bone_name(flver_bone.next_sibling_index, next_b.name)
            if flver_bone.previous_sibling_index != -1:
                previous_b = self.flver.bones[flver_bone.previous_sibling_index]
                edit_bone["Previous Sibling Bone"] = get_bone_name(flver_bone.previous_sibling_index, previous_b.name)
            edit_bones.append(edit_bone)

        # Assign parent bones in Blender and create head/tail.
        for flver_bone, edit_bone in zip(self.flver.bones, edit_bones):
            flver_tail = flver_bone.get_absolute_translate(self.flver.bones)
            edit_bone.tail = (-flver_tail[0], -flver_tail[2], flver_tail[1])

            if flver_bone.parent_index != -1:
                # Bone does not need a head; will be set to parent's tail.
                parent_edit_bone = edit_bones[flver_bone.parent_index]
                edit_bone.parent = parent_edit_bone
                edit_bone.use_connect = True
            else:
                # Head of root bone placed at origin.
                edit_bone.head = (0.0, 0.0, 0.0)

            # print(f"{edit_bone.name}:\n  Head: {edit_bone.head}\n  Tail: {edit_bone.tail}\n  Parent: }")

        # TODO: may want to test removing this
        del edit_bones  # clear references to edit bones as we exit EDIT mode

        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        if use_pose_transforms:
            #
            for pose_bone, flver_bone in zip(bl_armature_obj.pose.bones, self.flver.bones):
                t = flver_bone.translate
                pose_bone.location = Vector((-t.x, t.y, t.z))  # CORRECT
                r = flver_bone.rotate
                pose_bone.rotation_mode = "XYZ"  # has to be done before setting `.rotation_euler` (zeroes it)
                pose_bone.rotation_euler = Vector((r.x, -r.y, r.z))  # TODO: Y correct, but X and Z not confirmed
                pose_bone.scale = Vector(flver_bone.scale)
                # TODO: Bounding box? Can it be automatically generated from, say, a mesh's vertices min/max relative to
                #  the mesh's bone...?

        return bl_armature_obj

    def create_obj(self, name: str, data=None, parent_to_armature=True):
        """Create a new Blender object as a child to the FLVER's parent empty.

        I don't know how `new()` handles defaults, so the `data` argument isn't used if `data=None`.
        """
        obj = bpy.data.objects.new(name, data) if data is not None else bpy.data.objects.new(name)
        self.context.scene.collection.objects.link(obj)
        self.all_bl_objs.append(obj)
        if parent_to_armature:
            obj.parent = self.all_bl_objs[0]

        return obj

    def warning(self, warning: str):
        print(f"# WARNING: {warning}")
        self.operator.report({"WARNING"}, warning)

    @property
    def armature(self):
        return self.all_bl_objs[0]
