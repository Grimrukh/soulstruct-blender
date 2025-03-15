"""Property groups for all MSB subtypes in all games.

These groups are added as extension RNA properties of `bpy.types.Object` upon add-on registration.

Note that all games for all properties are POOLED here. The add-on's panels will selectively display only the properties
that are supported by the current game. The alternative -- a different property group for each game -- would be a mess
and would make it very hard to port entries between games, which is a core goal of Soulstruct for Blender.

In cases where properties conflict between games (e.g. they are extended or the enum changes), then per-game versions of
that property will be defined in the group, and `update` callbacks will be used to synchronize them where possible to
aid porting.
"""
from __future__ import annotations

__all__ = [
    "MSBRegionSubtype",
    "MSBRegionProps",
]

from enum import StrEnum

import bpy

from soulstruct.base.maps.msb.region_shapes import RegionShapeType

from io_soulstruct.msb.utilities import *
from io_soulstruct.utilities import ObjectType


class MSBRegionSubtype(StrEnum):
    """Union of Region subtypes across all games."""
    All = "ALL"  # for games with no real subtypes (DS1, BB, ...)


class MSBRegionProps(bpy.types.PropertyGroup):
    entity_id: bpy.props.IntProperty(
        name="Entity ID",
        default=-1
    )

    region_subtype: bpy.props.EnumProperty(
        name="Region Subtype",
        description="MSB subtype (shape) of this Region object",
        items=[
            ("NONE", "None", "Not an MSB Region"),
            (MSBRegionSubtype.All, "All", "Older game with no region subtypes (only shapes)"),
            # TODO: ER subtypes...
        ],
        default="NONE",
    )

    @property
    def region_subtype_enum(self):
        if self.region_subtype == "NONE":
            raise ValueError("MSB Region subtype is not set.")
        return MSBRegionSubtype(self.region_subtype)

    shape_type: bpy.props.EnumProperty(
        name="Shape",
        description="Shape of this Region object. Object's mesh will update automatically when changed and shape "
                    "dimension properties will be applied to object scale",
        items=[
            (RegionShapeType.Point.value, "Point", "Point with location and rotation only"),
            (RegionShapeType.Circle.value, "Circle", "2D circle with radius (-> X/Y scale). Unused"),
            (RegionShapeType.Sphere.value, "Sphere", "Volume with radius only (-> X/Y/Z scale)"),
            (RegionShapeType.Cylinder.value, "Cylinder", "Volume with radius (-> X/Y scale) and height (-> Z scale)"),
            (RegionShapeType.Rect.value, "Rect", "2D rectangle with width (X) and depth (Y). Unused"),
            (RegionShapeType.Box.value, "Box", "Volume with width (X), depth (Y), and height (Z)"),
        ],
        default=RegionShapeType.Point.name,
        update=lambda self, context: self._auto_shape_mesh(context),
    )

    @property
    def shape_type_enum(self) -> RegionShapeType:
        # noinspection PyTypeChecker
        return RegionShapeType[self.shape_type]

    # Three shape fields that are exposed differently depending on `shape` type. These are used to drive object scale.
    # Note that these are in Blender coordinates, so Z is height here, rather than Y (as in MSB).
    shape_x: bpy.props.FloatProperty(
        name="Shape X",
        description="X dimension of region shape (sphere/cylinder/circle radius or box/rect width)",
        default=1.0,
    )
    shape_y: bpy.props.FloatProperty(
        name="Shape Y",
        description="Y dimension of region shape (box/rect depth)",
        default=1.0,
    )
    shape_z: bpy.props.FloatProperty(
        name="Shape Z",
        description="Z dimension of region shape (cylinder/box height)",
        default=1.0,
    )

    def _auto_shape_mesh(self, _):
        """Fully replace mesh when a new shape is selected."""
        shape = RegionShapeType[self.shape_type]
        obj = self.id_data  # type: bpy.types.MeshObject
        if obj.type != ObjectType.Mesh:
            return  # unsupported region object
        mesh = obj.data  # type: bpy.types.Mesh
        # Clear scale drivers. New ones will be created as appropriate.
        for i in range(3):
            obj.driver_remove("scale", i)

        # NOTE: We don't change `obj.show_axis` here. It's enabled by default for Points on import, but is up to
        # the player to enable/disable after that.

        if shape == RegionShapeType.Point:
            primitive_three_axes(mesh)
            # No drivers.
        elif shape == RegionShapeType.Circle:
            primitive_circle(mesh)
            create_region_scale_driver(obj, "xx")
        elif shape == RegionShapeType.Sphere:
            primitive_sphere(mesh)
            create_region_scale_driver(obj, "xxx")
        elif shape == RegionShapeType.Cylinder:
            primitive_cylinder(mesh)
            create_region_scale_driver(obj, "xxz")
        elif shape == RegionShapeType.Rect:
            primitive_rect(mesh)
            create_region_scale_driver(obj, "xy")
        elif shape == RegionShapeType.Box:
            primitive_cube(mesh)
            create_region_scale_driver(obj, "xyz")
        else:
            # TODO: Handle Composite.
            pass
