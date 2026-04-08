from __future__ import annotations

__all__ = [
    "MapCollisionProps",
    "MapCollisionImportSettings",
    "MapCollisionToolSettings",
]

import bpy

from ..base.register import io_soulstruct_class, io_soulstruct_pointer_property
from .utilities import HKX_MATERIAL_NAME_RE


@io_soulstruct_class
@io_soulstruct_pointer_property(bpy.types.Object, "COLLISION")
class MapCollisionProps(bpy.types.PropertyGroup):
    """Common map collision properties for Blender objects."""

    # Currently none.
    pass


@io_soulstruct_class
@io_soulstruct_pointer_property(bpy.types.Scene, "map_collision_import_settings")
class MapCollisionImportSettings(bpy.types.PropertyGroup):
    """Common HKX map collision import settings. Drawn manually in operator browser windows."""

    # Currently none.


def _on_lo_alpha_change(self, _):
    for mat in bpy.data.materials:
        match = HKX_MATERIAL_NAME_RE.match(mat.name)
        if not match:
            continue
        if match.groupdict()["res"] == "Lo":
            mat.diffuse_color[3] = self.lo_alpha


def _on_hi_alpha_change(self, _):
    for mat in bpy.data.materials:
        match = HKX_MATERIAL_NAME_RE.match(mat.name)
        if not match:
            continue
        if match.groupdict()["res"] == "Hi":
            mat.diffuse_color[3] = self.hi_alpha


@io_soulstruct_class
@io_soulstruct_pointer_property(bpy.types.Scene, "map_collision_tool_settings")
class MapCollisionToolSettings(bpy.types.PropertyGroup):
    """Common HKX map collision tool settings. Drawn manually in operator browser windows."""

    lo_alpha: bpy.props.FloatProperty(
        name="Lo-Res Alpha",
        description="Viewport color alpha for Lo-Res HKX map collision materials",
        default=0.0,
        min=0.0,
        max=1.0,
        precision=2,
        update=_on_lo_alpha_change,
    )

    hi_alpha: bpy.props.FloatProperty(
        name="Hi-Res Alpha",
        description="Viewport color alpha for Hi-Res HKX map collision materials",
        default=1.0,
        min=0.0,
        max=1.0,
        precision=2,
        update=_on_hi_alpha_change,
    )
