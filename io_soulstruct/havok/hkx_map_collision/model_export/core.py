from __future__ import annotations

__all__ = [
    "HKXMapCollisionExportError",
    "LOOSE_HKX_COLLISION_NAME_RE",
    "NUMERIC_HKX_COLLISION_NAME_RE",
    "get_mesh_children",
    "load_hkxbhds",
    "find_binder_hkx_entry",
    "export_hkx_to_binder",
    "HKXMapCollisionExporter",
]

import re
from pathlib import Path

import numpy as np

import bmesh
import bpy

from soulstruct.dcx import DCXType
from soulstruct.containers import Binder, BinderEntry
from soulstruct_havok.wrappers.hkx2015 import MapCollisionHKX

from io_soulstruct.utilities import *


class HKXMapCollisionExportError(Exception):
    pass


LOOSE_HKX_COLLISION_NAME_RE = re.compile(r"^([hl])(\w{6})A(\d\d)$")  # game-readable model name; no extensions
NUMERIC_HKX_COLLISION_NAME_RE = re.compile(r"^([hl])(\d{4})B(\d)A(\d\d)$")  # standard map model name; no extensions


def get_mesh_children(
    operator: LoggingOperator, bl_parent: bpy.types.Object, get_other_resolution: bool
) -> tuple[list, list, str]:
    """Return a tuple of `(bl_meshes, other_res_bl_meshes, other_res)`."""
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


def load_hkxbhds(hkxbhd_path: Path, other_res: str = "") -> tuple[Binder, Binder | None]:
    """Load the HKXBHD file at `hkxbhd_path` and the other resolution HKXBHD file (if `other_res` is given)."""

    try:
        hkxbhd = Binder.from_path(hkxbhd_path)
    except Exception as ex:
        raise HKXMapCollisionExportError(f"Could not load HKXBHD file '{hkxbhd_path}'. Error: {ex}")

    if not other_res:
        return hkxbhd, None

    other_res_hkxbhd = None  # type: Binder | None
    other_res_binder_name = f"{other_res}{hkxbhd_path.name[1:]}"
    other_res_binder_path = hkxbhd_path.with_name(other_res_binder_name)
    try:
        other_res_hkxbhd = Binder.from_path(other_res_binder_path)
    except Exception as ex:
        raise HKXMapCollisionExportError(
            f"Could not load HKXBHD file '{other_res_hkxbhd}' for other resolution. Error: {ex}"
        )
    return hkxbhd, other_res_hkxbhd


def find_binder_hkx_entry(
    operator: LoggingOperator,
    binder: Binder,
    hkx_entry_stem: str,
    default_entry_path: str,
    default_entry_flags: int,
    overwrite_existing: bool,
    map_stem="",
) -> BinderEntry:
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
    context: bpy.types.Context,
    bl_meshes: list[bpy.types.MeshObject],
    hkxbhd: Binder,
    hkx_entry_stem: str,
    dcx_type: DCXType,
    default_entry_path: str,
    default_entry_flags: int,
    overwrite_existing: bool,
    map_stem="",
):
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

    # TODO: Not needed for meshes only?
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

    exporter = HKXMapCollisionExporter(operator, context)

    try:
        hkx = exporter.export_hkx_map_collision(bl_meshes, name=hkx_entry_stem)
    except Exception as ex:
        raise HKXMapCollisionExportError(f"Cannot get exported HKX for '{hkx_entry_stem}'. Error: {ex}")
    hkx.dcx_type = dcx_type

    try:
        hkx_entry.set_from_binary_file(hkx)
    except Exception as ex:
        raise HKXMapCollisionExportError(f"Cannot pack exported HKX '{hkx_entry_stem}' into Binder entry. Error: {ex}")


class HKXMapCollisionExporter:
    operator: LoggingOperator

    def __init__(self, operator: LoggingOperator, context):
        self.operator = operator
        self.context = context

    def warning(self, msg: str):
        self.operator.report({"WARNING"}, msg)
        print(f"# WARNING: {msg}")

    @staticmethod
    def _clear_temp_hkx():
        try:
            bpy.data.meshes.remove(bpy.data.meshes["__TEMP_HKX__"])
        except KeyError:
            pass

    def export_hkx_map_collision(self, bl_meshes, name: str) -> MapCollisionHKX:
        """Create HKX from Blender meshes (subparts).

        `name` is needed to set internally to the HKX file (though it probably doesn't impact gameplay).

        TODO: Currently only supported for DS1R and Havok 2015.
        """
        if not bl_meshes:
            raise ValueError("No meshes given to export to HKX.")

        hkx_meshes = []  # type: list[tuple[np.ndarray, np.ndarray]]
        hkx_material_indices = []  # type: list[int]

        for bl_mesh in bl_meshes:

            if bl_mesh.get("Material Index", None) is None and bl_mesh.get("material_index", None) is not None:
                # NOTE: Legacy code for previous name of this property. TODO: Remove after a few releases.
                material_index = get_bl_prop(bl_mesh, "material_index", int, default=0)
                # Move property to new name.
                bl_mesh["Material Index"] = material_index
                del bl_mesh["material_index"]
            else:
                material_index = get_bl_prop(bl_mesh, "Material Index", int, default=0)
            hkx_material_indices.append(material_index)

            self._clear_temp_hkx()

            # Automatically triangulate the mesh.
            bm = bmesh.new()
            bm.from_mesh(bl_mesh.data)
            bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
            tri_mesh_data = bpy.data.meshes.new("__TEMP_HKX__")
            # No need to copy materials over (no UV, etc.)
            bm.to_mesh(tri_mesh_data)
            bm.free()
            del bm

            # Swap Y and Z coordinates.
            hkx_verts_list = [[vert.co.x, vert.co.z, vert.co.y] for vert in tri_mesh_data.vertices]
            hkx_verts = np.array(hkx_verts_list, dtype=np.float32)
            hkx_faces = np.empty((len(tri_mesh_data.polygons), 3), dtype=np.uint32)  # we know all faces are triangles
            tri_mesh_data.polygons.foreach_get("vertices", hkx_faces.ravel())

            hkx_meshes.append((hkx_verts, hkx_faces))

        self._clear_temp_hkx()

        hkx = MapCollisionHKX.from_meshes(
            meshes=hkx_meshes,
            hkx_name=name,
            material_indices=hkx_material_indices,
            # Bundled template HKX serves fine.
            # DCX applied by caller.
        )

        return hkx
