from __future__ import annotations

__all__ = [
    "BlenderMSBRegion",
]

import typing as tp

import bpy
from io_soulstruct import SoulstructSettings
from io_soulstruct.exceptions import MSBRegionImportError, SoulstructTypeError
from io_soulstruct.utilities import Transform, BlenderTransform, LoggingOperator
from io_soulstruct.msb.base import BlenderMSBEntry, ENTRY_TYPE
from io_soulstruct.msb.properties import MSBRegionSubtype, MSBRegionShape
from io_soulstruct.types import SoulstructType

if tp.TYPE_CHECKING:
    from soulstruct.darksouls1ptde.maps.msb import MSB
    from soulstruct.darksouls1ptde.maps.regions import *


class BlenderMSBRegion(BlenderMSBEntry[MSBRegion]):
    """Not abstract in DS1."""

    @property
    def region_props(self):
        return self.obj.msb_region_props

    def set_obj_transform(self, region: MSBRegion):
        game_transform = Transform.from_msb_entry(region)
        self.obj.location = game_transform.bl_translate
        self.obj.rotation_euler = game_transform.bl_rotate
        # No scale for regions.

    def set_region_transform(self, region: MSBRegion):
        bl_transform = BlenderTransform.from_bl_obj(self.obj)
        region.translate = bl_transform.game_translate
        region.rotate = bl_transform.game_rotate_deg
        # No scale for regions.

    def assert_obj_region_subtype(self, subtype: MSBRegionSubtype):
        if self.region_props.region_subtype != subtype:
            raise SoulstructTypeError(
                f"Blender object '{self.name}' has MSB Region subtype '{self.region_props.region_subtype}', not "
                f"'{subtype}'."
            )

    def set_obj_properties(self, operator: LoggingOperator, entry: MSBRegion):
        props = self.obj.msb_region_props

        props.entity_id = entry.entity_id

        # Set custom properties. This will depend on the shape type.
        # TODO: I want to overhaul all game `MSBRegion` classes to use `RegionShape` components, which will make this a bit
        #  easier (rather than relying on subclass name).
        # TODO: Obviously, it would be nice/smart to use Blender scale for the radius/size of the region. This is only
        #  complicated for Cylinders, really, which need to enforce equal X and Y (radius) but allow different Z (height).
        #  The draw tool can make it clear that only X *or* Y is used for Cylinders though (e.g. whichever is larger).

        region_type_name = entry.__class__.__name__
        if "Point" in region_type_name:
            entry: MSBRegionPoint
            props.region_shape = MSBRegionShape.POINT
            self.obj.empty_display_type = "SPHERE"  # best for points
            # No scale needed.
        elif "Sphere" in region_type_name:
            entry: MSBRegionSphere
            props.region_shape = MSBRegionShape.SPHERE
            self.obj.scale = (entry.radius, entry.radius, entry.radius)
            self.obj.empty_display_type = "SPHERE"  # makes these regions much easier to click
        elif "Cylinder" in region_type_name:
            entry: MSBRegionCylinder
            props.region_shape = MSBRegionShape.CYLINDER
            self.obj.scale = (entry.radius, entry.radius, entry.height)
            self.obj.empty_display_type = "PLAIN_AXES"  # no great choice for cylinders but this is probably best
        elif "Box" in region_type_name:
            entry: MSBRegionBox
            props.region_shape = MSBRegionShape.BOX
            self.obj.scale = (entry.width, entry.depth, entry.height)
            self.obj.empty_display_type = "CUBE"  # makes these regions much easier to click
        else:
            raise MSBRegionImportError(f"Cannot import MSB region type/shape: {region_type_name}")

    @classmethod
    def new_from_entry(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        settings: SoulstructSettings,
        map_stem: str,
        entry: MSBRegion,
        collection: bpy.types.Collection = None,
    ) -> BlenderMSBRegion:
        # Create an Empty representing the region.
        obj = bpy.data.objects.new(entry.name, None)
        obj.soulstruct_type = SoulstructType.MSB_REGION
        (collection or bpy.context.scene.collection).objects.link(obj)

        bl_region = cls(obj)
        bl_region.set_obj_transform(entry)
        bl_region.set_obj_properties(operator, entry)
        return bl_region

    def to_entry(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        settings: SoulstructSettings,
        map_stem: str,
        msb: MSB,
    ) -> ENTRY_TYPE:
        entry = super().to_entry(operator, context, settings, map_stem, msb)
        self.set_region_transform(entry)
        return entry
