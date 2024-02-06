from __future__ import annotations

__all__ = [
    "HKXImportInfo",
    "load_other_res_hkx",
    "HKXMapCollisionImportError",
    "HKXMapCollisionImporter",
]

import typing as tp
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

import bpy

from soulstruct.containers import Binder, EntryNotFoundError
from soulstruct_havok.wrappers.hkx2015 import MapCollisionHKX

from io_soulstruct.utilities import *
from io_soulstruct.utilities.materials import *


# HSV values for HKX materials, out of 360/100/100.
HKX_MATERIAL_COLORS = {
    0: (0, 0, 100),  # default (white)
    1: (24, 75, 70),  # rock (orange)
    2: (130, 0, 40),  # stone (grey)
    3: (114, 58, 57),  # grass (green)
    4: (36, 86, 43),  # wood (dark brown)

    20: (214, 75, 64),  # under shallow water (light blue)
    21: (230, 85, 64),  # under deep water (dark blue)

    40: (50, 68, 80),  # trigger only (yellow)
}


class HKXImportInfo(tp.NamedTuple):
    """Holds information about a HKX to import into Blender."""
    path: Path  # source file for HKX (possibly a Binder path)
    hkx_name: str  # name of HKX file or Binder entry
    hkx: MapCollisionHKX  # parsed HKX


def load_other_res_hkx(
    operator: LoggingOperator, file_path: Path, import_info: HKXImportInfo, is_binder: bool
) -> MapCollisionHKX | None:
    match import_info.hkx_name[0]:
        case "h":
            other_res = "l"
        case "l":
            other_res = "h"
        case _:
            operator.warning(f"Could not determine resolution (h/l) of HKX '{import_info.hkx_name}'.")
            return None
    if is_binder:
        # Look for other-resolution binder and find matching other-res HKX entry.
        other_res_binder_path = file_path.parent / f"{other_res}{file_path.name[1:]}"
        if not other_res_binder_path.is_file():
            operator.warning(
                f"Could not find corresponding '{other_res}' collision binder for '{file_path.name}'."
            )
            return None
        other_res_binder = Binder.from_path(other_res_binder_path)
        other_hkx_name = f"{other_res}{import_info.hkx_name[1:]}"
        try:
            other_res_hkx_entry = other_res_binder.find_entry_name(other_hkx_name)
        except EntryNotFoundError:
            operator.warning(
                f"Found corresponding '{other_res}' collision binder, but could not find corresponding "
                f"HKX entry '{other_hkx_name}' inside it."
            )
            return None
        try:
            other_res_hkx = MapCollisionHKX.from_binder_entry(other_res_hkx_entry)
        except Exception as ex:
            operator.warning(
                f"Error occurred while reading corresponding '{other_res}' HKX file "
                f"'{other_res_hkx_entry.path}': {ex}"
            )
            return None
        return other_res_hkx

    # Look for other-resolution loose HKX in same directory (e.g. DS1: PTDE).
    other_hkx_path = file_path.parent / f"{other_res}{file_path.name[1:]}"
    if not other_hkx_path.is_file():
        operator.warning(
            f"Could not find corresponding '{other_res}' collision HKX for '{file_path.name}'."
        )
        return None
    try:
        other_res_hkx = MapCollisionHKX.from_path(other_hkx_path)
    except Exception as ex:
        operator.warning(
            f"Error occurred while reading corresponding '{other_res}' HKX file "
            f"'{other_hkx_path}': {ex}"
        )
        return None
    return other_res_hkx


class HKXMapCollisionImportError(Exception):
    pass


@dataclass(slots=True)
class HKXMapCollisionImporter:
    """Manages imports for a batch of HKX files imported simultaneously."""

    operator: LoggingOperator
    context: bpy.types.Context
    collection: bpy.types.Collection = None

    # Set per import.
    hkx: MapCollisionHKX | None = None
    bl_name: str = ""
    all_bl_objs: list[bpy.types.Object] = field(default_factory=list)

    def __post_init__(self):
        if self.collection is None:
            self.collection = self.context.scene.collection

    def import_hkx(
        self, hkx: MapCollisionHKX, bl_name: str, use_material=True, existing_parent=None
    ) -> tuple[bpy.types.Object, list[bpy.types.MeshObject]]:
        """Read a HKX into a collection of Blender mesh objects.

        TODO: Create only one mesh and use material slots? Unsure.
        """
        self.hkx = hkx
        self.bl_name = bl_name  # should not have extensions (e.g. `h0100B0A10`)

        # Set mode to OBJECT and deselect all objects.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action="DESELECT")
        if bpy.ops.object.mode_set.poll():  # just to be safe
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        if existing_parent:
            hkx_parent = existing_parent
        else:
            # Empty parent.
            hkx_parent = bpy.data.objects.new(bl_name, None)
            self.context.scene.collection.objects.link(hkx_parent)
            self.all_bl_objs = [hkx_parent]

        meshes = self.hkx.to_meshes()
        material_indices = self.hkx.map_collision_physics_data.get_subpart_materials()
        if bl_name.startswith("h"):
            is_hi_res = True
        elif bl_name.startswith("l"):
            is_hi_res = False
        else:
            is_hi_res = True
            self.operator.warning(f"Cannot determine if HKX is hi-res or lo-res: {bl_name}. Defaulting to hi-res.")

        # NOTE: We include the collision's full name in each submesh so that Blender does not add '.001' suffixes to
        # distinguish them across collisions (which could be a problem even if we just leave off the map indicator).
        # However, on export, only the first (lower-cased) letter of each submesh is used to check its resolution.
        submesh_name_prefix = f"{bl_name} Submesh"
        bl_meshes = []
        for i, (vertices, faces) in enumerate(meshes):

            # Swap vertex Y and Z coordinates.
            vertices = np.c_[vertices[:, 0], vertices[:, 2], vertices[:, 1]]
            mesh_name = f"{submesh_name_prefix} {i}"
            bl_mesh = self.create_mesh_obj(vertices, faces, material_indices[i], mesh_name)
            if use_material:
                bl_material = self.create_hkx_material(material_indices[i], is_hi_res)
                bl_mesh.data.materials.append(bl_material)
            bl_meshes.append(bl_mesh)

        return hkx_parent, bl_meshes

    @staticmethod
    def create_hkx_material(hkx_material_index: int, is_hi_res: bool) -> bpy.types.Material:
        material_name = f"HKX Material {hkx_material_index} ({'Hi' if is_hi_res else 'Lo'})"
        try:
            return bpy.data.materials[material_name]
        except KeyError:
            pass
        offset_100, mod_index = divmod(hkx_material_index, 100)
        h, s, v = HKX_MATERIAL_COLORS.get(mod_index, (340, 74, 70))  # defaults to red
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


    def create_mesh_obj(
        self,
        vertices: np.ndarray,
        faces: np.ndarray,
        material_index: int,
        mesh_name: str,
    ) -> bpy.types.MeshObject:
        """Create a Blender mesh object. The only custom property for HKX is material index."""
        bl_mesh = bpy.data.meshes.new(name=mesh_name)

        edges = []  # no edges in HKX
        bl_mesh.from_pydata(vertices, edges, faces)

        bl_mesh_obj = bpy.data.objects.new(mesh_name, bl_mesh)
        self.collection.objects.link(bl_mesh_obj)
        self.all_bl_objs.append(bl_mesh_obj)
        bl_mesh_obj.parent = self.all_bl_objs[0]
        bl_mesh_obj["Material Index"] = material_index

        # noinspection PyTypeChecker
        return bl_mesh_obj
