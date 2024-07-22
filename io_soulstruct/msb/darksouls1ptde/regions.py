from __future__ import annotations

__all__ = [
    "BlenderMSBRegion",
]

import typing as tp

import bpy
from io_soulstruct.exceptions import MSBRegionImportError
from io_soulstruct.utilities import Transform, LoggingOperator
from io_soulstruct.msb.base import BlenderMSBEntry
from io_soulstruct.types import SoulstructType

if tp.TYPE_CHECKING:
    from soulstruct.base.maps.msb.regions import BaseMSBRegion
    from soulstruct.darksouls1ptde.maps.regions import *


class BlenderMSBRegion(BlenderMSBEntry):
    """Not abstract in DS1."""

    @property
    def region_props(self):
        return self.obj.msb_region_props

    def set_transform(self, region: BaseMSBRegion):
        game_transform = Transform.from_msb_entry(region)
        self.obj.location = game_transform.bl_translate
        self.obj.rotation_euler = game_transform.bl_rotate
        # No scale for regions.

    @classmethod
    def new_from_region(
        cls,
        operator: LoggingOperator,
        region: MSBRegion,
        collection: bpy.types.Collection = None,
    ) -> BlenderMSBRegion:

        # Create an Empty representing the region.
        # noinspection PyTypeChecker
        obj = bpy.data.objects.new(region.name, None)
        obj.soulstruct_type = SoulstructType.MSB_REGION
        (collection or bpy.context.scene.collection).objects.link(obj)

        bl_region = cls(obj)
        bl_region.set_transform(region)
        bl_region.set_properties(operator, region)
        return bl_region

    def set_properties(self, operator: LoggingOperator, region: MSBRegion):
        props = self.obj.msb_region_props

        props.entity_id = region.entity_id

        # Set custom properties. This will depend on the shape type.
        # TODO: I want to overhaul all game `MSBRegion` classes to use `RegionShape` components, which will make this a bit
        #  easier (rather than relying on subclass name).
        # TODO: Obviously, it would be nice/smart to use Blender scale for the radius/size of the region. This is only
        #  complicated for Cylinders, really, which need to enforce equal X and Y (radius) but allow different Z (height).
        #  The draw tool can make it clear that only X *or* Y is used for Cylinders though (e.g. whichever is larger).

        region_type_name = region.__class__.__name__
        if "Point" in region_type_name:
            region: MSBRegionPoint
            props.region_shape = "POINT"
            self.obj.empty_display_type = "SPHERE"  # best for points
            # No scale needed.
        elif "Sphere" in region_type_name:
            region: MSBRegionSphere
            props.region_shape = "SPHERE"
            self.obj.scale = (region.radius, region.radius, region.radius)
            self.obj.empty_display_type = "SPHERE"  # makes these regions much easier to click
        elif "Cylinder" in region_type_name:
            region: MSBRegionCylinder
            props.region_shape = "CYLINDER"
            self.obj.scale = (region.radius, region.radius, region.height)
            self.obj.empty_display_type = "PLAIN_AXES"  # no great choice for cylinders but this is probably best
        elif "Box" in region_type_name:
            region: MSBRegionBox
            props.region_shape = "BOX"
            self.obj.scale = (region.width, region.depth, region.height)
            self.obj.empty_display_type = "CUBE"  # makes these regions much easier to click
        else:
            raise MSBRegionImportError(f"Cannot import MSB region type/shape: {region_type_name}")
