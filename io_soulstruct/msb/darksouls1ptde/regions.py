from __future__ import annotations

__all__ = [
    "BlenderMSBRegion",
]

import typing as tp

import bpy

from io_soulstruct.exceptions import MSBRegionImportError, SoulstructTypeError
from io_soulstruct.msb.properties import MSBRegionProps, MSBRegionSubtype
from io_soulstruct.msb.utilities import *
from io_soulstruct.types import *
from io_soulstruct.utilities import Transform, BlenderTransform, LoggingOperator
from soulstruct.darksouls1ptde.maps.regions import *


class BlenderMSBRegion(SoulstructObject[MSBRegion, MSBRegionProps]):
    """Not abstract in DS1."""

    TYPE = SoulstructType.MSB_REGION
    OBJ_DATA_TYPE = SoulstructDataType.MESH
    SOULSTRUCT_CLASS = MSBRegion
    REGION_SUBTYPE = MSBRegionSubtype.All  # no subtypes for DS1

    __slots__ = []
    data: bpy.types.Mesh  # type override

    @property
    def entity_id(self) -> int:
        return self.type_properties.entity_id

    @entity_id.setter
    def entity_id(self, value: int):
        self.type_properties.entity_id = value

    @property
    def shape_type(self) -> RegionShapeType:
        return RegionShapeType[self.type_properties.shape_type]

    @shape_type.setter
    def shape_type(self, value: RegionShapeType):
        self.type_properties.shape_type = value.name

    @property
    def radius(self):
        if self.shape_type not in {RegionShapeType.Sphere, RegionShapeType.Circle, RegionShapeType.Cylinder}:
            raise TypeError(f"Region shape {self.shape_type} does not have a radius.")
        return self.type_properties.shape_x

    @radius.setter
    def radius(self, value):
        if self.shape_type not in {RegionShapeType.Sphere, RegionShapeType.Circle, RegionShapeType.Cylinder}:
            raise TypeError(f"Region shape {self.shape_type} does not have a radius.")
        self.type_properties.shape_x = value

    @property
    def width(self):
        if self.shape_type not in {RegionShapeType.Rect, RegionShapeType.Box}:
            raise TypeError(f"Region shape {self.shape_type} does not have a width.")
        return self.type_properties.shape_x

    @width.setter
    def width(self, value):
        if self.shape_type not in {RegionShapeType.Rect, RegionShapeType.Box}:
            raise TypeError(f"Region shape {self.shape_type} does not have a width.")
        self.type_properties.shape_x = value

    @property
    def depth(self):
        if self.shape_type not in {RegionShapeType.Rect, RegionShapeType.Box}:
            raise TypeError(f"Region shape {self.shape_type} does not have a depth.")
        return self.type_properties.shape_y

    @depth.setter
    def depth(self, value):
        if self.shape_type not in {RegionShapeType.Rect, RegionShapeType.Box}:
            raise TypeError(f"Region shape {self.shape_type} does not have a depth.")
        self.type_properties.shape_y = value

    @property
    def height(self):
        if self.shape_type not in {RegionShapeType.Cylinder, RegionShapeType.Box}:
            raise TypeError(f"Region shape {self.shape_type} does not have a height.")
        return self.type_properties.shape_z

    @height.setter
    def height(self, value):
        if self.shape_type not in {RegionShapeType.Cylinder, RegionShapeType.Box}:
            raise TypeError(f"Region shape {self.shape_type} does not have a height.")
        self.type_properties.shape_z = value

    def set_obj_transform(self, region: MSBRegion):
        game_transform = Transform.from_msb_entry(region)
        self.obj.location = game_transform.bl_translate
        self.obj.rotation_euler = game_transform.bl_rotate
        # We use scale to represent shape dimensions.

    def set_region_transform(self, region: MSBRegion, use_world_transform=False):
        bl_transform = BlenderTransform.from_bl_obj(self.obj, use_world_transform)
        region.translate = bl_transform.game_translate
        region.rotate = bl_transform.game_rotate_deg
        # We use scale to represent shape dimensions.

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MSBRegion,
        name: str,
        collection: bpy.types.Collection = None,
    ) -> BlenderMSBRegion:
        """Creates the appropriate Mesh depending on the region type.

        The user should NOT mess with these meshes, but just control them with Region properties, which in turn drive
        scale (to impact the unit-scale, correctly offset meshes).
        """
        collection = collection or context.scene.collection
        operator.to_object_mode()

        if isinstance(soulstruct_obj.shape, PointShape):
            # Create a new tiny cube Mesh object to represent a Point. Manual GUI handles better drawing, since I don't
            # like any of Blender's Empty display modes for this, but still want something easily clickable.
            mesh = bpy.data.meshes.new(name)
            primitive_three_axes(mesh)
            bl_region = cls.new(name, mesh, collection)  # type: tp.Self
            bl_region.shape_type = RegionShapeType.Point
            # Points also have axes enabled.
            bl_region.obj.show_axis = True
        elif isinstance(soulstruct_obj.shape, CircleShape):
            mesh = bpy.data.meshes.new(name)
            primitive_circle(mesh)
            bl_region = cls.new(name, mesh, collection)  # type: tp.Self
            bl_region.shape_type = RegionShapeType.Circle
            bl_region.radius = soulstruct_obj.shape.radius
        elif isinstance(soulstruct_obj.shape, SphereShape):
            mesh = bpy.data.meshes.new(name)
            primitive_cube(mesh)
            bl_region = cls.new(name, mesh, collection)  # type: tp.Self
            bl_region.shape_type = RegionShapeType.Sphere
            bl_region.radius = soulstruct_obj.shape.radius
        elif isinstance(soulstruct_obj.shape, CylinderShape):
            mesh = bpy.data.meshes.new(name)
            primitive_cube(mesh)
            bl_region = cls.new(name, mesh, collection)  # type: tp.Self
            bl_region.shape_type = RegionShapeType.Cylinder
            bl_region.radius = soulstruct_obj.shape.radius
            bl_region.height = soulstruct_obj.shape.height
        elif isinstance(soulstruct_obj.shape, RectShape):
            mesh = bpy.data.meshes.new(name)
            primitive_rect(mesh)
            bl_region = cls.new(name, mesh, collection)  # type: tp.Self
            bl_region.shape_type = RegionShapeType.Rect
            bl_region.width = soulstruct_obj.shape.width
            bl_region.depth = soulstruct_obj.shape.depth
        elif isinstance(soulstruct_obj.shape, BoxShape):
            mesh = bpy.data.meshes.new(name)
            primitive_cube(mesh)
            bl_region = cls.new(name, mesh, collection)  # type: tp.Self
            bl_region.shape_type = RegionShapeType.Box
            bl_region.width = soulstruct_obj.shape.width
            bl_region.depth = soulstruct_obj.shape.depth
            bl_region.height = soulstruct_obj.shape.height
        else:
            # TODO: Handle Composite... Depends if the children are used anywhere else.
            raise MSBRegionImportError(f"Cannot yet import MSB region shape: {soulstruct_obj.shape_type}")

        # Set viewport display to Wire.
        bl_region.obj.display_type = "WIRE"

        bl_region.set_obj_transform(soulstruct_obj)
        bl_region.type_properties.region_subtype = MSBRegionSubtype.All  # no subtypes for DS1
        bl_region.entity_id = soulstruct_obj.entity_id

        return bl_region

    # noinspection PyArgumentList
    def _create_soulstruct_obj(self) -> MSBRegion:
        shape_class = MSBRegion.SHAPE_CLASSES[self.shape_type.value]
        match self.shape_type.value:
            case RegionShapeType.Point:
                shape = shape_class()
            case RegionShapeType.Circle:
                shape = shape_class(radius=self.radius)
            case RegionShapeType.Sphere:
                shape = shape_class(radius=self.radius)
            case RegionShapeType.Cylinder:
                shape = shape_class(radius=self.radius, height=self.height)
            case RegionShapeType.Rect:
                shape = shape_class(width=self.width, depth=self.depth)
            case RegionShapeType.Box:
                shape = shape_class(width=self.width, depth=self.depth, height=self.height)
            case _:
                # TODO: Composite.
                raise SoulstructTypeError(f"Unsupported MSB region shape for export: {self.shape_type}")
        return MSBRegion(name=self.name, shape=shape)

    def to_soulstruct_obj(self, operator: LoggingOperator, context: bpy.types.Context) -> MSBRegion:
        region = self._create_soulstruct_obj()
        use_world_transform = context.scene.msb_export_settings.use_world_transforms
        self.set_region_transform(region, use_world_transform=use_world_transform)
        region.entity_id = self.entity_id
        return region
