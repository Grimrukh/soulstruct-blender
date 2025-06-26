from __future__ import annotations

__all__ = [
    "BaseBlenderMSBRegion",
]

import typing as tp

import bpy

from soulstruct.base.maps.msb.region_shapes import *
from soulstruct.base.maps.msb.regions import BaseMSBRegion

from soulstruct.blender.exceptions import MSBRegionImportError, SoulstructTypeError
from soulstruct.blender.msb.properties import MSBRegionProps, BlenderMSBRegionSubtype
from soulstruct.blender.msb.types.adapters import *
from soulstruct.blender.msb.utilities import *
from soulstruct.blender.types import *
from soulstruct.blender.utilities import LoggingOperator, find_or_create_collection

from .entry import BaseBlenderMSBEntry, MSB_T


REGION_T = tp.TypeVar("REGION_T", bound=BaseMSBRegion)


class BaseBlenderMSBRegion(BaseBlenderMSBEntry[REGION_T, MSBRegionProps, None, MSB_T]):
    """Identical across early games, before Regions had events merged into them.

    TODO: Currently has no subtype properties, but this will change when later games are supported.
    """

    TYPE = SoulstructType.MSB_REGION
    BL_OBJ_TYPE = ObjectType.MESH
    SOULSTRUCT_CLASS: tp.ClassVar[type[BaseMSBRegion]]  # set by subclasses
    MSB_ENTRY_SUBTYPE: tp.ClassVar[BlenderMSBRegionSubtype]  # set by subclasses

    __slots__ = []
    data: bpy.types.Mesh  # type override

    TYPE_FIELDS = (
        MSBTransformFieldAdapter("translate|rotate"),
        FieldAdapter("entity_id"),
        # NOTE: `shape_type` is a 'class property' in `BaseMSBRegion`, but an instance property in Blender.
    )

    entity_id: int

    @property
    def shape_type(self) -> RegionShapeType:
        return RegionShapeType[self.type_properties.shape_type]

    @shape_type.setter
    def shape_type(self, value: RegionShapeType):
        self.type_properties.shape_type = value.name

    # region Dimensional Properties

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

    # endregion

    @classmethod
    def get_msb_subcollection(cls, msb_collection: bpy.types.Collection, msb_stem: str) -> bpy.types.Collection:
        return find_or_create_collection(msb_collection, f"{msb_stem} Regions")

    @classmethod
    def new_from_shape_type(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        shape_type: RegionShapeType,
        name: str,
        collection: bpy.types.Collection = None,
        **kwargs,
    ) -> tp.Self:
        collection = collection or context.scene.collection
        operator.to_object_mode(context)

        if shape_type == RegionShapeType.Point:
            mesh = bpy.data.meshes.new(name)
            primitive_three_axes(mesh)
            bl_region = cls.new(name, mesh, collection)  # type: tp.Self
            bl_region.shape_type = RegionShapeType.Point
            # Points also have axes enabled.
            bl_region.obj.show_axis = True
        elif shape_type == RegionShapeType.Circle:
            mesh = bpy.data.meshes.new(name)
            primitive_circle(mesh)
            bl_region = cls.new(name, mesh, collection)  # type: tp.Self
            bl_region.shape_type = RegionShapeType.Circle
            bl_region.radius = kwargs.pop("radius", 1.0)
        elif shape_type == RegionShapeType.Sphere:
            mesh = bpy.data.meshes.new(name)
            primitive_cube(mesh)
            bl_region = cls.new(name, mesh, collection)  # type: tp.Self
            bl_region.shape_type = RegionShapeType.Sphere
            bl_region.radius = kwargs.pop("radius", 1.0)
        elif shape_type == RegionShapeType.Cylinder:
            mesh = bpy.data.meshes.new(name)
            primitive_cube(mesh)
            bl_region = cls.new(name, mesh, collection)  # type: tp.Self
            bl_region.shape_type = RegionShapeType.Cylinder
            bl_region.radius = kwargs.pop("radius", 1.0)
            bl_region.height = kwargs.pop("height", 1.0)
        elif shape_type == RegionShapeType.Rect:
            mesh = bpy.data.meshes.new(name)
            primitive_rect(mesh)
            bl_region = cls.new(name, mesh, collection)  # type: tp.Self
            bl_region.shape_type = RegionShapeType.Rect
            bl_region.width = kwargs.pop("width", 1.0)
            bl_region.depth = kwargs.pop("depth", 1.0)
        elif shape_type == RegionShapeType.Box:
            mesh = bpy.data.meshes.new(name)
            primitive_cube(mesh)
            bl_region = cls.new(name, mesh, collection)  # type: tp.Self
            bl_region.shape_type = RegionShapeType.Box
            bl_region.width = kwargs.pop("width", 1.0)
            bl_region.depth = kwargs.pop("depth", 1.0)
            bl_region.height = kwargs.pop("height", 1.0)
        else:
            # TODO: Handle Composite... Depends if the children are used anywhere else. Hard to child them if so.
            raise TypeError(f"Unsupported MSB region shape: {shape_type}")

        if kwargs:
            raise TypeError(f"Invalid dimension arguments for shape type {shape_type}: {kwargs.keys()}")

        bl_region.shape_type = shape_type
        bl_region.type_properties.region_subtype = BlenderMSBRegionSubtype.All  # no subtypes for DS1
        # Other fields (transform, entity ID) left as default.

        # Set viewport display to Wire.
        bl_region.obj.display_type = "WIRE"

        return bl_region

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: REGION_T,
        name: str,
        collection: bpy.types.Collection = None,
    ) -> tp.Self:
        """Creates the appropriate Mesh depending on the region type.

        The user should NOT mess with these meshes, but just control them with Region properties, which in turn drive
        scale (to impact the unit-scale, correctly offset meshes).
        """
        shape = soulstruct_obj.shape
        if isinstance(shape, CompositeShape):
            raise MSBRegionImportError(f"Cannot yet import MSB region shape: {shape.SHAPE_TYPE.name}")

        kwargs = {field: getattr(shape, field) for field in shape.SHAPE_FIELDS}
        bl_region = cls.new_from_shape_type(operator, context, shape.SHAPE_TYPE, name, collection, **kwargs)
        bl_region._read_props_from_soulstruct_obj(operator, context, soulstruct_obj)

        return bl_region

    # noinspection PyArgumentList
    def _create_soulstruct_obj(self) -> REGION_T:
        """Selects Soulstruct shape class automatically from `shape_type` enum."""

        if self.shape_type == RegionShapeType.Composite:
            raise SoulstructTypeError(f"Cannot yet export Composite MSB region shapes.")

        shape_class = self.SOULSTRUCT_CLASS.SHAPE_CLASSES[self.shape_type.value]
        kwargs = {field: getattr(self, field) for field in shape_class.SHAPE_FIELDS}
        shape = shape_class(**kwargs)

        # noinspection PyTypeChecker
        return self.SOULSTRUCT_CLASS(name=self.name, shape=shape)

    @property
    def game_name(self) -> str:
        return get_region_game_name(self.name)
