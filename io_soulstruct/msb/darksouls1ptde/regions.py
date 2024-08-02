from __future__ import annotations

__all__ = [
    "BlenderMSBRegion",
]

import bpy
from io_soulstruct.exceptions import MSBRegionImportError, SoulstructTypeError
from io_soulstruct.msb.properties import MSBRegionProps, MSBRegionSubtype
from io_soulstruct.types import *
from io_soulstruct.utilities import Transform, BlenderTransform, LoggingOperator
from soulstruct.darksouls1ptde.maps.regions import *


class BlenderMSBRegion(SoulstructObject[MSBRegion, MSBRegionProps]):
    """Not abstract in DS1."""

    TYPE = SoulstructType.MSB_REGION
    OBJ_DATA_TYPE = SoulstructDataType.MESH
    SOULSTRUCT_CLASS = MSBRegion

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
        """Creates the appropriate Mesh depending on the region type.

        The user should NOT mess with these meshes, but just control them with Region properties, which in turn drive
        scale (to impact the unit-scale, correctly offset meshes).
        """
        collection = collection or context.scene.collection
        operator.to_object_mode()

        if isinstance(soulstruct_obj.shape, PointShape):
            # Create a new tiny cube Mesh object to represent an Empty.
            mesh = cls.create_cube(name, width=0.2)
            bl_region = cls.new(name, mesh, collection)  # type: BlenderMSBRegion
        elif isinstance(soulstruct_obj.shape, CircleShape):
            bpy.ops.mesh.primitive_circle_add(radius=1, location=(0, 0, 0))
            bl_region = cls.from_primitive_obj(context, name, collection)

            bl_region.shape_type = RegionShapeType.Circle
            bl_region.radius = soulstruct_obj.shape.radius
            # Drive X and Y scale from radius. Z scale is irrelevant.
            bl_region.create_scale_driver("shape_x", 0)
            bl_region.create_scale_driver("shape_x", 1)
        elif isinstance(soulstruct_obj.shape, SphereShape):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
            bl_region = cls.from_primitive_obj(context, name, collection)

            bl_region.shape_type = RegionShapeType.Sphere
            bl_region.radius = soulstruct_obj.shape.radius
            # Drive X, Y, and Z scale from radius.
            bl_region.create_scale_driver("shape_x", 0)
            bl_region.create_scale_driver("shape_x", 1)
            bl_region.create_scale_driver("shape_x", 2)
        elif isinstance(soulstruct_obj.shape, CylinderShape):
            bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=1, location=(0, 0, 0))
            bl_region = cls.from_primitive_obj(context, name, collection)
            # Cylinder origin is in center of bottom face, so move up by half height.
            mesh_data = bl_region.data
            for v in mesh_data.vertices:
                v.co[2] += 0.5
            bl_region.shape_type = RegionShapeType.Cylinder
            bl_region.radius = soulstruct_obj.shape.radius
            bl_region.height = soulstruct_obj.shape.height
            # Drive X and Y scale from radius, Z scale from height.
            bl_region.create_scale_driver("shape_x", 0)
            bl_region.create_scale_driver("shape_x", 1)
            bl_region.create_scale_driver("shape_z", 2)
        elif isinstance(soulstruct_obj.shape, RectShape):
            bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
            bl_region = cls.from_primitive_obj(context, name, collection)

            bl_region.shape_type = RegionShapeType.Rect
            bl_region.width = soulstruct_obj.shape.width
            bl_region.depth = soulstruct_obj.shape.depth
            # Drive X and Y scale from width and depth. Z scale is irrelevant.
            bl_region.create_scale_driver("shape_x", 0)
            bl_region.create_scale_driver("shape_y", 1)
        elif isinstance(soulstruct_obj.shape, BoxShape):
            mesh = cls.create_cube(name, width=1)
            bl_region = cls.new(name, mesh, collection)  # type: BlenderMSBRegion
            bl_region.shape_type = RegionShapeType.Box
            bl_region.width = soulstruct_obj.shape.width
            bl_region.depth = soulstruct_obj.shape.depth
            bl_region.height = soulstruct_obj.shape.height
            # Drive all three scale dimensions.
            bl_region.create_scale_driver("shape_x", 0)
            bl_region.create_scale_driver("shape_y", 1)
            bl_region.create_scale_driver("shape_z", 2)
        else:
            # TODO: Handle 2D shapes at least. Composite... Depends if the children are used anywhere else.
            raise MSBRegionImportError(f"Cannot yet import MSB region shape: {soulstruct_obj.shape_type}")

        if soulstruct_obj.shape_type != RegionShapeType.Point:
            # Set viewport display to Wire.
            bl_region.obj.display_type = "WIRE"

        bl_region.set_obj_transform(soulstruct_obj)
        bl_region.type_properties.region_subtype = MSBRegionSubtype.ALL  # no subtypes for DS1
        bl_region.entity_id = soulstruct_obj.entity_id

        return bl_region

    @classmethod
    def from_primitive_obj(
        cls, context: bpy.types.Context, name: str, collection: bpy.types.Collection
    ) -> BlenderMSBRegion:
        obj = context.object
        obj.name = obj.data.name = name
        obj.soulstruct_type = cls.TYPE
        for default_col in obj.users_collection:
            default_col.objects.unlink(obj)
        collection.objects.link(obj)
        return cls(obj)

    # noinspection PyArgumentList
    def create_soulstruct_obj(self) -> MSBRegion:
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
        region = self.create_soulstruct_obj()
        self.set_region_transform(region)
        region.entity_id = self.entity_id
        return region

    def create_scale_driver(self, prop_name: str, target_index: int):
        driver = self.obj.driver_add("scale", target_index).driver
        driver.type = "SCRIPTED"
        driver.expression = "uniform_scale"
        var = driver.variables.new()
        var.name = "uniform_scale"
        var.type = "SINGLE_PROP"
        var.targets[0].id_type = "OBJECT"
        var.targets[0].id = self.obj
        var.targets[0].data_path = f"MSB_REGION.{prop_name}"

    @staticmethod
    def create_cube(name: str, width: float) -> bpy.types.Mesh:
        """Create a new cube with edge lengths `width` that is offset upward by half its height, as in-game."""
        mesh = bpy.data.meshes.new(name)

        half_width = width / 2
        vertices = [
            (-half_width, -half_width, 0),
            (-half_width, half_width, 0),
            (half_width, half_width, 0),
            (half_width, -half_width, 0),
            (-half_width, -half_width, width),
            (-half_width, half_width, width),
            (half_width, half_width, width),
            (half_width, -half_width, width),
        ]
        faces = [
            (0, 1, 2, 3),
            (4, 5, 6, 7),
            (0, 1, 5, 4),
            (2, 3, 7, 6),
            (0, 3, 7, 4),
            (1, 2, 6, 5),
        ]
        mesh.from_pydata(vertices, [], faces)

        mesh.update()
        return mesh
