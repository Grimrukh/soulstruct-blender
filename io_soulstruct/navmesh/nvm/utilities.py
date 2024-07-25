from __future__ import annotations

__all__ = [
    "ANY_NVM_NAME_RE",
    "STANDARD_NVM_STEM_RE",
    "NVMBND_NAME_RE",
    "NAVMESH_FLAG_COLORS",
    "NAVMESH_MULTIPLE_FLAG_COLOR",
    "NVMImportInfo",
    "set_face_material",
]

import re
import typing as tp
from pathlib import Path

import bpy
from io_soulstruct.utilities.materials import hsv_color, create_basic_material
from soulstruct.darksouls1r.maps.navmesh import NVM, NavmeshFlag

ANY_NVM_NAME_RE = re.compile(r"^(?P<stem>.*)\.nvm(?P<dcx>\.dcx)?$")
STANDARD_NVM_STEM_RE = re.compile(r"^n(\d{4})B(?P<B>\d)A(?P<A>\d{2})$")  # no extensions
NVMBND_NAME_RE = re.compile(r"^.*?\.nvmbnd(\.dcx)?$")


# In descending priority order. All flags can be inspected in custom properties.
NAVMESH_FLAG_COLORS = {
    NavmeshFlag.Disable: hsv_color(0.0, 0.0, 0.1),  # DARK GREY
    NavmeshFlag.Degenerate: hsv_color(0.0, 0.0, 0.1),  # DARK GREY
    NavmeshFlag.Obstacle: hsv_color(0.064, 0.9, 0.2),  # DARK ORANGE
    NavmeshFlag.BlockExit: hsv_color(0.3, 0.9, 1.0),  # LIGHT GREEN
    NavmeshFlag.Hole: hsv_color(0.066, 0.9, 0.5),  # ORANGE
    NavmeshFlag.Ladder: hsv_color(0.15, 0.9, 0.5),  # YELLOW
    NavmeshFlag.ClosedDoor: hsv_color(0.66, 0.9, 0.25),  # DARK BLUE
    NavmeshFlag.Exit: hsv_color(0.33, 0.9, 0.15),  # DARK GREEN
    NavmeshFlag.Door: hsv_color(0.66, 0.9, 0.75),  # LIGHT BLUE
    NavmeshFlag.InsideWall: hsv_color(0.4, 0.9, 0.3),  # TURQUOISE
    NavmeshFlag.Edge: hsv_color(0.066, 0.9, 0.5),  # ORANGE
    NavmeshFlag.FloorBeneathWall: hsv_color(0.0, 0.8, 0.8),  # LIGHT RED
    NavmeshFlag.LandingPoint: hsv_color(0.4, 0.9, 0.7),  # LIGHT TURQUOISE
    NavmeshFlag.LargeSpace: hsv_color(0.7, 0.9, 0.7),  # PURPLE
    NavmeshFlag.Event: hsv_color(0.5, 0.9, 0.5),  # CYAN
    NavmeshFlag.Wall: hsv_color(0.0, 0.8, 0.1),  # DARK RED
    NavmeshFlag.Default: hsv_color(0.8, 0.9, 0.5),  # MAGENTA
}
NAVMESH_MULTIPLE_FLAG_COLOR = hsv_color(0.0, 0.0, 1.0)  # WHITE
NAVMESH_UNKNOWN_FLAG_COLOR = hsv_color(0.0, 0.0, 0.25)  # GREY


class NVMImportInfo(tp.NamedTuple):
    """Holds information about a navmesh to import into Blender."""
    path: Path  # source file for NVM (likely a Binder path)
    model_file_stem: str  # generally stem of NVM file or Binder entry
    bl_name: str  # name to assign to Blender object (usually same as `model_file_stem`)
    nvm: NVM  # parsed NVM


def set_face_material(bl_mesh, bl_face, face_flags: int):
    """Set face materials according to their `NVMTriangle` flags.

    Searches for existing materials on the mesh with names like "Navmesh Flag <flag_name>", and creates them with
    simple diffuse colors if they don't exist in the Blender session yet.

    NOTE: `bl_face` can be from a `Mesh` or `BMesh`. Both have `material_index`.
    """

    # Color face according to its single `flag` if present.
    try:
        flag = NavmeshFlag(face_flags)
        material_name = f"Navmesh Flag {flag.name}"
    except ValueError:  # multiple flags
        flag = None
        material_name = "Navmesh Flag <Multiple>"

    material_index = bl_mesh.materials.find(material_name)
    if material_index >= 0:
        bl_face.material_index = material_index
        return bl_mesh.materials[material_name]

    # Try to get existing material from Blender.
    try:
        bl_material = bpy.data.materials[material_name]
    except KeyError:
        # Create new material with color from dictionary.
        if flag is None:
            color = NAVMESH_MULTIPLE_FLAG_COLOR
        else:
            try:
                color = NAVMESH_FLAG_COLORS[flag]
            except (ValueError, KeyError):
                # Unspecified flag color.
                color = NAVMESH_UNKNOWN_FLAG_COLOR
        bl_material = create_basic_material(material_name, color, wireframe_pixel_width=2)

    # Add material to this mesh and this face.
    bl_face.material_index = len(bl_mesh.materials)
    bl_mesh.materials.append(bl_material)
    return bl_material
