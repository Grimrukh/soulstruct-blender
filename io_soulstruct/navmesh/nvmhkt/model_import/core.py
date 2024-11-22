from __future__ import annotations

__all__ = [
    "NVMHKTImporter",
]

from dataclasses import dataclass, field

import bpy

from soulstruct_havok.fromsoft.eldenring import NavmeshHKX

from io_soulstruct.utilities import *


@dataclass(slots=True)
class NVMHKTImporter:
    """Manages imports for a batch of NVMHKT files imported simultaneously."""

    operator: LoggingOperator
    context: bpy.types.Context
    collection: bpy.types.Collection = None

    all_bl_objs: list[bpy.types.Object] = field(default_factory=list)  # all objects created during import

    def __post_init__(self):
        if not self.collection:
            self.collection = self.context.scene.collection

    def import_nvmhkt(
        self, nvmhkt: NavmeshHKX, name: str, use_material=True, vertex_merge_dist=0.0,
    ) -> bpy.types.MeshObject:
        """Read a NVMHKT into a Blender mesh object."""

        # Set mode to OBJECT and deselect all objects.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action="DESELECT")
        if bpy.ops.object.mode_set.poll():  # just to be safe
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        # Create mesh.
        bl_mesh = bpy.data.meshes.new(name=name)
        mesh = nvmhkt.get_simple_mesh(merge_dist=vertex_merge_dist)
        vertices = GAME_TO_BL_ARRAY(mesh.vertices)
        bl_mesh.from_pydata(vertices, [], mesh.faces)
        # noinspection PyTypeChecker
        mesh_obj = bpy.data.objects.new(name, bl_mesh)  # type: bpy.types.MeshObject
        self.collection.objects.link(mesh_obj)
        self.all_bl_objs = [mesh_obj]

        # TODO: Get Elden Ring face flags from HKX?
        # if use_material:
        #     for bl_face, nvm_triangle in zip(bl_mesh.polygons, nvm.triangles):
        #         set_face_material(bl_mesh, bl_face, nvm_triangle.flags)

        if use_material:
            # TODO: Setting Default material to all faces.
            try:
                bl_material = bpy.data.materials["Navmesh Flag <Default>"]
            except KeyError:
                color = hsv_color(0.8, 0.9, 0.5)  # MAGENTA
                bl_material = create_basic_material("Navmesh Flag <Default>", color, wireframe_pixel_width=2)
            bl_mesh.materials.append(bl_material)

        return mesh_obj
