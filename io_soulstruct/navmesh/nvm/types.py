from __future__ import annotations

__all__ = [
    "BlenderNVM",
    "BlenderNVMEventEntity",
]

import typing as tp

import numpy as np

import bmesh
import bpy
from mathutils import Vector

from soulstruct.base.maps.navmesh.nvm import *
from io_soulstruct.exceptions import NVMExportError
from io_soulstruct.types import *
from io_soulstruct.utilities import *
from .properties import *
from .utilities import set_face_material


class BlenderNVM(SoulstructObject[NVM, NVMProps]):

    TYPE = SoulstructType.NAVMESH
    OBJ_DATA_TYPE = SoulstructDataType.MESH
    SOULSTRUCT_CLASS = NVM

    __slots__ = []

    obj: bpy.types.MeshObject
    data: bpy.types.Mesh

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: NVM,
        name: str,
        collection: bpy.types.Collection = None,
    ) -> BlenderNVM:
        operator.to_object_mode()
        operator.deselect_all()

        nvm = soulstruct_obj

        # Create mesh.
        mesh = bpy.data.meshes.new(name=name)
        vertices = GAME_TO_BL_ARRAY(nvm.vertices)
        edges = []  # no edges in NVM
        faces = [triangle.vertex_indices for triangle in nvm.triangles]
        mesh.from_pydata(vertices, edges, faces)

        # Create `BMesh` (as we need to assign face flag data to a custom `int` layer).
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        flags_layer = bm.faces.layers.int.new("nvm_face_flags")
        obstacle_count_layer = bm.faces.layers.int.new("nvm_face_obstacle_count")
        for f_i, face in enumerate(bm.faces):
            nvm_triangle = nvm.triangles[f_i]
            face[flags_layer] = nvm_triangle.flags
            face[obstacle_count_layer] = nvm_triangle.obstacle_count

        bl_nvm = cls.new(name, data=mesh, collection=collection)  # type: BlenderNVM

        for nvm_event in nvm.event_entities:
            # Get the average position of the faces. This is purely for show and is not exported.
            avg_pos = Vector((0, 0, 0))
            for i in nvm_event.triangle_indices:
                avg_pos += bm.faces[i].calc_center_median()
            avg_pos /= len(nvm_event.triangle_indices)
            nvm_event_name = f"{name} Event {nvm_event.entity_id}"
            bl_event = BlenderNVMEventEntity.new_from_soulstruct_obj(
                operator, context, nvm_event, nvm_event_name, collection, location=avg_pos
            )
            bl_event.obj.parent = bl_nvm.obj

        bm.to_mesh(mesh)
        del bm

        return bl_nvm

    def get_nvm_event_entities(self) -> list[BlenderNVMEventEntity]:
        return [
            BlenderNVMEventEntity(obj) for obj in self.obj.children
            if obj.soulstruct_type == SoulstructType.NVM_EVENT_ENTITY
        ]

    def to_soulstruct_obj(self, operator: LoggingOperator, context: bpy.types.Context) -> NVM:
        """Create `NVM` from a Blender mesh object.

        This is much simpler than FLVER or HKX map collision mesh export. Note that the navmesh name is not needed, as
        it appears nowhere in the NVM binary file.

        We do not do any triangulation here; the NVM model should already be triangulated exactly as desired, as the
        triangles actually matter for navigation.
        """
        mesh_data = self.obj.data
        nvm_verts = np.array([vert.co for vert in mesh_data.vertices], dtype=np.float32)
        # Swap Y and Z coordinates.
        nvm_verts[:, [1, 2]] = nvm_verts[:, [2, 1]]

        nvm_faces = []  # type: list[tuple[int, int, int]]
        for face in mesh_data.polygons:
            if len(face.vertices) != 3:
                raise NVMExportError(
                    f"Found a non-triangle mesh face in NVM {self.name} (face {face.index}). You must triangulate it."
                )
            # noinspection PyTypeChecker
            vertices = tuple(face.vertices)  # type: tuple[int, int, int]
            nvm_faces.append(vertices)

        def find_connected_face_index(edge_v1: int, edge_v2: int, not_face) -> int:
            """Find face that shares an edge with the given edge.

            Returns -1 if no connected face is found (i.e. edge is on the edge of the mesh).
            """
            # TODO: Could surely iterate over faces just once for this?
            for i_, f_ in enumerate(nvm_faces):
                if f_ != not_face and edge_v1 in f_ and edge_v2 in f_:  # order doesn't matter
                    return i_
            return -1

        # Get connected faces along each edge of each face.
        nvm_connected_face_indices = []  # type: list[tuple[int, int, int]]
        for face in nvm_faces:
            connected_v1 = find_connected_face_index(face[0], face[1], face)
            connected_v2 = find_connected_face_index(face[1], face[2], face)
            connected_v3 = find_connected_face_index(face[2], face[0], face)
            nvm_connected_face_indices.append((connected_v1, connected_v2, connected_v3))
            if connected_v1 == -1 and connected_v2 == -1 and connected_v3 == -1:
                operator.warning(
                    f"NVM face {face} in '{self.name}' appears to have no connected faces, which is very suspicious!"
                )

        # Create `BMesh` to access custom face layers for `flags` and `obstacle_count`.
        bm = bmesh.new()
        bm.from_mesh(mesh_data)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        flags_layer = bm.faces.layers.int.get("nvm_face_flags")
        if not flags_layer:
            raise ValueError("NVM mesh does not have 'nvm_face_flags' custom face layer.")
        obstacle_count_layer = bm.faces.layers.int.get("nvm_face_obstacle_count")
        if not obstacle_count_layer:
            raise ValueError("NVM mesh does not have 'nvm_face_obstacle_count' custom face layer.")

        nvm_flags = []
        nvm_obstacle_counts = []
        for bm_face in bm.faces:
            nvm_flags.append(bm_face[flags_layer])
            nvm_obstacle_counts.append(bm_face[obstacle_count_layer])
        if len(nvm_flags) != len(nvm_faces):
            raise ValueError("NVM mesh has different number of `Mesh` faces and `BMesh` face flags.")

        nvm_triangles = [
            NVMTriangle(
                vertex_indices=nvm_faces[i],
                connected_indices=nvm_connected_face_indices[i],
                obstacle_count=nvm_obstacle_counts[i],
                flags=nvm_flags[i],
            )
            for i in range(len(nvm_faces))
        ]

        event_entities = [
            nvm_event_entity.to_soulstruct_obj(operator, context)
            for nvm_event_entity in self.get_nvm_event_entities()
        ]

        nvm = NVM(
            big_endian=False,
            vertices=nvm_verts,
            triangles=nvm_triangles,
            event_entities=event_entities,
            # quadtree boxes generated automatically on pack
        )

        return nvm

    def set_face_materials(self, nvm: NVM):
        mesh_data = self.obj.data
        for bl_tri, nvm_triangle in zip(mesh_data.polygons, nvm.triangles):
            set_face_material(mesh_data, bl_tri, nvm_triangle.flags)

    def create_nvm_quadtree(
        self, context: bpy.types.Context, nvm: NVM, model_name: str, collection: bpy.types.Collection = None
    ) -> list[bpy.types.Object]:
        """Create box tree (depth first creation order).

        NOTE: These boxes should be imported for inspection only. They are automatically generated from the mesh
        min/max vertex coordinates on NVM export and have no properties.
        """
        collection = collection or context.scene.collection
        boxes = []
        for box, indices in nvm.get_all_boxes(nvm.root_box):
            if not indices:
                box_name = f"{model_name} Box ROOT"
            else:
                indices_string = "-".join(str(i) for i in indices)
                box_name = f"{model_name} Box {indices_string}"
            bl_box = self.create_box(context, box)
            collection.objects.link(bl_box)
            bl_box.name = box_name
            boxes.append(bl_box)
            bl_box.parent = self.obj
        return boxes

    def duplicate(self, collections: tp.Sequence[bpy.types.Collection] = None) -> BlenderNVM:
        """Duplicate Navmesh model to a new object. Does not rename (will just add duplicate suffix)."""
        new_model = new_mesh_object(self.name, self.data.copy())
        new_model.soulstruct_type = SoulstructType.NAVMESH
        # NOTE: There are currently no properties in the 'NVM' property group.
        # Face flags and obstacle counts are stored in mesh face data layers.
        copy_obj_property_group(self.obj, new_model, "NVM")
        for collection in collections:
            collection.objects.link(new_model)

        # Copy any NVM Event Entity children of old model.
        for event_entity in self.get_nvm_event_entities():
            new_event_obj = event_entity.obj.copy()  # empty object, no data to copy
            new_event_obj.parent = new_model
            for collection in collections:
                collection.objects.link(new_event_obj)

        return self.__class__(new_model)

    def rename(self, new_name: str):
        """Rename object, data, and event entity children."""
        old_name = self.name  # TODO: export name?
        self.obj.name = new_name
        self.data.name = new_name

        for event_entity in self.get_nvm_event_entities():
            event_entity.obj.name = event_entity.name.replace(old_name, new_name)

    @staticmethod
    def create_box(context: bpy.types.Context, box: NVMBox):
        """Create an AABB prism representing `box`. Position is baked into mesh data fully, just like the navmesh."""
        start_vec = GAME_TO_BL_VECTOR(box.start_corner)
        end_vec = GAME_TO_BL_VECTOR(box.end_corner)
        bpy.ops.mesh.primitive_cube_add()
        bl_box = context.active_object
        # noinspection PyTypeChecker
        box_data = bl_box.data  # type: bpy.types.Mesh
        for vertex in box_data.vertices:
            vertex.co[0] = start_vec.x if vertex.co[0] == -1.0 else end_vec.x
            vertex.co[1] = start_vec.y if vertex.co[1] == -1.0 else end_vec.y
            vertex.co[2] = start_vec.z if vertex.co[2] == -1.0 else end_vec.z
        bpy.ops.object.modifier_add(type="WIREFRAME")
        bl_box.modifiers[0].thickness = 0.02
        return bl_box


class BlenderNVMEventEntity(SoulstructObject[NVMEventEntity, NVMEventEntityProps]):

    TYPE = SoulstructType.NVM_EVENT_ENTITY
    OBJ_DATA_TYPE = SoulstructDataType.EMPTY
    SOULSTRUCT_CLASS = NVMEventEntity

    __slots__ = []

    @property
    def entity_id(self) -> int:
        return self.type_properties.entity_id
    
    @entity_id.setter
    def entity_id(self, value: int):
        self.type_properties.entity_id = value

    @property
    def triangle_indices(self) -> list[int]:
        return [face.index for face in self.type_properties.triangle_indices]

    @triangle_indices.setter
    def triangle_indices(self, indices: list[int]):
        self.type_properties.triangle_indices.clear()
        for index in indices:
            self.type_properties.triangle_indices.add().index = index

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: NVMEventEntity,
        name: str,
        collection: bpy.types.Collection = None,
        location: Vector = None,
    ) -> BlenderNVMEventEntity:
        bl_event = cls.new(name, data=None, collection=collection)  # type: BlenderNVMEventEntity
        bl_event.obj.empty_display_type = "CUBE"  # to distinguish it from node spheres
        
        bl_event.obj.location = location or Vector()
        bl_event.entity_id = soulstruct_obj.entity_id
        bl_event.triangle_indices = soulstruct_obj.triangle_indices
        return bl_event

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
    ) -> NVMEventEntity:
        return NVMEventEntity(
            entity_id=self.entity_id,
            triangle_indices=self.triangle_indices,
        )
