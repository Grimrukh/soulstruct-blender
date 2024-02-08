from __future__ import annotations

__all__ = [
    "HKXMapCollisionExportError",
    "LOOSE_HKX_COLLISION_NAME_RE",
    "NUMERIC_HKX_COLLISION_NAME_RE",
    "load_hkxbhds",
    "find_binder_hkx_entry",
    "export_hkx_to_binder",
    "HKXMapCollisionExporter",
]

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

import bmesh
import bpy

from soulstruct.containers import Binder, BinderEntry
from soulstruct_havok.wrappers.hkx2015 import MapCollisionHKX

from io_soulstruct.utilities import *


class HKXMapCollisionExportError(Exception):
    pass


LOOSE_HKX_COLLISION_NAME_RE = re.compile(r"^([hl])(\w{6})A(\d\d)$")  # game-readable model name; no extensions
NUMERIC_HKX_COLLISION_NAME_RE = re.compile(r"^([hl])(\d{4})B(\d)A(\d\d)$")  # standard map model name; no extensions

HKX_MATERIAL_NAME_RE = re.compile(r"HKX (?P<index>\d+) \((?P<res>Hi|Lo)\).*")  # Blender HKX material name


def _get_mesh_children(
    operator: LoggingOperator, bl_parent: bpy.types.Object, get_other_resolution: bool
) -> tuple[list, list, str]:
    """Return a tuple of `(bl_meshes, other_res_bl_meshes, other_res)`.

    TODO: Deprecated, as HKX material submeshes are now merged.
    """
    bl_meshes = []
    other_res_bl_meshes = []
    other_res = ""

    target_res = bl_parent.name[0]
    if get_other_resolution:
        match target_res:
            case "h":
                other_res = "l"
            case "l":
                other_res = "h"
            case _:
                raise HKXMapCollisionExportError(
                    f"Selected Empty parent '{bl_parent.name}' must start with 'h' or 'l' to get other resolution."
                )

    for child in bl_parent.children:
        child_res = child.name.lower()[0]
        if child.type != "MESH":
            operator.warning(f"Ignoring non-mesh child '{child.name}' of selected Empty parent.")
        elif child_res == target_res:
            bl_meshes.append(child)
        elif get_other_resolution and child_res == other_res:  # cannot be empty here
            other_res_bl_meshes.append(child)
        else:
            operator.warning(f"Ignoring child '{child.name}' of selected Empty parent with non-'h', non-'l' name.")

    # Ensure meshes have the same order as they do in the Blender viewer.
    bl_meshes.sort(key=lambda obj: natural_keys(obj.name))
    other_res_bl_meshes.sort(key=lambda obj: natural_keys(obj.name))

    return bl_meshes, other_res_bl_meshes, other_res


def load_hkxbhds(hi_hkxbhd_path: Path = None, lo_hkxbhd_path: Path = None) -> tuple[Binder | None, Binder | None]:
    """Load the given 'hi' and 'lo' HKXBHD files."""

    if hi_hkxbhd_path:
        if not hi_hkxbhd_path.is_file():
            raise HKXMapCollisionExportError(f"Could not find 'hi' HKXBHD file '{hi_hkxbhd_path}'.")
        hi_hkxbhd = Binder.from_path(hi_hkxbhd_path)
    else:
        hi_hkxbhd = None

    if lo_hkxbhd_path:
        if not lo_hkxbhd_path.is_file():
            raise HKXMapCollisionExportError(f"Could not find 'lo' HKXBHD file '{lo_hkxbhd_path}'.")
        lo_hkxbhd = Binder.from_path(lo_hkxbhd_path)
    else:
        lo_hkxbhd = None

    return hi_hkxbhd, lo_hkxbhd


def find_binder_hkx_entry(
    operator: LoggingOperator,
    binder: Binder,
    hkx_entry_stem: str,
    default_entry_path: str,
    default_entry_flags: int,
    overwrite_existing: bool,
    map_stem="",
) -> BinderEntry:
    """Find or create a Binder entry for the given `hkx_entry_stem` in the given `binder`."""

    matching_entries = binder.find_entries_matching_name(rf"{hkx_entry_stem}\.hkx(\.dcx)?")

    if not matching_entries:
        # Create new entry.
        if "{map}" in default_entry_path:
            if not map_stem:
                if match := NUMERIC_HKX_COLLISION_NAME_RE.match(hkx_entry_stem):
                    block, area = int(match.group(3)), int(match.group(4))
                    map_stem = f"m{area:02d}_{block:02d}_00_00"
                else:
                    raise HKXMapCollisionExportError(
                        f"Could not determine '{{map}}' for new Binder entry from HKX name: {hkx_entry_stem}. It must "
                        f"be in the format '[hl]####A#B##' for map name 'mAA_BB_00_00' to be detected."
                    )
            entry_path = default_entry_path.format(map=map_stem, name=hkx_entry_stem)
        else:
            entry_path = default_entry_path.format(name=hkx_entry_stem)
        new_entry_id = binder.highest_entry_id + 1
        hkx_entry = BinderEntry(
            b"", entry_id=new_entry_id, path=entry_path, flags=default_entry_flags
        )
        binder.add_entry(hkx_entry)
        operator.info(f"Creating new Binder entry: ID {new_entry_id}, path '{entry_path}'")
        return hkx_entry

    if not overwrite_existing:
        raise HKXMapCollisionExportError(
            f"HKX named '{hkx_entry_stem}' already exists in Binder and overwrite is disabled."
        )

    entry = matching_entries[0]
    if len(matching_entries) > 1:
        operator.warning(
            f"Multiple HKXs named '{hkx_entry_stem}' found in Binder. Replacing first: {entry.name}"
        )
    else:
        operator.info(f"Replacing existing Binder entry: ID {entry.id}, path '{entry.path}'")
    return matching_entries[0]


def export_hkx_to_binder(
    operator: LoggingOperator,
    hkx: MapCollisionHKX,
    hkxbhd: Binder,
    hkx_entry_stem: str,
    default_entry_path: str,
    default_entry_flags: int,
    overwrite_existing: bool,
    map_stem="",
):
    """Export the given `hkx` to the given `hkxbhd` as an entry with the given `hkx_entry_stem`."""

    # Find Binder entry.
    try:
        hkx_entry = find_binder_hkx_entry(
            operator,
            hkxbhd,
            hkx_entry_stem,
            default_entry_path,
            default_entry_flags,
            overwrite_existing,
            map_stem,
        )
    except Exception as ex:
        raise HKXMapCollisionExportError(f"Cannot find or create Binder entry for '{hkx_entry_stem}'. Error: {ex}")

    try:
        hkx_entry.set_from_binary_file(hkx)
    except Exception as ex:
        raise HKXMapCollisionExportError(f"Cannot pack exported HKX '{hkx_entry_stem}' into Binder entry. Error: {ex}")


@dataclass(slots=True)
class HKXMapCollisionExporter:
    """Only has one real method, but staying consistent with other file types."""

    operator: LoggingOperator
    context: bpy.types.Context

    def warning(self, msg: str):
        self.operator.report({"WARNING"}, msg)

    def export_hkx_map_collision(
        self,
        hkx_model: bpy.types.MeshObject,
        hi_name: str | None,
        lo_name: str | None,
        require_hi=True,
        use_hi_if_missing_lo=False,
    ) -> tuple[MapCollisionHKX | None, MapCollisionHKX | None]:
        """Create 'hi' and/or 'lo' HKX files by splitting given `hkx_model` into submeshes by material.

        `hi_name` and `lo_name` are required to set internally to the HKX file (though it probably doesn't impact
        gameplay). If passed explicitly as `None`, those submeshes will be ignored -- but they cannot BOTH be `None`.

        TODO: Currently only supported for DS1R and Havok 2015.

        TODO: Add an argument to duplicate hi-res as lo-res if no lo-res materials exist.
        """
        if not hi_name and not lo_name:
            raise ValueError("At least one of 'hi_name' and 'lo_name' must be provided.")
        if not hkx_model.material_slots:
            raise ValueError(f"HKX model mesh '{hkx_model.name}' has no materials for submesh detection.")

        # Automatically triangulate the mesh.
        self._clear_temp_hkx()
        bm = bmesh.new()
        bm.from_mesh(hkx_model.data)
        bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
        tri_mesh_data = bpy.data.meshes.new("__TEMP_HKX__")
        # No need to copy materials over (no UV, etc.)
        bm.to_mesh(tri_mesh_data)
        bm.free()
        del bm

        hi_hkx_meshes = []  # type: list[tuple[np.ndarray, np.ndarray]]  # vertices, faces
        hi_hkx_material_indices = []  # type: list[int]
        lo_hkx_meshes = []  # type: list[tuple[np.ndarray, np.ndarray]]  # vertices, faces
        lo_hkx_material_indices = []  # type: list[int]

        # Note that it is possible that the user may have faces with different materials share vertices; this is fine,
        # and that vertex will be copied into each HKX submesh with a face loop that uses it.

        # Rather than iterating over all faces once for every material, we iterate over all of them once to split them
        # up by material index, then iterate once over each of those sublists (so the full face list is iterated twice).
        faces_by_material = {i: [] for i in range(len(hkx_model.material_slots))}
        for face in tri_mesh_data.polygons:
            try:
                faces_by_material[face.material_index].append(face)
            except KeyError:
                raise HKXMapCollisionExportError(
                    f"Face {face.index} of mesh '{hkx_model.name}' has material index {face.material_index}, "
                    f"which is not in the material slots of the mesh."
                )

        # Now iterate over each sublist of faces and create lists of HKX vertices and faces for each one. We maintain
        # a vertex map that maps the original full-mesh Blender vertex index to the submesh index.
        for bl_material_index, faces in faces_by_material.items():
            if not faces:
                continue  # no faces use this material

            # We can use the original non-triangulated mesh's material slots.
            bl_material = hkx_model.material_slots[bl_material_index].material
            mat_match = HKX_MATERIAL_NAME_RE.match(bl_material.name)
            if not mat_match:
                raise HKXMapCollisionExportError(
                    f"Material '{bl_material.name}' of mesh '{hkx_model.name}' does not match expected HKX material "
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
                            [vert.co.x, vert.co.z, vert.co.y]  # may as well swap Y and Z coordinates here
                        )
                    else:
                        # Vertex has already been used by this submesh.
                        hkx_vert_index = vertex_map[vert_index]
                    hkx_face.append(hkx_vert_index)
                hkx_faces_list.append(hkx_face)

            meshes, hkx_material_indices = (
                (hi_hkx_meshes, hi_hkx_material_indices) if res == "h" else (lo_hkx_meshes, lo_hkx_material_indices)
            )
            meshes.append(
                (np.array(hkx_verts_list, dtype=np.float32), np.array(hkx_faces_list, dtype=np.uint32))
            )
            hkx_material_indices.append(hkx_material_index)

        self._clear_temp_hkx()

        if hi_hkx_meshes:
            hi_hkx = MapCollisionHKX.from_meshes(
                meshes=hi_hkx_meshes,
                hkx_name=hi_name,
                material_indices=hi_hkx_material_indices,
                # Bundled template HKX serves fine.
                # DCX applied by caller.
            )
        else:
            if require_hi:
                raise HKXMapCollisionExportError(
                    f"No 'hi' HKX meshes found in mesh '{hkx_model.name}'."
                )
            self.warning(f"No 'hi' HKX meshes found in mesh '{hkx_model.name}' and `require_hi=False`.")
            hi_hkx = None

        if lo_hkx_meshes:
            lo_hkx = MapCollisionHKX.from_meshes(
                meshes=lo_hkx_meshes,
                hkx_name=lo_name,
                material_indices=lo_hkx_material_indices,
                # Bundled template HKX serves fine.
                # DCX applied by caller.
            )
        elif use_hi_if_missing_lo:
            # Duplicate hi-res meshes and materials for lo-res (but use lo-res name).
            lo_hkx = MapCollisionHKX.from_meshes(
                meshes=hi_hkx_meshes,
                hkx_name=lo_name,
                material_indices=hi_hkx_material_indices,
                # Bundled template HKX serves fine.
                # DCX applied by caller.
            )
        else:
            self.warning(f"No 'lo' HKX meshes found for '{lo_name}' and `use_hi_as_missing_lo=False`.")
            lo_hkx = None

        if not hi_hkx and not lo_hkx:
            raise HKXMapCollisionExportError(
                f"No material-based HKX submeshes could be created for HKX mesh '{hkx_model.name}'. Are all faces "
                f"assigned to a material with name template 'HKX # (Hi|Lo)'?"
            )

        return hi_hkx, lo_hkx

    @staticmethod
    def _clear_temp_hkx():
        try:
            bpy.data.meshes.remove(bpy.data.meshes["__TEMP_HKX__"])
        except KeyError:
            pass
