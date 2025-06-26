from __future__ import annotations

__all__ = [
    "BlenderMapCollision",
]

import typing as tp
from pathlib import Path

import bmesh
import bpy
import numpy as np
from soulstruct.blender.exceptions import MapCollisionExportError
from soulstruct.blender.types import *
from soulstruct.blender.utilities import *

from soulstruct.havok.enums import HavokModule
from soulstruct.havok.fromsoft.shared.map_collision import *

from .properties import MapCollisionProps
from .utilities import HKX_MATERIAL_NAME_RE


class BlenderMapCollision(BaseBlenderSoulstructObject[MapCollisionModel, MapCollisionProps]):

    TYPE = SoulstructType.COLLISION
    BL_OBJ_TYPE = ObjectType.MESH
    SOULSTRUCT_CLASS = MapCollisionModel

    obj: bpy.types.MeshObject
    data: bpy.types.Mesh

    __slots__ = []

    # No Map Collision model properties. Materials store their indices in their names.

    # HSV values for HKX materials, out of 360/100/100.
    HKX_MATERIAL_COLORS = {
        0: (0, 0, 100),  # default (white)
        1: (24, 75, 70),  # rock (orange)
        2: (130, 0, 10),  # stone (dark grey)
        3: (114, 58, 57),  # grass (green)
        4: (36, 86, 43),  # wood (dark brown)
        9: (179, 66, 64),  # metal (cyan)

        20: (214, 75, 64),  # under shallow water (light blue)
        21: (230, 85, 64),  # under deep water (dark blue)

        40: (50, 68, 80),  # trigger only (yellow)
    }

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MapCollisionModel,
        name: str,
        collection: bpy.types.Collection = None,
        *,
        lo_collision: MapCollisionModel | None = None,  # optional
    ) -> tp.Self:
        """Read a HKX or two (hi/lo) HKXs into a single Blender mesh, with materials representing res/submeshes."""
        hi_collision = soulstruct_obj

        # Maps `(is_hi, hkx_mat_index)` to Blender material index for both resolutions.
        hkx_to_bl_material_indices = {}  # type: dict[tuple[bool, int], int]
        # Blender materials, into which the above values index.
        bl_materials = []  # type: list[bpy.types.Material]

        def get_bl_mat_index(is_hi_res: bool, hkx_mat_index: int) -> int:
            key = (is_hi_res, hkx_mat_index)
            if key in hkx_to_bl_material_indices:
                return hkx_to_bl_material_indices[key]
            # New Blender material for this res and index.
            _i = hkx_to_bl_material_indices[key] = len(bl_materials)
            _bl_material = cls.get_hkx_material(hkx_mat_index, is_hi_res)
            bl_materials.append(_bl_material)
            return _i

        # Construct Blender materials corresponding to HKX res and material indices and collect indices.
        hi_bl_mat_indices = []  # matches length of `hi_submeshes`
        for mesh in hi_collision.meshes:
            bl_mat_index = get_bl_mat_index(True, mesh.material_index)
            hi_bl_mat_indices.append(bl_mat_index)

        vertices, faces, face_materials = cls.join_collision_meshes(hi_collision, hi_bl_mat_indices)

        if lo_collision:
            lo_bl_mat_indices = []  # matches length of `lo_submeshes`
            # Continue building `bl_materials` list and `hkx_to_bl_material_indices` dict from hi-res above.
            for mesh in lo_collision.meshes:
                bl_mat_index = get_bl_mat_index(False, mesh.material_index)
                lo_bl_mat_indices.append(bl_mat_index)

            lo_vertices, lo_faces, lo_face_materials = cls.join_collision_meshes(
                lo_collision, lo_bl_mat_indices, initial_offset=len(vertices)
            )
            vertices = np.vstack((vertices, lo_vertices))
            faces = np.vstack((faces, lo_faces))
            face_materials = np.concatenate([face_materials, lo_face_materials])

        # Swap vertex Y and Z coordinates.
        vertices = np.c_[vertices[:, 0], vertices[:, 2], vertices[:, 1]]

        bl_mesh = bpy.data.meshes.new(name=name)
        edges = []  # no edges in HKX
        bl_mesh.from_pydata(vertices, edges, faces)
        for material in bl_materials:
            bl_mesh.materials.append(material)
        bl_mesh.polygons.foreach_set("material_index", face_materials)

        bl_map_collision = cls.new(name, bl_mesh, collection)
        # No further properties to assign.
        return bl_map_collision

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
    ):
        raise TypeError("Cannot convert BlenderMapCollision to a single `MapCollisionModel`. Use `to_hkx_pair()`.")

    def to_hkx_pair(
        self,
        operator: LoggingOperator,
        havok_module: HavokModule,
        require_hi=True,
        use_hi_if_missing_lo=False,
        hi_name="",
        lo_name="",
    ) -> tuple[MapCollisionModel | None, MapCollisionModel | None]:
        """Create 'hi' and/or 'lo' HKX files by splitting given `hkx_model` into submeshes by material, or (if empty),
        directly from child submesh Mesh objects.

        `hi_name` and `lo_name` are required to set internally to the HKX file (though it probably doesn't impact
        gameplay). If passed explicitly as `None`, those submeshes will be ignored -- but they cannot BOTH be `None`.
        """
        if not self.obj.material_slots:
            raise ValueError(f"HKX model mesh '{self.name}' has no materials for submesh detection.")

        model_name = self.game_name
        if model_name.startswith("h") or hi_name:
            hi_name = hi_name or model_name
            lo_name = lo_name or model_name.replace("h", "l", 1)
        elif model_name.startswith("l") or lo_name:
            lo_name = lo_name or model_name
            hi_name = hi_name or model_name.replace("l", "h", 1)
        else:
            raise ValueError(f"Name of Map Collision model mesh '{self.name}' does not start with 'h' or 'l'.")

        # Automatically triangulate the mesh.
        self._clear_temp_hkx()
        bm = bmesh.new()
        bm.from_mesh(self.obj.data)
        bmesh.ops.triangulate(bm, faces=bm.faces, quad_method="BEAUTY", ngon_method="BEAUTY")
        tri_mesh_data = bpy.data.meshes.new("__TEMP_HKX__")
        # No need to copy materials over (no UV, etc.)
        bm.to_mesh(tri_mesh_data)
        bm.free()
        del bm

        hi_hkx_meshes = []  # type: list[MapCollisionModelMesh]
        lo_hkx_meshes = []  # type: list[MapCollisionModelMesh]

        # Note that it is possible that the user may have faces with different materials share vertices; this is fine,
        # and that vertex will be copied into each HKX submesh with a face loop that uses it.

        # Rather than iterating over all faces once for every material, we iterate over all of them once to split them
        # up by material index, then iterate once over each of those sublists (so the full face list is iterated twice).
        faces_by_material = {i: [] for i in range(len(self.obj.material_slots))}
        for face in tri_mesh_data.polygons:
            try:
                faces_by_material[face.material_index].append(face)
            except KeyError:
                raise MapCollisionExportError(
                    f"Face {face.index} of mesh '{self.name}' has material index {face.material_index}, "
                    f"which is not in the material slots of the mesh."
                )

        # Now iterate over each sublist of faces and create lists of HKX vertices and faces for each one. We maintain
        # a vertex map that maps the original full-mesh Blender vertex index to the submesh index.
        for bl_material_index, faces in faces_by_material.items():
            if not faces:
                continue  # no faces use this material

            # Extract HKX material index from name of Blender material.
            # We can use the original non-triangulated mesh's material slots.
            bl_material = self.obj.material_slots[bl_material_index].material
            mat_match = HKX_MATERIAL_NAME_RE.match(bl_material.name)
            if not mat_match:
                raise MapCollisionExportError(
                    f"Material '{bl_material.name}' of mesh '{self.name}' does not match expected HKX material "
                    f"name pattern: 'HKX # (Hi|Lo)'."
                )
            hkx_material_index = int(mat_match.group("index"))
            res = mat_match.group("res")[0].lower()  # 'h' or 'l'
            if (res == "h" and not hi_name) or (res == "l" and not lo_name):
                continue  # ignoring resolution

            # We can't assume that all faces with the same material index - and the vertices they use - are contiguous
            # in `polygons`, so a simple global vertex index subtraction won't work. We need to maintain a vertex map.
            vertex_map = {}
            hkx_verts_list = []
            hkx_faces_list = []
            for face in faces:
                hkx_face = []
                for vert_index in face.vertices:
                    if vert_index not in vertex_map:
                        # First time this vertex has been used by this submesh.
                        hkx_vert_index = vertex_map[vert_index] = len(hkx_verts_list)
                        vert = tri_mesh_data.vertices[vert_index]
                        hkx_verts_list.append(
                            [vert.co.x, vert.co.z, vert.co.y, 0.0]  # may as well swap Y and Z coordinates here
                        )
                    else:
                        # Vertex has already been used by this submesh.
                        hkx_vert_index = vertex_map[vert_index]
                    hkx_face.append(hkx_vert_index)
                hkx_faces_list.append(hkx_face)

            meshes = hi_hkx_meshes if res == "h" else lo_hkx_meshes
            mesh = MapCollisionModelMesh(
                vertices=np.array(hkx_verts_list, dtype=np.float32),
                faces=np.array(hkx_faces_list, dtype=np.uint16),
                material_index=hkx_material_index,
            )
            meshes.append(mesh)

        if hi_hkx_meshes:
            hi_collision = self.SOULSTRUCT_CLASS(
                name=hi_name,
                meshes=hi_hkx_meshes,
                havok_module=havok_module,
            )
            hi_collision.path = Path(f"{hi_name}.hkx")
        else:
            if require_hi:
                raise MapCollisionExportError(f"No 'hi' HKX meshes found in mesh '{self.name}'.")
            operator.warning(f"No 'hi' HKX meshes found in mesh '{self.name}'. Continuing as `require_hi=False`.")
            hi_collision = None

        if lo_hkx_meshes:
            lo_collision = self.SOULSTRUCT_CLASS(
                name=lo_name,
                meshes=lo_hkx_meshes,
                havok_module=havok_module,
            )
            lo_collision.path = Path(f"{lo_name}.hkx")
        elif use_hi_if_missing_lo:
            # Duplicate hi-res meshes and materials for lo-res (but use lo-res name).
            lo_collision = self.SOULSTRUCT_CLASS(
                name=lo_name,
                meshes=hi_hkx_meshes,
                havok_module=havok_module,
            )
            lo_collision.path = Path(f"{lo_name}.hkx")
        else:
            operator.warning(
                f"No 'lo' HKX meshes found for '{lo_name}' and `use_hi_if_missing_lo=False`. No lo-res exported."
            )
            lo_collision = None

        if not hi_collision and not lo_collision:
            raise MapCollisionExportError(
                f"No material-based HKX submeshes could be created for HKX mesh '{self.name}'. Are all faces "
                f"assigned to a material with name template 'HKX # (Hi|Lo)'?"
            )

        return hi_collision, lo_collision

    def duplicate(self, collections: tp.Sequence[bpy.types.Collection] = None) -> BlenderMapCollision:
        """Duplicate Collision model to a new object. Does not rename (will just add duplicate suffix)."""
        new_model = new_mesh_object(self.name, self.data.copy())
        new_model.soulstruct_type = SoulstructType.COLLISION
        # NOTE: There are currently no properties in the 'COLLISION' property group.
        # The only non-mesh data in a Collision model is represented by HKX materials.
        copy_obj_property_group(self.obj, new_model, "COLLISION")
        for collection in collections:
            collection.objects.link(new_model)
        return self.__class__(new_model)

    def rename(self, new_name: str):
        """Just renames object and data."""
        self.obj.name = new_name
        self.data.name = new_name

    @staticmethod
    def join_collision_meshes(
        collision: MapCollisionModel, bl_material_indices: tp.Sequence[int], initial_offset=0
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Concatenate all vertices and faces from a list of meshes by offsetting the face indices.

        TODO: Currently discards the fourth columns of vertices and faces. The latter may contain data.

        Also returns array of face material indices for use with `foreach_set()` by simply coping the corresponding
        `bl_material_indices` element to all faces.
        """
        if len(collision.meshes) != len(bl_material_indices):
            raise ValueError("Number of HKX meshes and Blender material indices must match.")
        vert_stack = []
        face_stack = []
        face_materials = []
        offset = initial_offset
        for mesh, bl_material_index in zip(collision.meshes, bl_material_indices, strict=True):
            face_stack.append(mesh.faces[:, :3] + offset)
            vert_stack.append(mesh.vertices[:, :3])
            face_materials.extend([bl_material_index] * mesh.face_count)
            offset += mesh.vertex_count
        vertices = np.vstack(vert_stack)
        faces = np.vstack(face_stack)
        return vertices, faces, np.array(face_materials)

    @classmethod
    def get_hkx_material(cls, hkx_material_index: int, is_hi_res: bool) -> bpy.types.Material:
        material_name = f"HKX {hkx_material_index} ({'Hi' if is_hi_res else 'Lo'})"
        try:
            material_offset, material_base = divmod(hkx_material_index, 100)
            hkx_material_enum = MapCollisionMaterial(material_base)
        except ValueError:
            pass
        else:
            # Add material enum name to material name. Will be ignored on export.
            if material_offset == 0:
                material_name = f"{material_name} <{hkx_material_enum.name}>"
            else:
                material_name = f"{material_name} <{hkx_material_enum.name} + {100 * material_offset}>"

        try:
            return bpy.data.materials[material_name]
        except KeyError:
            pass
        offset_100, mod_index = divmod(hkx_material_index, 100)
        h, s, v = cls.HKX_MATERIAL_COLORS.get(mod_index, (340, 74, 70))  # defaults to red
        if offset_100 > 0:  # rotate hue by 10 degrees for each 100 in material index
            h = (h + 10 * offset_100) % 360
        h /= 360.0
        s /= 100.0
        v /= 100.0
        if not is_hi_res:  # darken for lo-res
            v /= 2
        color = hsv_color(h, s, v)  # alpha = 1.0
        # NOTE: Not using wireframe in collision materials (unlike navmesh) as there is no per-face data.
        return create_basic_material(material_name, color, wireframe_pixel_width=0.0)

    @staticmethod
    def _clear_temp_hkx():
        """Delete temporary triangulated HKX mesh."""
        try:
            bpy.data.meshes.remove(bpy.data.meshes["__TEMP_HKX__"])
        except KeyError:
            pass
