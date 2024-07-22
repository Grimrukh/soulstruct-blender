from __future__ import annotations

__all__ = [
    "NVMImportInfo",
    "NVMImporter",
]

import typing as tp
from dataclasses import dataclass, field
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

from soulstruct.darksouls1r.maps.navmesh.nvm import NVM, NVMBox, NVMEventEntity

from io_soulstruct.navmesh.nvm.utilities import *
from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities import *


class NVMImportInfo(tp.NamedTuple):
    """Holds information about a navmesh to import into Blender."""
    path: Path  # source file for NVM (likely a Binder path)
    model_file_stem: str  # generally stem of NVM file or Binder entry
    bl_name: str  # name to assign to Blender object (usually same as `model_file_stem`)
    nvm: NVM  # parsed NVM


@dataclass(slots=True)
class NVMImporter:
    """Manages imports for a batch of NVM files imported simultaneously."""

    operator: LoggingOperator
    context: bpy.types.Context
    collection: bpy.types.Collection = None

    all_bl_objs: list[bpy.types.Object] = field(default_factory=list)  # all objects created during import
    imported_models: dict[str, bpy.types.Object] = field(default_factory=dict)  # model file stem -> Blender object

    def __post_init__(self):
        if not self.collection:
            self.collection = self.context.scene.collection

    def import_nvm(
        self, import_info: NVMImportInfo, use_material=True, create_quadtree_boxes=False
    ) -> bpy.types.MeshObject:
        """Read a NVM into a Blender mesh object."""

        # Set mode to OBJECT and deselect all objects.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action="DESELECT")
        if bpy.ops.object.mode_set.poll():  # just to be safe
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        # Create mesh.
        nvm = import_info.nvm
        bl_mesh = bpy.data.meshes.new(name=import_info.bl_name)
        vertices = GAME_TO_BL_ARRAY(nvm.vertices)
        edges = []  # no edges in NVM
        faces = [triangle.vertex_indices for triangle in nvm.triangles]
        bl_mesh.from_pydata(vertices, edges, faces)
        # noinspection PyTypeChecker
        mesh_obj = bpy.data.objects.new(import_info.bl_name, bl_mesh)  # type: bpy.types.MeshObject
        mesh_obj.soulstruct_type = SoulstructType.NAVMESH
        self.collection.objects.link(mesh_obj)
        self.all_bl_objs = [mesh_obj]

        if use_material:
            for bl_face, nvm_triangle in zip(bl_mesh.polygons, nvm.triangles):
                set_face_material(bl_mesh, bl_face, nvm_triangle.flags)

        # Create `BMesh` (as we need to assign face flag data to a custom `int` layer).
        bm = bmesh.new()
        bm.from_mesh(bl_mesh)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        flags_layer = bm.faces.layers.int.new("nvm_face_flags")
        obstacle_count_layer = bm.faces.layers.int.new("nvm_face_obstacle_count")

        for f_i, face in enumerate(bm.faces):
            nvm_triangle = nvm.triangles[f_i]
            face[flags_layer] = nvm_triangle.flags
            face[obstacle_count_layer] = nvm_triangle.obstacle_count

        for event in nvm.event_entities:
            bl_event = self.create_event_entity(event, bm.faces, import_info.bl_name)
            self.collection.objects.link(bl_event)
            self.all_bl_objs.append(bl_event)
            bl_event.parent = mesh_obj

        bm.to_mesh(bl_mesh)
        del bm

        if create_quadtree_boxes:
            self.create_nvm_quadtree(mesh_obj, nvm, import_info.bl_name)

        self.imported_models[import_info.model_file_stem] = mesh_obj

        return mesh_obj

    def create_nvm_quadtree(self, bl_mesh, nvm: NVM, bl_name: str) -> list[bpy.types.Object]:
        """Create box tree (depth first creation order).

        NOTE: These boxes should be imported for inspection only. They are automatically generated from the mesh
        min/max vertex coordinates on NVM export.
        """
        boxes = []
        for box, indices in nvm.get_all_boxes(nvm.root_box):
            if not indices:
                box_name = f"{bl_name} Box ROOT"
            else:
                indices_string = "-".join(str(i) for i in indices)
                box_name = f"{bl_name} Box {indices_string}"
            bl_box = self.create_box(box)
            self.collection.objects.link(bl_box)
            bl_box.name = box_name
            boxes.append(bl_box)
            self.all_bl_objs.append(bl_box)
            bl_box.parent = bl_mesh
        return boxes

    @staticmethod
    def create_box(box: NVMBox):
        """Create an AABB prism representing `box`. Position is baked into mesh data fully, just like the navmesh."""
        start_vec = GAME_TO_BL_VECTOR(box.start_corner)
        end_vec = GAME_TO_BL_VECTOR(box.end_corner)
        bpy.ops.mesh.primitive_cube_add()
        bl_box = bpy.context.active_object
        # noinspection PyTypeChecker
        box_data = bl_box.data  # type: bpy.types.Mesh
        for vertex in box_data.vertices:
            vertex.co[0] = start_vec.x if vertex.co[0] == -1.0 else end_vec.x
            vertex.co[1] = start_vec.y if vertex.co[1] == -1.0 else end_vec.y
            vertex.co[2] = start_vec.z if vertex.co[2] == -1.0 else end_vec.z
        bpy.ops.object.modifier_add(type="WIREFRAME")
        bl_box.modifiers[0].thickness = 0.02
        return bl_box

    @staticmethod
    def create_event_entity(
        nvm_event_entity: NVMEventEntity, bm_faces: bmesh.types.BMFaceSeq | list[bmesh.types.BMFace], bl_nvm_name: str
    ):
        """Create an Empty child that just holds the ID and triangle indices of a NVM event entity.

        Object is placed at the centroid of the faces it references, but this is just for convenience, and does not
        affect export. The user should move the event around if they change the attached faces.
        """
        bl_event = bpy.data.objects.new(f"{bl_nvm_name} Event {nvm_event_entity.entity_id}", None)
        bl_event.empty_display_type = "CUBE"  # to distinguish it from node spheres

        # Get the average position of the faces.
        avg_pos = Vector((0, 0, 0))
        for i in nvm_event_entity.triangle_indices:
            avg_pos += bm_faces[i].calc_center_median()
        avg_pos /= len(nvm_event_entity.triangle_indices)
        bl_event.location = avg_pos

        bl_event["entity_id"] = nvm_event_entity.entity_id
        bl_event["triangle_indices"] = nvm_event_entity.triangle_indices
        return bl_event
