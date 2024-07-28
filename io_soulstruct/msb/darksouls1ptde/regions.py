from __future__ import annotations

__all__ = [
    "BlenderMSBRegion",
]

import bpy
from io_soulstruct.exceptions import MSBRegionImportError, SoulstructTypeError
from io_soulstruct.msb.properties import MSBRegionProps, MSBRegionSubtype, MSBRegionShape
from io_soulstruct.types import *
from io_soulstruct.utilities import Transform, BlenderTransform, LoggingOperator
from soulstruct.darksouls1ptde.maps.regions import *


class BlenderMSBRegion(SoulstructObject[MSBRegion, MSBRegionProps]):
    """Not abstract in DS1."""

    TYPE = SoulstructType.MSB_REGION
    OBJ_DATA_TYPE = SoulstructDataType.EMPTY
    SOULSTRUCT_CLASS = MSBRegion

    data: None  # type override

    @property
    def entity_id(self) -> int:
        return self.type_properties.entity_id

    @entity_id.setter
    def entity_id(self, value: int):
        self.type_properties.entity_id = value

    @property
    def shape(self) -> MSBRegionShape:
        return self.type_properties.shape

    @shape.setter
    def shape(self, value: MSBRegionShape):
        self.type_properties.shape = value

    def set_obj_transform(self, region: MSBRegion):
        game_transform = Transform.from_msb_entry(region)
        self.obj.location = game_transform.bl_translate
        self.obj.rotation_euler = game_transform.bl_rotate
        # We use scale to represent shape dimensions.

    def set_region_transform(self, region: MSBRegion):
        bl_transform = BlenderTransform.from_bl_obj(self.obj)
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
        bl_region = cls.new(name, None, collection)  # type: BlenderMSBRegion

        bl_region.set_obj_transform(soulstruct_obj)
        bl_region.type_properties.region_subtype = MSBRegionSubtype.NA  # no subtypes for DS1
        bl_region.entity_id = soulstruct_obj.entity_id

        # TODO: I want to overhaul all game `MSBRegion` classes to use `RegionShape` components, which will make this a
        #  bit cleaner (rather than relying on subclass name).

        region_type_name = soulstruct_obj.__class__.__name__
        if "Point" in region_type_name:
            soulstruct_obj: MSBRegionPoint
            bl_region.shape = MSBRegionShape.POINT
            bl_region.obj.empty_display_type = "SPHERE"  # best for points
            # No scale needed.
        elif "Sphere" in region_type_name:
            soulstruct_obj: MSBRegionSphere
            bl_region.shape = MSBRegionShape.SPHERE
            bl_region.obj.scale = (soulstruct_obj.radius, soulstruct_obj.radius, soulstruct_obj.radius)
            bl_region.obj.empty_display_type = "SPHERE"  # makes these regions much easier to click
        elif "Cylinder" in region_type_name:
            soulstruct_obj: MSBRegionCylinder
            bl_region.shape = MSBRegionShape.CYLINDER
            bl_region.obj.scale = (soulstruct_obj.radius, soulstruct_obj.radius, soulstruct_obj.height)
            bl_region.obj.empty_display_type = "PLAIN_AXES"  # no great choice for cylinders but this is probably best
        elif "Box" in region_type_name:
            soulstruct_obj: MSBRegionBox
            bl_region.shape = MSBRegionShape.BOX
            bl_region.obj.scale = (soulstruct_obj.width, soulstruct_obj.depth, soulstruct_obj.height)
            # TODO: CUBE vis is wrong, since origin is in center center, not bottom center...
            bl_region.obj.empty_display_type = "CUBE"  # makes these regions much easier to click
        else:
            raise MSBRegionImportError(f"Cannot import MSB region type/shape: {region_type_name}")

        return bl_region

    def create_soulstruct_obj(self) -> MSBRegion:
        if self.shape == MSBRegionShape.POINT:
            return MSBRegionPoint(name=self.name)
        elif self.shape == MSBRegionShape.SPHERE:
            return MSBRegionSphere(name=self.name)
        elif self.shape == MSBRegionShape.CYLINDER:
            return MSBRegionCylinder(name=self.name)
        elif self.shape == MSBRegionShape.BOX:
            return MSBRegionBox(name=self.name)
        raise SoulstructTypeError(f"Unsupported MSB region shape for export: {self.shape}")

    def to_soulstruct_obj(self, operator: LoggingOperator, context: bpy.types.Context) -> MSBRegion:
        region = self.create_soulstruct_obj()
        self.set_region_transform(region)
        region.entity_id = self.entity_id

        # Use shape and scale to set dimensions.
        if isinstance(region, MSBRegionPoint):
            pass  # no dimensions
        elif isinstance(region, MSBRegionSphere):
            if self.obj.scale[0] != self.obj.scale[1] or self.obj.scale[0] != self.obj.scale[2]:
                operator.warning(f"MSB Region Sphere scale is not uniform. Using X: {self.obj.scale[0]}")
            region.radius = self.obj.scale[0]
        elif isinstance(region, MSBRegionCylinder):
            if self.obj.scale[0] != self.obj.scale[1]:
                operator.warning(f"MSB Region Cylinder XY scale is not uniform. Using X: {self.obj.scale[0]}")
            region.radius = self.obj.scale[0]
            region.height = self.obj.scale[2]
        elif isinstance(region, MSBRegionBox):
            region.width = self.obj.scale[0]
            region.depth = self.obj.scale[1]
            region.height = self.obj.scale[2]
        else:
            pass  # won't pass object creation

        return region
