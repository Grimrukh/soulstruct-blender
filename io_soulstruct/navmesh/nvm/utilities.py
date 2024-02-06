from __future__ import annotations

__all__ = [
    "ANY_NVM_NAME_RE",
    "STANDARD_NVM_STEM_RE",
    "NVMBND_NAME_RE",
    "NVM_MESH_TYPING",
    "NAVMESH_FLAG_COLORS",
    "NAVMESH_MULTIPLE_FLAG_COLOR",
    "get_navmesh_msb_transforms",
    "set_face_material",
]

import re
import typing as tp
from pathlib import Path

import bpy

from soulstruct.darksouls1r.maps import MSB, get_map
from soulstruct.darksouls1r.maps.navmesh import NavmeshType

from io_soulstruct.utilities import Transform
from io_soulstruct.utilities.materials import hsv_color, create_basic_material


NVM_MESH_TYPING = tuple[list[tp.Sequence[float]], list[tp.Sequence[int]]]

ANY_NVM_NAME_RE = re.compile(r"^(?P<stem>.*)\.nvm(?P<dvx>\.dcx)?$")
STANDARD_NVM_STEM_RE = re.compile(r"^n(\d{4})B(?P<B>\d)A(?P<A>\d{2})$")  # no extensions
NVMBND_NAME_RE = re.compile(r"^.*?\.nvmbnd(\.dcx)?$")


# In descending priority order. All flags can be inspected in custom properties.
NAVMESH_FLAG_COLORS = {
    NavmeshType.Disable: hsv_color(0.0, 0.0, 0.1),  # DARK GREY
    NavmeshType.Degenerate: hsv_color(0.0, 0.0, 0.1),  # DARK GREY
    NavmeshType.Obstacle: hsv_color(0.064, 0.9, 0.2),  # DARK ORANGE
    NavmeshType.MapExit: hsv_color(0.3, 0.9, 1.0),  # LIGHT GREEN
    NavmeshType.Hole: hsv_color(0.066, 0.9, 0.5),  # ORANGE
    NavmeshType.Ladder: hsv_color(0.15, 0.9, 0.5),  # YELLOW
    NavmeshType.ClosedDoor: hsv_color(0.66, 0.9, 0.25),  # DARK BLUE
    NavmeshType.Gate: hsv_color(0.33, 0.9, 0.15),  # DARK GREEN
    NavmeshType.Door: hsv_color(0.66, 0.9, 0.75),  # LIGHT BLUE
    NavmeshType.InsideWall: hsv_color(0.4, 0.9, 0.3),  # TURQUOISE
    NavmeshType.Edge: hsv_color(0.066, 0.9, 0.5),  # ORANGE
    NavmeshType.DropAdjacent: hsv_color(0.0, 0.8, 0.8),  # LIGHT RED
    NavmeshType.LandingPoint: hsv_color(0.4, 0.9, 0.7),  # LIGHT TURQUOISE
    NavmeshType.LargeSpace: hsv_color(0.7, 0.9, 0.7),  # PURPLE
    NavmeshType.Event: hsv_color(0.5, 0.9, 0.5),  # CYAN
    NavmeshType.Drop: hsv_color(0.0, 0.8, 0.1),  # DARK RED
    NavmeshType.Default: hsv_color(0.8, 0.9, 0.5),  # MAGENTA
}
NAVMESH_MULTIPLE_FLAG_COLOR = hsv_color(0.0, 0.0, 1.0)  # WHITE
NAVMESH_UNKNOWN_FLAG_COLOR = hsv_color(0.0, 0.0, 0.25)  # GREY


def get_navmesh_msb_transforms(
    msb_model_name: str, nvm_path: Path, msb: MSB | None = None, msb_path: Path = None
) -> list[tuple[str, Transform]]:
    """Search MSB at `msb_path` (autodetected from `nvm_path.parent` by default) and return
    `(navmesh_name, Transform)` pairs for all Navmesh entries using the `nvm_name` model."""
    if msb is None and msb_path is None:
        nvm_parent_dir = nvm_path.parent
        nvm_map = get_map(nvm_parent_dir.name)
        msb_path = nvm_parent_dir.parent / f"MapStudio/{nvm_map.msb_file_stem}.msb"
    if msb is None:
        if not msb_path.is_file():
            raise FileNotFoundError(f"Cannot find MSB file '{msb_path}'.")
        try:
            msb = MSB.from_path(msb_path)
        except Exception as ex:
            raise RuntimeError(
                f"Cannot open MSB: {ex}.\n"
                f"\nCurrently, only Dark Souls 1 (either version) MSBs are supported."
            )
    elif msb_path is not None:
        raise ValueError("Cannot provide both `msb` and `msb_path`.")
    matches = []
    for navmesh in msb.navmeshes:
        if msb_model_name == navmesh.model.name:
            matches.append(navmesh)
    if not matches:
        raise ValueError(f"Cannot find any MSB Navmesh entries using MSB model '{msb_model_name}'.")
    transforms = [(m.name, Transform.from_msb_entry(m)) for m in matches]
    return transforms


def set_face_material(bl_mesh, bl_face, face_flags: int):
    """Set face materials according to their `NVMTriangle` flags.

    Searches for existing materials on the mesh with names like "Navmesh Flag <flag_name>", and creates them with
    simple diffuse colors if they don't exist in the Blender session yet.

    NOTE: `bl_face` can be from a `Mesh` or `BMesh`. Both have `material_index`.
    """

    # Color face according to its single `flag` if present.
    try:
        flag = NavmeshType(face_flags)
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
