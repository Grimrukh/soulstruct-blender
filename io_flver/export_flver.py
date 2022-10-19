from __future__ import annotations

__all__ = ["FLVERExporter"]

import re
import typing as tp
from multiprocessing import Pool, Queue

import bmesh
import bpy
import bpy_types
from mathutils import Euler, Matrix, Vector

from soulstruct.base.models.flver import FLVER, Version
from soulstruct.base.models.flver.vertex import VertexBuffer, BufferLayout, LayoutMember, MemberType, MemberFormat
from soulstruct.utilities.maths import Vector3

from .core import blender_vec_to_flver_vec, BlenderTransform, natural_keys, bl_euler_to_fl_forward_up_vectors

if tp.TYPE_CHECKING:
    from . import ExportFLVER

# TODO: Doesn't work yet, as I can't pickle Blender Objects at least.
#    - Would need to convert all the triangles/faces/loops/UVs etc. to Python data first.
USE_MULTIPROCESSING = False

MESH_RE = re.compile(r"(.*) Mesh (\d+) Obj")
NAME_RE = re.compile(r"FLVER (.*)")

DEBUG_MESH_INDEX = None
DEBUG_VERTEX_INDICES = []


TEXTURE_TYPES = (
    "g_Diffuse",
    "g_Specular",
    "g_Bumpmap",
    "g_Diffuse_2",
    "g_Specular_2",
    "g_Bumpmap_2",
    "g_Bumpmap_3",
    "g_Height",
    "g_Lightmap",
    "g_DetailBumpmap",
)


class MeshBuilder(tp.NamedTuple):
    """Holds data for a potentially multiprocessed mesh-building job."""
    bl_mesh: tp.Any
    fl_mesh: FLVER.Mesh
    layout: BufferLayout
    buffer: VertexBuffer
    uv_count: int
    face_set_count: int
    cull_back_faces: bool


class MeshBuildResult(tp.NamedTuple):
    """Sent back to main process in a Queue."""
    fl_vertices: list[FLVER.Mesh.Vertex]
    fl_face_sets: list[FLVER.Mesh.FaceSet]
    local_bone_indices: list[int]


class BlenderProp(tp.NamedTuple):
    bl_type: tp.Type
    default: tp.Any = None
    callback: tp.Callable = None
    do_not_assign: bool = False


class FLVERExporter:

    # TODO: DS1 values (map pieces, specifically).
    PROPERTIES = {
        "FLVER": {
            "endian": BlenderProp(bytes, b"L"),
            "version": BlenderProp(str, "DarkSouls_A", Version.__getitem__),
            "unicode": BlenderProp(int, True, bool),
            "unk_x4a": BlenderProp(int, False, bool),
            "unk_x4c": BlenderProp(int, 0),
            "unk_x5c": BlenderProp(int, 0),
            "unk_x5d": BlenderProp(int, 0),
            "unk_x68": BlenderProp(int, 0),
            "layout_member_unk_x00": BlenderProp(int, 0, do_not_assign=True),
        },
        "Bone": {
            "unk_x3c": BlenderProp(int, 0),
        },
        "Mesh": {
            "face_set_count": BlenderProp(int, 1, do_not_assign=True),
            "cull_back_faces": BlenderProp(int, False, bool, do_not_assign=True),
            "default_bone_index": BlenderProp(int, 0),
            "is_bind_pose": BlenderProp(int, False, bool),  # default suitable for Map Pieces
        },
        "Material": {
            "flags": BlenderProp(int),
            "mtd_path": BlenderProp(str),
            "texture_count": BlenderProp(int, do_not_assign=True),
            "gx_index": BlenderProp(int, -1),
            "unk_x18": BlenderProp(int, 0),
        },
        "Texture": {
            "texture_type": BlenderProp(str),
            "path": BlenderProp(str),
            "unk_x10": BlenderProp(int, 1),
            "unk_x11": BlenderProp(int, True, bool),
            "unk_x14": BlenderProp(float, 0.0),
            "unk_x18": BlenderProp(float, 0.0),
            "unk_x1C": BlenderProp(float, 0.0),
            "scale": BlenderProp(tuple, (1.0, 1.0)),
        },
        "LayoutMember": {
            "unk_x00": BlenderProp(int, 0),
        },
        "Dummy": {
            "color": BlenderProp(tuple, (255, 255, 255, 255), list),
            "reference_id": BlenderProp(int),
            "flag_1": BlenderProp(int, True, bool),
            "use_upward_vector": BlenderProp(int, True, bool),
            "unk_x30": BlenderProp(int, 0),
            "unk_x34": BlenderProp(int, 0),
        },
    }  # type: dict[str, dict[str, BlenderProp]]

    operator: bpy_types.Operator
    name: str
    layout_member_unk_x00: int

    def __init__(self, operator: ExportFLVER, context):
        self.operator = operator
        self.context = context

    def warning(self, msg: str):
        self.operator.report({"WARNING"}, msg)
        print(f"# WARNING: {msg}")

    def member(self, member_type: MemberType, member_format: MemberFormat, index=0):
        return LayoutMember(
            member_type=member_type,
            member_format=member_format,
            index=index,
            unk_x00=self.layout_member_unk_x00,
        )

    @classmethod
    def get(cls, bl_obj, prop_class: str, bl_prop_name: str, py_prop_name: str = None):
        if py_prop_name is None:
            py_prop_name = bl_prop_name
        try:
            prop = cls.PROPERTIES[prop_class][py_prop_name]
        except KeyError:
            raise KeyError(f"Invalid Blender FLVER property class/name: {prop_class}, {bl_prop_name}")

        prop_value = bl_obj.get(bl_prop_name, prop.default)

        if prop_value is None:
            raise KeyError(f"Object '{bl_obj.name}' does not have required `{prop_class}` property '{bl_prop_name}'.")
        if prop.bl_type is tuple:
            # Blender type is an `IDPropertyArray` with `typecode = 'i'` or `'d'`.
            if type(prop_value).__name__ != "IDPropertyArray":
                raise KeyError(
                    f"Object '{bl_obj.name}' property '{bl_prop_name}' does not have type `IDPropertyArray`."
                )
            if not prop.callback:
                prop_value = tuple(prop_value)  # convert `IDPropertyArray` to `tuple` by default
        elif not isinstance(prop_value, prop.bl_type):
            raise KeyError(f"Object '{bl_obj.name}' property '{bl_prop_name}' does not have type `{prop.bl_type}`.")

        if prop.callback:
            prop_value = prop.callback(prop_value)

        return prop_value

    @classmethod
    def get_all_props(cls, bl_obj, py_obj, prop_class: str, bl_prop_prefix: str = "") -> dict[str, tp.Any]:
        """Assign all class properties from Blender object `bl_obj` as attributes of Soulstruct object `py_obj`."""
        unassigned = {}
        for prop_name, prop in cls.PROPERTIES[prop_class].items():
            prop_value = cls.get(bl_obj, prop_class, bl_prop_prefix + prop_name, py_prop_name=prop_name)
            if prop.do_not_assign:
                unassigned[prop_name] = prop_value
            else:
                setattr(py_obj, prop_name, prop_value)
        return unassigned

    def detect_is_bind_pose(self, bl_meshes) -> str:
        read_bone_type = ""
        warn_partial_bind_pose = False
        for mesh in bl_meshes:
            is_bind_pose = bool(mesh.get("is_bind_pose", False))
            if is_bind_pose:  # typically: characters, objects, parts
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
        if warn_partial_bind_pose:
            self.warning(
                f"Some meshes in FLVER {self.name} use `is_bind_pose` (bone data written to EditBones) and some do not "
                f"(bone data written to PoseBones). Writing all bone data to EditBones."
            )
        return read_bone_type

    def export_flver(self, bl_armature) -> tp.Optional[FLVER]:
        """Create an entire FLVER from a Blender object.

        Expected object structure:

            Armature
                Dummies (Empty)
                    ... (probably none for map pieces)
                Mesh 0 Obj (Mesh)
                Mesh 1 Obj (Mesh)
                Mesh 2 Obj (Mesh)
                ...

        TODO: Currently only prepared for DS1 map pieces.
        """
        self.name = bl_armature.name
        flver = FLVER()
        extra_flver_props = self.get_all_props(bl_armature, flver.header, "FLVER")
        self.layout_member_unk_x00 = extra_flver_props["layout_member_unk_x00"]

        bl_child_objs = [obj for obj in bpy.data.objects if obj.parent is bl_armature]
        bl_meshes = []
        bl_dummies = []

        # Scan children of Armature.
        for child in bl_child_objs:
            if child.type == "MESH":
                bl_meshes.append(child)
            elif child.type == "EMPTY":
                if bl_dummies:
                    self.warning(f"Second Empty child of FLVER '{child.name}' ignored. Dummies only taken from first.")
                else:
                    bl_dummies = [obj for obj in bpy.data.objects if obj.parent is child]
            else:
                self.warning(f"Non-Mesh, non-Empty Child object '{child.name}' of FLVER ignored.")

        if not bl_meshes:
            self.operator.report({"ERROR"}, f"No mesh children of {self.name} found to export.")
            return None

        # Sort dummies/meshes by 'human sorting' on name (should match order in Blender hierarchy view).
        bl_dummies.sort(key=lambda obj: natural_keys(obj.name))
        bl_meshes.sort(key=lambda obj: natural_keys(obj.name))

        read_bone_type = self.detect_is_bind_pose(bl_meshes)
        print(f"Exporting FLVER bones from data type: {read_bone_type}")
        flver.bones = self.create_bones(bl_armature, read_bone_type)
        bone_names = [bone.name for bone in flver.bones]  # for vertex weighting

        for bl_dummy in bl_dummies:
            if not bl_dummy.type == "EMPTY":
                self.warning(f"Ignoring non-Empty child object '{bl_dummy.name}' of empty Dummy parent.")
            fl_dummy = self.create_dummy(bl_dummy, bone_names)
            flver.dummies.append(fl_dummy)

        # Set up basic Mesh properties.
        mesh_builders = []
        for bl_mesh in bl_meshes:
            fl_mesh, fl_material, fl_layout, mesh_builder = self.create_mesh_material_layout(
                bl_mesh, flver.buffer_layouts, use_chr_layout=read_bone_type == "EDIT"
            )
            fl_mesh.material_index = len(flver.materials)
            flver.materials.append(fl_material)
            flver.meshes.append(fl_mesh)
            if fl_layout is not None:
                flver.buffer_layouts.append(fl_layout)
            mesh_builders.append(mesh_builder)

        # Process mesh vertices, faces, and bones.
        if USE_MULTIPROCESSING:
            queue = Queue()  # type: Queue[MeshBuildResult]

            worker_args = [
                (builder, bone_names, queue)
                for builder in mesh_builders
            ]

            with Pool() as pool:
                pool.starmap(build_fl_mesh_mp, worker_args)  # blocks here until all done

            builder_index = 0
            while not queue.empty():
                build_result = queue.get()
                fl_mesh = mesh_builders[builder_index].fl_mesh
                fl_mesh.vertices = build_result.fl_vertices
                fl_mesh.face_sets = build_result.fl_face_sets
                fl_mesh.bone_indices = build_result.local_bone_indices
                mesh_builders[builder_index].buffer.vertex_count = len(build_result.fl_vertices)
        else:
            for builder in mesh_builders:
                print(f"Building FLVER mesh: {builder.bl_mesh.name}")
                fl_vertices, fl_face_sets, mesh_local_bone_indices = build_fl_mesh(
                    builder, bone_names
                )
                print(f"    --> {len(fl_vertices)} vertices")
                if not fl_vertices or not fl_face_sets:
                    raise ValueError(
                        f"Cannot export a FLVER mesh with no vertices and/or faces: {builder.bl_mesh.name}"
                    )
                builder.fl_mesh.vertices = fl_vertices
                builder.fl_mesh.face_sets = fl_face_sets
                builder.fl_mesh.bone_indices = mesh_local_bone_indices
                builder.buffer.vertex_count = len(fl_vertices)

        # TODO: Set BB properly per bone (need to update bounds for each bone while building vertices).
        recompute_bounding_box(flver, flver.bones)

        return flver

    def create_bones(self, bl_armature_obj, read_bone_type: str) -> list[FLVER.Bone]:
        self.context.view_layer.objects.active = bl_armature_obj

        # We need `EditBone` mode to retrieve custom properties, even if reading transforms from pose later.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="EDIT", toggle=False)

        fl_bones = []
        bl_world_transforms = []  # type: list[BlenderTransform]  # collected and converted to local space later
        edit_bone_names = [edit_bone.name for edit_bone in bl_armature_obj.data.edit_bones]
        if len(set(edit_bone_names)) != len(edit_bone_names):
            raise ValueError(f"Bone names of '{self.name}' armature are not all unique.")
        for edit_bone in bl_armature_obj.data.edit_bones:
            fl_bone = FLVER.Bone(name=edit_bone.name)
            self.get_all_props(edit_bone, fl_bone, "Bone")
            if edit_bone.parent:
                parent_bone_name = edit_bone.parent.name
                fl_bone.parent_index = edit_bone_names.index(parent_bone_name)
            else:
                fl_bone.parent_index = -1
            child_name = edit_bone.get("child_name", None)
            if child_name is not None:
                # TODO: Check if this is set IFF bone has exactly one child, which can be auto-detected.
                try:
                    fl_bone.child_index = edit_bone_names.index(child_name)
                except IndexError:
                    raise ValueError(f"Cannot find child '{child_name}' of bone '{edit_bone.name}'.")
            next_sibling_name = edit_bone.get("next_sibling_name", None)
            if next_sibling_name is not None:
                try:
                    fl_bone.next_sibling_index = edit_bone_names.index(next_sibling_name)
                except IndexError:
                    raise ValueError(f"Cannot find next sibling '{next_sibling_name}' of bone '{edit_bone.name}'.")
            prev_sibling_name = edit_bone.get("previous_sibling_name", None)
            if prev_sibling_name is not None:
                try:
                    fl_bone.previous_sibling_index = edit_bone_names.index(prev_sibling_name)
                except IndexError:
                    raise ValueError(f"Cannot find previous sibling '{prev_sibling_name}' of bone '{edit_bone.name}'.")

            if read_bone_type == "EDIT":
                # Get absolute bone transform from EditBone (characters, etc.).
                world_translate = Vector(edit_bone.head)
                rotate_mat = Matrix.Rotation(edit_bone.roll, 3, edit_bone.tail - edit_bone.head)
                world_rotate = rotate_mat.to_euler()
                scale = 10 * edit_bone.length
                world_scale = Vector((scale, scale, scale))
                bl_world_transforms.append(
                    BlenderTransform(world_translate, world_rotate, world_scale),
                )

            fl_bones.append(fl_bone)

        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        if read_bone_type == "POSE":
            # Get absolute bone transform from PoseBone (map pieces).
            for fl_bone, pose_bone in zip(fl_bones, bl_armature_obj.pose.bones):
                world_translate = Vector(pose_bone.location)
                world_rotate = Euler(pose_bone.rotation_euler)
                world_scale = Vector(pose_bone.scale)
                bl_world_transforms.append(
                    BlenderTransform(world_translate, world_rotate, world_scale),
                )

        for fl_bone, bl_world_transform in zip(fl_bones, bl_world_transforms):
            # Convert Blender T/R/S to local space. Since ALL bones are currently in world space, we only need each
            # immediate parent to convert to local space (just translate/rotate relative to parent).
            if fl_bone.parent_index != -1:
                # Get inverse parent transform and compose.
                inv_parent = bl_world_transforms[fl_bone.parent_index].inverse()
                bl_local_transform = inv_parent.compose(bl_world_transform)
                fl_bone.translate = bl_local_transform.fl_translate
                fl_bone.rotate = bl_local_transform.fl_rotate_rad  # FLVER bone uses radians
                # TODO: Scale is not transformed to local. (Not transformed to world by importer.)
                fl_bone.scale = bl_world_transform.fl_scale
            else:
                # World space is local space for root bone.
                fl_bone.translate = bl_world_transform.fl_translate
                fl_bone.rotate = bl_world_transform.fl_rotate_rad  # FLVER bone uses radians
                fl_bone.scale = bl_world_transform.fl_scale

        return fl_bones

    def create_dummy(self, bl_dummy, bone_names: list[str]) -> FLVER.Dummy:
        fl_dummy = FLVER.Dummy()
        self.get_all_props(bl_dummy, fl_dummy, "Dummy")
        bl_transform = BlenderTransform.from_bl_obj(bl_dummy)
        fl_dummy.position = bl_transform.fl_translate
        forward, up = bl_euler_to_fl_forward_up_vectors(bl_transform.bl_rotate)
        fl_dummy.forward = forward
        fl_dummy.upward = up if fl_dummy.use_upward_vector else Vector3.zero()

        parent_bone_name = None
        attach_bone_name = None
        for constraint in bl_dummy.constraints:
            if constraint.name == "Dummy Parent Bone":
                parent_bone_name = constraint.subtarget
            elif constraint.name == "Dummy Attach Bone":
                attach_bone_name = constraint.subtarget
            else:
                self.warning(f"Ignoring unrecognized Dummy constraint: {constraint.name}")
        if parent_bone_name is None:
            fl_dummy.parent_bone_index = -1
        elif parent_bone_name not in bone_names:
            raise ValueError(
                f"Dummy Empty '{bl_dummy.name}' 'Dummy Parent Bone' constraint is targeting "
                f"an invalid bone name: {parent_bone_name}."
            )
        else:
            fl_dummy.parent_bone_index = bone_names.index(parent_bone_name)
        if attach_bone_name is None:
            fl_dummy.attach_bone_index = -1
        elif attach_bone_name not in bone_names:
            raise ValueError(
                f"Dummy Empty '{bl_dummy.name}' 'Dummy Attach Bone' constraint is targeting "
                f"an invalid bone name: {parent_bone_name}."
            )
        else:
            fl_dummy.attach_bone_index = bone_names.index(attach_bone_name)
        return fl_dummy

    def create_mesh_material_layout(
        self, bl_mesh, buffer_layouts: list[BufferLayout], use_chr_layout: bool
    ) -> (FLVER.Mesh, FLVER.Material, tp.Optional[BufferLayout], MeshBuilder):
        fl_mesh = FLVER.Mesh()
        extra_mesh_props = self.get_all_props(bl_mesh, fl_mesh, "Mesh")

        # Process material.
        if len(bl_mesh.material_slots) != 1:
            raise ValueError(f"Mesh {bl_mesh.name} must have exactly one material.")
        bl_material = bl_mesh.material_slots[0].material
        fl_material = FLVER.Material()
        fl_material.name = bl_material.name
        extra_mat_props = self.get_all_props(bl_material, fl_material, "Material", bl_prop_prefix="material_")
        found_texture_types = set()
        for i in range(extra_mat_props["texture_count"]):
            fl_texture = FLVER.Material.Texture()
            self.get_all_props(bl_material, fl_texture, "Texture", bl_prop_prefix=f"texture[{i}]_")
            tex_type = fl_texture.texture_type
            if tex_type not in TEXTURE_TYPES:
                self.warning(f"Unrecognized FLVER Texture type: {tex_type}")
            if tex_type in found_texture_types:
                self.warning(f"Ignoring duplicate of texture type '{tex_type}' in Material {fl_material.name}.")
            else:
                found_texture_types.add(tex_type)
                fl_material.textures.append(fl_texture)

        # NOTE: Extra textures not required by this shader (e.g., 'g_DetailBumpmap' for most of them) are still
        # written, but missing required textures will raise an error here.
        mtd_name = fl_material.mtd_name
        mtd_bools = fl_material.get_mtd_bools()
        self.validate_found_textures(mtd_bools, found_texture_types, mtd_name)

        # TODO: Choose default layout factory with an export enum.
        if use_chr_layout:
            fl_layout = self.get_ds1_chr_buffer_layout(
                is_multiple=mtd_bools["multiple"],
            )
        else:
            fl_layout = self.get_ds1_map_buffer_layout(
                is_multiple=mtd_bools["multiple"],
                is_lightmap=mtd_bools["lightmap"],
            )
        uv_count = 1 + mtd_bools["multiple"] + mtd_bools["lightmap"]

        vertex_buffer = VertexBuffer()
        fl_mesh.vertex_buffers = [vertex_buffer]
        return_layout = True
        if fl_layout in buffer_layouts:
            # Already defined.
            vertex_buffer.layout_index = buffer_layouts.index(fl_layout)
            return_layout = False
        else:
            vertex_buffer.layout_index = len(buffer_layouts)
            # Returned `buffer_layout` will be added to FLVER.

        mesh_builder = MeshBuilder(
            bl_mesh,
            fl_mesh,
            fl_layout,
            vertex_buffer,
            uv_count,
            extra_mesh_props.get("face_set_count", 1),
            extra_mesh_props.get("cull_back_faces", False),
        )

        return fl_mesh, fl_material, (fl_layout if return_layout else None), mesh_builder

    @staticmethod
    def validate_found_textures(mtd_bools: dict[str, bool], found_texture_types: set[str], mtd_name: str):
        for tex_type in ("Diffuse", "Specular", "Bumpmap"):
            if mtd_bools[tex_type.lower()]:
                if f"g_{tex_type}" not in found_texture_types:
                    raise ValueError(f"Texture type 'g_{tex_type}' required for material with MTD '{mtd_name}'.")
                if mtd_bools["multiple"] and f"g_{tex_type}_2" not in found_texture_types:
                    raise ValueError(f"Texture type 'g_{tex_type}_2' required for material with MTD '{mtd_name}'.")
        for tex_type in ("Lightmap", "Height"):
            if mtd_bools[tex_type.lower()] and f"g_{tex_type}" not in found_texture_types:
                raise ValueError(f"Texture type 'g_{tex_type}' required for material with MTD '{mtd_name}'.")

    def get_ds1_map_buffer_layout(self, is_multiple=False, is_lightmap=False) -> BufferLayout:
        members = [
            self.member(MemberType.Position, MemberFormat.Float3),
            self.member(MemberType.BoneIndices, MemberFormat.Byte4B),
            self.member(MemberType.Normal, MemberFormat.Byte4C),
            self.member(MemberType.Tangent, MemberFormat.Byte4C),
            self.member(MemberType.VertexColor, MemberFormat.Byte4C),
        ]
        if is_multiple:  # has Bitangent
            members.insert(4, self.member(MemberType.Bitangent, MemberFormat.Byte4C))
        if is_multiple and is_lightmap:  # three UVs
            members.append(self.member(MemberType.UV, MemberFormat.UVPair))
            members.append(self.member(MemberType.UV, MemberFormat.UV, index=1))
        elif is_multiple or is_lightmap:  # two UVs
            members.append(self.member(MemberType.UV, MemberFormat.UVPair))
        else:  # one UV
            members.append(self.member(MemberType.UV, MemberFormat.UV))

        return BufferLayout(members)

    def get_ds1_chr_buffer_layout(self, is_multiple=False) -> BufferLayout:
        members = [
            self.member(MemberType.Position, MemberFormat.Float3),
            self.member(MemberType.BoneIndices, MemberFormat.Byte4B),
            self.member(MemberType.BoneWeights, MemberFormat.Short4ToFloat4A),
            self.member(MemberType.Normal, MemberFormat.Byte4C),
            self.member(MemberType.Tangent, MemberFormat.Byte4C),
            self.member(MemberType.VertexColor, MemberFormat.Byte4C),
        ]
        if is_multiple:  # has Bitangent and UVPair
            members.insert(5, self.member(MemberType.Bitangent, MemberFormat.Byte4C))
            members.append(self.member(MemberType.UV, MemberFormat.UVPair))
        else:  # one UV
            members.append(self.member(MemberType.UV, MemberFormat.UV))

        return BufferLayout(members)


def build_fl_mesh_mp(builder: MeshBuilder, bone_names: list[str], queue: Queue):
    fl_vertices, fl_face_sets, local_bone_indices = build_fl_mesh(builder, bone_names)
    build_result = MeshBuildResult(fl_vertices, fl_face_sets, local_bone_indices)
    queue.put(build_result)


def build_fl_mesh(
    mesh_builder: MeshBuilder, bone_names: list[str],
) -> (list[FLVER.Mesh.Vertex], list[FLVER.Mesh.FaceSet], list[int]):
    """Process Blender vertices, faces, and bone-weighted vertex groups into FLVER equivalents."""

    bl_mesh = mesh_builder.bl_mesh.data
    mesh_vertex_groups = mesh_builder.bl_mesh.vertex_groups
    layout = mesh_builder.layout

    bl_mesh.calc_normals_split()  # TODO: I think `calc_tangents` calls this automatically.
    try:
        bl_mesh.calc_tangents(uvmap="UVMap1")
    except RuntimeError:
        # TODO: should I ever use UVMap2?
        # try:
        #     bl_mesh.calc_tangents(uvmap="UVMap2")
        # except RuntimeError:
        raise RuntimeError("Could not find UVMap1 or UVMap2. If this mesh is empty, delete it.")

    # Temporary BMesh is triangulated, but is never saved back to Blender.
    bm = bmesh.new()
    bm.from_mesh(bl_mesh)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    # Dictionary that maps created FLVER vertex indices to `(position, uvs, colors)` triples that mark them as unique.
    flver_v_indices = {}

    fl_face_sets = [
        FLVER.Mesh.FaceSet(
            flags=i,
            unk_x06=0,  # TODO: define default in dict
            triangle_strip=False,
            cull_back_faces=mesh_builder.cull_back_faces,
            vertex_indices=[],
        )
        for i in range(mesh_builder.face_set_count)
    ]

    # NOTE: Vertices that do not appear in any Blender faces will NOT be exported.
    triangles = bm.calc_loop_triangles()

    fl_vertices = []
    mesh_local_bone_indices = []

    # noinspection PyTypeChecker
    for f_i, face in enumerate(triangles):
        flver_face = []
        for loop in face:
            v_i = loop.vert.index
            mesh_loop = bl_mesh.loops[loop.index]

            if layout.has_member_type(MemberType.Position):
                position = blender_vec_to_flver_vec(bm.verts[v_i].co)
            else:
                position = None

            if layout.has_member_type(MemberType.BoneIndices):

                has_weights = layout.has_member_type(MemberType.BoneWeights)

                bl_v = bl_mesh.vertices[v_i]
                global_bone_indices = []
                bone_weights = []
                for vertex_group in bl_v.groups:  # only one for map pieces; max of 4 for other FLVER types
                    # Find mesh vertex group with this index.
                    for mesh_group in mesh_vertex_groups:
                        if vertex_group.group == mesh_group.index:
                            try:
                                bone_index = bone_names.index(mesh_group.name)
                            except ValueError:
                                raise ValueError(f"Vertex is weighted to invalid bone name: '{mesh_group.name}'.")
                            global_bone_indices.append(bone_index)
                            if has_weights:  # don't waste time calling `weight()` for non-weight layouts (map pieces)
                                bone_weights.append(mesh_group.weight(v_i))
                            break
                if len(global_bone_indices) > 4:
                    raise ValueError(f"Vertex cannot be weighted to >4 bones ({len(global_bone_indices)} is too many).")

                bone_indices = []  # local
                for global_bone_index in global_bone_indices:
                    try:
                        bone_indices.append(mesh_local_bone_indices.index(global_bone_index))
                    except ValueError:
                        bone_indices.append(len(mesh_local_bone_indices))
                        mesh_local_bone_indices.append(global_bone_index)

                while len(bone_weights) < 4:
                    bone_weights.append(0.0)

                if has_weights:
                    while len(bone_indices) < 4:
                        bone_indices.append(0)  # zero-weight indices are zero
                elif len(bone_indices) == 1:
                    bone_indices *= 4  # duplicate single-element list to four-element list
            else:
                bone_indices = [0] * 4
                bone_weights = [0.0] * 4

            if layout.has_member_type(MemberType.Normal):
                # TODO: 127 is the only value seen in DS1 models thus far for `normal[3]`. Will need to store as a
                #  custom vertex property for other games that use it.
                normal = [*blender_vec_to_flver_vec(mesh_loop.normal), 127.0]
            else:
                normal = None

            # Get UVs from loop. We always need to do this because even if the vertex has already been filled, we need
            # to check if this loop has different UVs and create a duplicate vertex if so.
            if layout.has_member_type(MemberType.UV):
                uvs = []
                for uv_index in range(1, mesh_builder.uv_count + 1):
                    try:
                        uv_layer = bl_mesh.uv_layers[f"UVMap{uv_index}"]
                    except KeyError:
                        raise KeyError(
                            f"Expected {mesh_builder.uv_count} UVs for mesh, but could not find 'UVMap{uv_index}'."
                        )
                    bl_uv = uv_layer.data[loop.index].uv
                    uvs.append((bl_uv[0], -bl_uv[1], 0.0))  # FLVER UV always has Z coordinate (usually 0)
            else:
                uvs = None

            if layout.has_member_type(MemberType.Tangent):
                tangents = [[*blender_vec_to_flver_vec(mesh_loop.tangent), -1.0]]
            else:
                tangents = None

            if layout.has_member_type(MemberType.Bitangent):
                bitangent = [*blender_vec_to_flver_vec(mesh_loop.bitangent), -1.0]
            else:
                bitangent = None

            # Same with vertex colors. Though they are stored as a list, there should always only be one color layer.
            if layout.has_member_type(MemberType.VertexColor):
                colors = [tuple(bl_mesh.vertex_colors["VertexColors"].data[loop.index].color)]
            else:
                colors = None

            v_key = (tuple(position), tuple(uvs), tuple(colors))  # hashable

            try:
                fl_v_i = flver_v_indices[v_key]
            except KeyError:
                # Create new `Vertex`.
                fl_v_i = flver_v_indices[v_key] = len(flver_v_indices)
                fl_vertices.append(FLVER.Mesh.Vertex(
                    position=position,
                    bone_weights=bone_weights,
                    bone_indices=bone_indices,
                    normal=normal,
                    uvs=uvs,
                    tangents=tangents,
                    bitangent=bitangent,
                    colors=colors,
                ))
            flver_face.append(fl_v_i)

        fl_face_sets[0].vertex_indices += flver_face

    # All LOD face sets are duplicated from the first.
    # TODO: Setting up actual face sets (which share vertices) in Blender would be very annoying.
    for lod_face_set in fl_face_sets[1:]:
        lod_face_set.vertex_indices = fl_face_sets[0].vertex_indices.copy()

    return fl_vertices, fl_face_sets, mesh_local_bone_indices


def recompute_bounding_box(flver: FLVER, bones: list[FLVER.Bone]):
    """Update bounding box min/max for `flver.header` and all bones in `bones`."""
    x = [v.position[0] for mesh in flver.meshes for v in mesh.vertices]
    y = [v.position[1] for mesh in flver.meshes for v in mesh.vertices]
    z = [v.position[2] for mesh in flver.meshes for v in mesh.vertices]
    if x or y or z:
        bb_min = Vector3(min(x), min(y), min(z))
        bb_max = Vector3(max(x), max(y), max(z))
    else:
        # No vertex data in ANY mesh. Highly suspect, obviously.
        bb_min = Vector3.zero()
        bb_max = Vector3.zero()
    flver.header.bounding_box_min = bb_min
    flver.header.bounding_box_max = bb_max
    for bone in bones:
        bone.bounding_box_min = bb_min
        bone.bounding_box_max = bb_max
