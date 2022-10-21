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

import math
import re
import typing as tp
from pathlib import Path

import bpy
import bpy_types
import bmesh
from mathutils import Euler, Vector, Matrix

from soulstruct.utilities.maths import Vector3

from .core import Transform, FLVERImportError, fl_forward_up_vectors_to_bl_euler, is_uniform
from .textures import load_tpf_texture_as_png

if tp.TYPE_CHECKING:
    from io_flver import ImportFLVER
    from soulstruct.base.models.flver import FLVER
    from soulstruct.containers.tpf import TPFTexture


# TODO: Turn into import settings.
NORMAL_MAP_STRENGTH = 0.4
ROUGHNESS = 0.75

ARMATURE_RE = re.compile(r"(.*) Armature Obj")


# Blender matrix to convert from FromSoft space to Blender space.
FL_TO_BL_SPACE_POS = Matrix((
    (-1.0, 0.0, 0.0),
    (0.0, 0.0, -1.0),
    (0.0, 1.0, 0.0),
))
FL_TO_BL_SPACE_ROT = Matrix((
    (1.0, 0.0, 0.0),
    (0.0, 0.0, 1.0),
    (0.0, -1.0, 0.0),
))


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

        self.dds_dump_path = dds_dump_path
        # These DDS sources/images are shared between all FLVER files imported with this `FLVERImporter` instance.
        self.texture_sources = texture_sources
        self.dds_images = {}
        self.enable_alpha_hashed = enable_alpha_hashed

        self.flver = None
        self.name = ""
        self.bl_bone_names = {}  # type: dict[int, str]
        self.all_bl_objs = []
        self.materials = {}

    def import_flver(self, flver: FLVER, file_path: Path, transform: tp.Optional[Transform] = None):
        """Read a FLVER into a collection of Blender mesh objects (and one Armature).

        TODO:
            - Not fully happy with how duplicate materials are handled.
                - If an existing material is found, but has no texture images, maybe just load those into it.
        """
        self.flver = flver
        self.name = file_path.name.split(".")[0]  # drop all extensions

        # Create FLVER bone index -> Blender bone name dictionary. (Blender names are UTF-8.)
        self.bl_bone_names.clear()
        for bone_index, bone in enumerate(self.flver.bones):
            # TODO: Just using actual bone names to avoid the need for parsing rules on export.
            # self.bl_bone_names[bone_index] = f"{self.name} Bone({bone_index}) {bone.name}"
            self.bl_bone_names[bone_index] = bone.name

        # Set mode to OBJECT and deselect all objects.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action="DESELECT")
        bl_armature = self.create_bones()
        if bpy.ops.object.mode_set.poll():  # just to be safe
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        # Assign basic FLVER header information as custom props.
        # TODO: Configure a full-exporter dropdown/choice of game version that defaults as many of these as possible.
        bl_armature["endian"] = self.flver.header.endian  # bytes
        bl_armature["version"] = self.flver.header.version.name  # str
        bl_armature["unicode"] = self.flver.header.unicode  # bool
        bl_armature["unk_x4a"] = self.flver.header.unk_x4a  # bool
        bl_armature["unk_x4c"] = self.flver.header.unk_x4c  # int
        bl_armature["unk_x5c"] = self.flver.header.unk_x5c  # int
        bl_armature["unk_x5d"] = self.flver.header.unk_x5d  # int
        bl_armature["unk_x68"] = self.flver.header.unk_x68  # int

        if transform is not None:
            bl_armature.location = transform.bl_translate
            bl_armature.rotation_euler = transform.bl_rotate
            bl_armature.scale = transform.bl_scale

        self.all_bl_objs = [bl_armature]
        self.materials = {}

        if self.flver.gx_lists:
            self.warning(
                f"FLVER {self.name} has GX lists, which are not yet supported by the importer. They will be lost."
            )

        # TODO: Would be better to do some other basic FLVER validation here before loading the TPFs.
        if self.texture_sources or self.dds_dump_path:
            self.load_texture_images()
        else:
            self.warning("No TPF files or DDS dump folder given. No textures loaded for FLVER.")

        # Note that materials with two sets of textures receive two BSDF nodes mixed 50/50.
        self.materials = {
            i: self.create_material(flver_material)
            for i, flver_material in enumerate(self.flver.materials)
        }

        for i, flver_mesh in enumerate(self.flver.meshes):
            mesh_name = f"{self.name} Mesh {i}"
            bl_obj = self.create_mesh_obj(flver_mesh, mesh_name)
            bl_obj["face_set_count"] = len(flver_mesh.face_sets)  # custom property

        self.create_dummies()

    def load_texture_images(self):
        """Load texture images from either `dds_dump` folder or TPFs found with the FLVER."""
        for texture_path in self.flver.get_all_texture_paths():
            if str(texture_path) in self.dds_images:
                continue  # already loaded
            if texture_path.stem in self.texture_sources:
                texture = self.texture_sources[texture_path.stem]
                bl_image = load_tpf_texture_as_png(texture)
                self.dds_images[str(texture_path)] = bl_image
                # Note that the full interroot path is stored in the texture node name.
            elif self.dds_dump_path:
                dds_path = self.dds_dump_path / f"{texture_path.stem}.dds"
                if dds_path.is_file():
                    # print(f"Loading dumped DDS texture: {texture_path.stem}.dds")
                    self.dds_images[str(texture_path)] = bpy.data.images.load(str(dds_path))
                else:
                    self.warning(f"Could not find TPF or dumped texture '{texture_path.stem}' for FLVER '{self.name}'.")

    def create_material(self, flver_material, use_existing=True):
        """Create a Blender material that represents a single `FLVER.Material`.

        NOTE: Actual information contained in the FLVER and used for export is stored in custom properties of the
        Blender material. The node graph generated here is simply for (very helpful) visualization in Blender, and is
        NOT synchronized at all with the custom properties.

        If `use_existing=False`, a new material will be created with the FLVER's values even if a material with that
        name already exists in the Blender environment. Be wary of texture RAM usage in this case! Make sure you delete
        unneeded materials from Blender as you go.
        """

        existing_material = bpy.data.materials.get(flver_material.name)
        if existing_material is not None:
            if use_existing:
                return existing_material
            # TODO: Should append '<i>' to duplicated name of new material...

        bl_material = bpy.data.materials.new(name=flver_material.name)
        if self.enable_alpha_hashed:
            bl_material.blend_method = "HASHED"  # show alpha in viewport

        # Critical `Material` information stored in custom properties.
        bl_material["material_mtd_path"] = flver_material.mtd_path  # str
        bl_material["material_flags"] = flver_material.flags  # int
        bl_material["material_gx_index"] = flver_material.gx_index  # int
        bl_material["material_unk_x18"] = flver_material.unk_x18  # int
        bl_material["material_texture_count"] = len(flver_material.textures)  # int

        # Texture information is also stored here.
        for i, fl_tex in enumerate(flver_material.textures):
            bl_material[f"texture[{i}]_path"] = fl_tex.path  # str
            bl_material[f"texture[{i}]_texture_type"] = fl_tex.texture_type  # str
            bl_material[f"texture[{i}]_scale"] = tuple(fl_tex.scale)  # tuple (float)
            bl_material[f"texture[{i}]_unk_x10"] = fl_tex.unk_x10  # int
            bl_material[f"texture[{i}]_unk_x11"] = fl_tex.unk_x11  # bool
            bl_material[f"texture[{i}]_unk_x14"] = fl_tex.unk_x14  # float
            bl_material[f"texture[{i}]_unk_x18"] = fl_tex.unk_x18  # float
            bl_material[f"texture[{i}]_unk_x1C"] = fl_tex.unk_x1C  # float

        mtd_bools = flver_material.get_mtd_bools()

        bl_material.use_nodes = True
        nt = bl_material.node_tree
        nt.nodes.remove(nt.nodes["Principled BSDF"])
        output_node = nt.nodes["Material Output"]

        # TODO: Finesse node coordinates.

        bsdf_1, diffuse_node_1 = self.create_bsdf_node(flver_material, mtd_bools, nt, is_second_slot=False)
        bsdf_2 = diffuse_node_2 = None

        vertex_colors_node = nt.nodes.new("ShaderNodeAttribute")
        vertex_colors_node.location = (-200, 430)
        vertex_colors_node.name = vertex_colors_node.attribute_name = "VertexColors"

        if mtd_bools["multiple"] or mtd_bools["alpha"]:
            # Use a mix shader weighted by vertex alpha.
            slot_mix_shader = nt.nodes.new("ShaderNodeMixShader")
            slot_mix_shader.location = (50, 300)
            nt.links.new(vertex_colors_node.outputs["Alpha"], slot_mix_shader.inputs["Fac"])
            nt.links.new(slot_mix_shader.outputs["Shader"], output_node.inputs["Surface"])
        else:
            slot_mix_shader = None
            nt.links.new(bsdf_1.outputs["BSDF"], output_node.inputs["Surface"])

        if mtd_bools["multiple"]:
            # Multi-textures shader (two slots).
            bsdf_2, diffuse_node_2 = self.create_bsdf_node(flver_material, mtd_bools, nt, is_second_slot=True)
            nt.links.new(bsdf_1.outputs["BSDF"], slot_mix_shader.inputs[1])
            nt.links.new(bsdf_2.outputs["BSDF"], slot_mix_shader.inputs[2])
        elif mtd_bools["alpha"]:
            # Single-texture shader (one slot). We mix with Transparent BSDF to render vertex alpha.
            # TODO: Could I not just multiply texture alpha and vertex alpha?
            transparent = nt.nodes.new("ShaderNodeBsdfTransparent")
            transparent.location = (-200, 230)
            nt.links.new(transparent.outputs["BSDF"], slot_mix_shader.inputs[1])
            nt.links.new(bsdf_1.outputs["BSDF"], slot_mix_shader.inputs[2])
        # TODO: Not sure if I can easily support 'edge' shader alpha.
        else:
            # Single texture, no alpha. Wait to see if lightmap used below.
            pass

        if mtd_bools["height"]:
            height_texture = flver_material.find_texture_type("g_Height")
            if height_texture is None:
                raise ValueError(
                    f"Material {flver_material.name} has MTD {flver_material.mtd_name} but no 'g_Height' texture."
                )
            height_node = nt.nodes.new("ShaderNodeTexImage")
            height_node.location = (-550, 345)
            height_node.name = f"{height_texture.texture_type} | {height_texture.path}"
            height_node.image = self.get_dds_image(height_texture.path)
            displace_node = nt.nodes.new("ShaderNodeDisplacement")
            displace_node.location = (-250, 170)
            nt.links.new(nt.nodes["UVMap1"].outputs["Vector"], height_node.inputs["Vector"])
            nt.links.new(height_node.outputs["Color"], displace_node.inputs["Normal"])
            nt.links.new(displace_node.outputs["Displacement"], output_node.inputs["Displacement"])

        if mtd_bools["lightmap"]:
            lightmap_texture = flver_material.find_texture_type("g_Lightmap")
            if lightmap_texture is None:
                raise ValueError(
                    f"Material {flver_material.name} has MTD {flver_material.mtd_name} but no 'g_Lightmap' texture."
                )
            lightmap_node = nt.nodes.new("ShaderNodeTexImage")
            lightmap_node.location = (-550, 0)
            lightmap_node.name = f"{lightmap_texture.texture_type} | {lightmap_texture.path}"
            lightmap_node.image = self.get_dds_image(lightmap_texture.path)

            light_uv_attr = nt.nodes.new("ShaderNodeAttribute")
            light_uv_name = "UVMap3" if mtd_bools["multiple"] else "UVMap2"
            light_uv_attr.name = light_uv_attr.attribute_name = light_uv_name
            light_uv_attr.location = (-750, 0)
            nt.links.new(light_uv_attr.outputs["Vector"], lightmap_node.inputs["Vector"])

            if diffuse_node_1:
                light_overlay_node = nt.nodes.new("ShaderNodeMixRGB")
                light_overlay_node.blend_type = "OVERLAY"
                light_overlay_node.location = (-200, 1200)
                nt.links.new(diffuse_node_1.outputs["Color"], light_overlay_node.inputs[1])
                nt.links.new(lightmap_node.outputs["Color"], light_overlay_node.inputs[2])
                nt.links.new(light_overlay_node.outputs["Color"], bsdf_1.inputs["Base Color"])
            if diffuse_node_2:
                light_overlay_node = nt.nodes.new("ShaderNodeMixRGB")
                light_overlay_node.blend_type = "OVERLAY"
                light_overlay_node.location = (-200, 600)
                nt.links.new(diffuse_node_2.outputs["Color"], light_overlay_node.inputs[1])
                nt.links.new(lightmap_node.outputs["Color"], light_overlay_node.inputs[2])
                nt.links.new(light_overlay_node.outputs["Color"], bsdf_2.inputs["Base Color"])

        # TODO: Confirm "g_DetailBumpmap" has no content.

        return bl_material

    def get_dds_image(self, texture_path: str):
        if self.dds_images and texture_path in self.dds_images:
            return self.dds_images[texture_path]
        self.warning(f"Could not find DDS image: {texture_path}")
        return None

    def create_bsdf_node(self, flver_material, mtd_bools, node_tree, is_second_slot: bool):
        bsdf = node_tree.nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location[1] = 0 if is_second_slot else 1000
        bsdf.inputs["Roughness"].default_value = ROUGHNESS

        textures = flver_material.get_texture_dict()
        slot = "_2" if is_second_slot else ""
        slot_y_offset = 0 if is_second_slot else 1000

        uv_attr = node_tree.nodes.new("ShaderNodeAttribute")
        uv_attr.name = uv_attr.attribute_name = "UVMap2" if is_second_slot else "UVMap1"
        uv_attr.location = (-750, 0 + slot_y_offset)

        if mtd_bools["diffuse"]:
            texture = textures["g_Diffuse" + slot]
            diffuse_node = node_tree.nodes.new("ShaderNodeTexImage")
            diffuse_node.location = (-550, 330 + slot_y_offset)
            diffuse_node.image = self.get_dds_image(texture.path)
            diffuse_node.name = f"g_Diffuse{slot}"
            node_tree.links.new(uv_attr.outputs["Vector"], diffuse_node.inputs["Vector"])
            if not mtd_bools["lightmap"]:  # otherwise, MixRGB node will mediate
                node_tree.links.new(diffuse_node.outputs["Color"], bsdf.inputs["Base Color"])
            node_tree.links.new(diffuse_node.outputs["Alpha"], bsdf.inputs["Alpha"])
        else:
            diffuse_node = None

        if mtd_bools["specular"]:
            texture = textures["g_Specular" + slot]
            node = node_tree.nodes.new("ShaderNodeTexImage")
            node.location = (-550, 0 + slot_y_offset)
            node.image = self.get_dds_image(texture.path)
            node.name = f"g_Specular{slot}"
            node_tree.links.new(uv_attr.outputs["Vector"], node.inputs["Vector"])
            node_tree.links.new(node.outputs["Color"], bsdf.inputs["Specular"])
        else:
            bsdf.inputs["Specular"].default_value = 0.0  # no default specularity

        if mtd_bools["bumpmap"]:
            texture = textures["g_Bumpmap" + slot]
            node = node_tree.nodes.new("ShaderNodeTexImage")
            node.location = (-550, -330 + slot_y_offset)
            node.image = self.get_dds_image(texture.path)
            node.name = f"g_Bumpmap{slot}"
            normal_map_node = node_tree.nodes.new("ShaderNodeNormalMap")
            normal_map_node.name = "NormalMap2" if is_second_slot else "NormalMap"
            normal_map_node.space = "TANGENT"
            normal_map_node.uv_map = "UVMap2" if is_second_slot else "UVMap1"
            normal_map_node.inputs["Strength"].default_value = NORMAL_MAP_STRENGTH
            normal_map_node.location = (-200, -400 + slot_y_offset)

            node_tree.links.new(uv_attr.outputs["Vector"], node.inputs["Vector"])
            node_tree.links.new(node.outputs["Color"], normal_map_node.inputs["Color"])
            node_tree.links.new(normal_map_node.outputs["Normal"], bsdf.inputs["Normal"])

        # NOTE: [M] multi-texture still only uses one `g_Height` map if present.

        return bsdf, diffuse_node

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
                uv_layers[uv_index].data[j].uv[:] = [uv[0], 1 - uv[1]]  # Z axis discarded, Y axis inverted
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
        bone_vertex_group_indices = {}  # type: dict[(int, float), list[int]]

        # TODO: I *believe* that vertex bone indices are global if and only if `mesh.bone_indices` is empty. (In DSR,
        #  it's never empty.)
        if flver_mesh.bone_indices:
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
        # of `bone_index` and `weight`, so the dictionary keys constructed above are a tuple of those two to minimize
        # the number of `add()` calls needed below.
        for (bone_index, bone_weight), bone_vertices in bone_vertex_group_indices.items():
            bone_vertex_groups[bone_index].add(bone_vertices, bone_weight, "ADD")

        bpy.ops.object.modifier_add(type="ARMATURE")
        armature_mod = bl_mesh_obj.modifiers["Armature"]
        armature_mod.object = self.armature
        armature_mod.show_in_editmode = True
        armature_mod.show_on_cage = True

        # Custom properties with mesh data.
        bl_mesh_obj["is_bind_pose"] = flver_mesh.is_bind_pose
        # We only store this setting for the first `FaceSet`.
        bl_mesh_obj["cull_back_faces"] = flver_mesh.face_sets[0].cull_back_faces
        # NOTE: This index is sometimes invalid for vanilla map FLVERs (e.g., 1 when there is only one bone).
        bl_mesh_obj["default_bone_index"] = flver_mesh.default_bone_index

        return bl_mesh_obj

    def create_bones(self):
        """Create FLVER bones in Blender.

        Bones can be a little confusing in Blender. See:
            https://docs.blender.org/api/blender_python_api_2_71_release/info_gotcha.html#editbones-posebones-bone-bones

        The short story is that the "resting state" of each bone, including its head and tail position, is created in
        EDIT mode (as `EditBone` instances). This data defines the "zero deformation" state of the mesh with regard to
        bone weights, and will typically not be edited again when posing/animating a mesh that is rigged to this
        Armature. Instead, the bones are accessed as `PoseBone` instances in POSE mode, where they are treated like
        objects with transform data.

        If a FLVER bone has a parent bone, its FLVER transform is given relative to its parent's frame of reference.
        Determining the final position of any given bone in world space therefore requires all of its parents'
        transforms to be accumulated up to the root.

        Note that while bones are typically used for obvious animation cases in characters, objects, and parts (e.g.
        armor/weapons), they are also occasionally used in a fairly basic way by map pieces to position certain vertices
        in certain meshes. When this happens, so far, the bones have always been root bones, and basically function as
        anchors for certain vertices. I strongly suspect, but have not absolutely confirmed, that the `is_bind_pose`
        attribute of each mesh indicates whether FLVER bone data should be written to the EditBone (`is_bind_pose=True`)
        or PoseBone (`is_bind_pose=False`). Of course, we have to decide for each BONE, not each mesh, so currently I am
        enforcing that `is_bind_post=False` for ALL meshes in order to write the bone transforms to PoseBone rather than
        EditBone. A warning will be logged if only some of them are False.

        The AABB of each bone is presumably generated to include all vertices that use that bone as a weight.
        """
        bl_armature = bpy.data.armatures.new(f"{self.name} Armature")
        bl_armature_obj = self.create_obj(f"FLVER {self.name}", bl_armature, parent_to_armature=False)

        write_bone_type = ""
        warn_partial_bind_pose = False
        for mesh in self.flver.meshes:
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
        if warn_partial_bind_pose:
            self.warning(
                f"Some meshes in FLVER {self.name} use `is_bind_pose` (bone data written to EditBones) and some do not "
                f"(bone data written to PoseBones). Writing all bone data to EditBones."
            )

        self.context.view_layer.objects.active = bl_armature_obj
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="EDIT", toggle=False)

        edit_bones = []  # all bones
        for i, fl_bone in enumerate(self.flver.bones):
            edit_bone = bl_armature_obj.data.edit_bones.new(self.bl_bone_names[i])
            edit_bone["unk_x3c"] = fl_bone.unk_x3c
            edit_bone: bpy_types.EditBone
            if fl_bone.child_index != -1:
                # TODO: Check if this is set IFF bone has exactly one child, which can be auto-detected.
                edit_bone["child_name"] = self.bl_bone_names[fl_bone.child_index]
            if fl_bone.next_sibling_index != -1:
                edit_bone["next_sibling_name"] = self.bl_bone_names[fl_bone.next_sibling_index]
            if fl_bone.previous_sibling_index != -1:
                edit_bone["previous_sibling_name"] = self.bl_bone_names[fl_bone.previous_sibling_index]
            edit_bones.append(edit_bone)

        # NOTE: Bones that have no vertices weighted to them are left as 'unused' root bones in the FLVER skeleton.
        # They may be animated by HKX animations (and will affect their children appropriately) but will not actually
        # affect any vertices in the mesh.

        for fl_bone, edit_bone in zip(self.flver.bones, edit_bones):

            if write_bone_type == "POSE":
                # All edit bones are just Y-direction stubs of length 1 ("forward").
                # This rotation makes map pieces 'pose' bone data transform as expected.
                edit_bone.head = Vector((0, 0, 0))
                edit_bone.tail = Vector((0, 1, 0))
                continue

            fl_bone_translate, fl_bone_rotate_mat = fl_bone.get_absolute_translate_rotate(self.flver.bones)
            fl_bone_rotate = fl_bone_rotate_mat.to_euler_angles(radians=True)

            # Check if scale is ALMOST one and correct it.
            # TODO: Maybe too aggressive?
            if is_uniform(fl_bone.scale, rel_tol=0.001) and math.isclose(fl_bone.scale.x, 1.0, rel_tol=0.001):
                fl_bone.scale = Vector3.ones()

            if not is_uniform(fl_bone.scale, rel_tol=0.001):
                self.warning(f"Bone {fl_bone.name} has non-uniform scale: {fl_bone.scale}. Left as identity.")
                length = 0.1
            elif any(c < 0.0 for c in fl_bone.scale):
                self.warning(f"Bone {fl_bone.name} has negative scale: {fl_bone.scale}. Left as identity.")
                length = 0.1
            else:
                length = 0.1 * fl_bone.scale.x

            bl_rotate_euler = Euler((fl_bone.rotate.x, fl_bone_rotate.z, -fl_bone_rotate.y))
            tail, roll = bl_rotate_euler.to_quaternion().to_axis_angle()
            edit_bone.tail = length * tail.normalized()
            edit_bone.roll = roll
            bl_bone_translate = FL_TO_BL_SPACE_POS @ Vector(fl_bone_translate)
            # Exact bone absolute position is always at `head`.
            edit_bone.head = bl_bone_translate
            edit_bone.tail += bl_bone_translate

            if fl_bone.parent_index != -1:
                parent_edit_bone = edit_bones[fl_bone.parent_index]
                edit_bone.parent = parent_edit_bone
                # edit_bone.use_connect = True

        del edit_bones  # clear references to edit bones as we exit EDIT mode

        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        if write_bone_type == "POSE":
            for fl_bone, pose_bone in zip(self.flver.bones, bl_armature_obj.pose.bones):
                fl_bone_translate, fl_bone_rotate = fl_bone.get_absolute_translate_rotate(self.flver.bones)
                pose_bone.location = FL_TO_BL_SPACE_POS @ Vector(fl_bone_translate)
                pose_bone.rotation_mode = "XYZ"  # not Quaternion
                bl_bone_rotate = FL_TO_BL_SPACE_ROT @ Vector(fl_bone_rotate.to_euler_angles(radians=True))
                pose_bone.rotation_euler = bl_bone_rotate
                pose_bone.scale = Vector((fl_bone.scale.x, fl_bone.scale.z, fl_bone.scale.y))

        return bl_armature_obj

    def create_dummies(self):
        """Create empty objects that represent dummies. All dummies are parented to a root empty object."""

        bl_dummy_parent = self.create_obj(f"{self.name} Dummies")

        for i, dummy in enumerate(self.flver.dummies):
            bl_dummy = self.create_obj(f"Dummy<{i}> [{dummy.reference_id}]", parent_to_armature=False)
            bl_dummy.parent = bl_dummy_parent
            bl_dummy.empty_display_type = "ARROWS"  # best display type/size I've found (single arrow not sufficient)
            bl_dummy.empty_display_size = 0.05

            bl_dummy.location = (-dummy.position.x, -dummy.position.z, dummy.position.y)
            if dummy.use_upward_vector:
                bl_dummy.rotation_euler = fl_forward_up_vectors_to_bl_euler(dummy.forward, dummy.upward)
            else:  # TODO: I assume this is right (up-ignoring dummies only rotate around vertical axis)
                bl_dummy.rotation_euler = fl_forward_up_vectors_to_bl_euler(dummy.forward, Vector3(0, 0, 1))

            # TODO: Parent bone index is used to "place" the dummy. These are usually dedicated bones at the origin,
            #  e.g. 'Model_Dmy', and so won't matter for placement in most cases. I assume they can be used to offset
            #  the dummy while still having its movement attached to the attach bone. In Blender, we just create two
            #  contraints and leave it to the user to understand the difference in animations.

            # TODO: Moving the model is glitched with the double child constraint. Just place the Dummy according to its
            #  parent bone (in world space) and record its name on the Dummy.

            # Dummy position coordinates are given in the space of this parent bone.
            if dummy.parent_bone_index != -1:
                parent_constraint = bl_dummy.constraints.new(type="CHILD_OF")
                parent_constraint.name = "Dummy Parent Bone"
                parent_constraint.target = self.armature
                parent_constraint.subtarget = self.bl_bone_names[dummy.parent_bone_index]

            # Dummy moves with this bone during animations.
            if dummy.attach_bone_index != -1:
                attach_constraint = bl_dummy.constraints.new(type="CHILD_OF")
                attach_constraint.name = "Dummy Attach Bone"
                attach_constraint.target = self.armature
                attach_constraint.subtarget = self.bl_bone_names[dummy.attach_bone_index]

            # NOTE: This property is the canonical dummy ID. You are free to rename the dummy without affecting it.
            bl_dummy["reference_id"] = dummy.reference_id  # int
            bl_dummy["color"] = dummy.color  # RGBA
            bl_dummy["flag_1"] = dummy.flag_1  # bool
            bl_dummy["use_upward_vector"] = dummy.use_upward_vector  # bool
            # NOTE: These two properties are only non-zero in Sekiro (and probably Elden Ring).
            bl_dummy["unk_x30"] = dummy.unk_x30  # int
            bl_dummy["unk_x34"] = dummy.unk_x34  # int

    def create_obj(self, name: str, data=None, parent_to_armature=True):
        """Create a new Blender object. By default, will be parented to the FLVER's armature object."""
        obj = bpy.data.objects.new(name, data)
        self.context.scene.collection.objects.link(obj)
        self.all_bl_objs.append(obj)
        if parent_to_armature:
            obj.parent = self.armature
        return obj

    def warning(self, warning: str):
        print(f"# WARNING: {warning}")
        self.operator.report({"WARNING"}, warning)

    @property
    def armature(self):
        """Always the first object created."""
        return self.all_bl_objs[0]
