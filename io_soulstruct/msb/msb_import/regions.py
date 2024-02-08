"""Import MSB Regions of any shape as Blender Empty objects, with custom shape properties and a custom draw tool.

Much simpler than MSB Part import, obviously, aside from the custom draw logic.
"""
from __future__ import annotations

__all__ = [
    "RegionImportError",
    "ImportMSBPoint",
    "ImportMSBVolume",
    "ImportAllMSBPoints",
    "ImportAllMSBVolumes",
    "RegionDrawSettings",
    "draw_regions",
]

import math
import time
import traceback
import typing as tp

import numpy as np

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix

from io_soulstruct.general.cached import get_cached_file
from io_soulstruct.utilities import *
from io_soulstruct.utilities.conversion import Transform
from io_soulstruct.utilities.operators import LoggingOperator

if tp.TYPE_CHECKING:
    from soulstruct.darksouls1r.maps.regions import *  # TODO: use multi-game typing
    from io_soulstruct.type_checking import MSB_TYPING
    from .settings import *


if bpy.app.version[0] == 4:
    UNIFORM_COLOR_SHADER = "UNIFORM_COLOR"
else:
    UNIFORM_COLOR_SHADER = "3D_UNIFORM_COLOR"


class RegionImportError(Exception):
    pass


def create_region_empty(msb_region: MSBRegion) -> bpy.types.Object:

    # Create an Empty representing the region.
    region = bpy.data.objects.new(msb_region.name, None)

    transform = Transform.from_msb_entry(msb_region)
    region.location = transform.bl_translate
    region.rotation_euler = transform.bl_rotate
    # No scale for regions.
    region["Entity ID"] = msb_region.entity_id

    # Set custom properties. This will depend on the shape type.
    # TODO: I want to overhaul all game `MSBRegion` classes to use `RegionShape` components, which will make this a bit
    #  easier (rather than relying on subclass name).
    # TODO: Obviously, it would be nice/smart to use Blender scale for the radius/size of the region. This is only
    #  complicated for Cylinders, really, which need to enforce equal X and Y (radius) but allow different Z (height).
    #  The draw tool can make it clear that only X *or* Y is used for Cylinders though (e.g. whichever is larger).
    # TODO: Create an EnumProperty for custom Region Type property?
    region_type_name = msb_region.__class__.__name__
    if "Point" in region_type_name:
        msb_region: MSBRegionPoint
        region["Region Shape"] = "Point"
        region.empty_display_type = "SPHERE"  # best for points
        # No scale needed.
    elif "Sphere" in region_type_name:
        msb_region: MSBRegionSphere
        region["Region Shape"] = "Sphere"
        region.scale = (msb_region.radius, msb_region.radius, msb_region.radius)
        region.empty_display_type = "SPHERE"  # makes these regions much easier to click
    elif "Cylinder" in region_type_name:
        msb_region: MSBRegionCylinder
        region["Region Shape"] = "Cylinder"
        region.scale = (msb_region.radius, msb_region.radius, msb_region.height)
        region.empty_display_type = "PLAIN_AXES"  # no great choice for cylinders but this is probably best
    elif "Box" in region_type_name:
        msb_region: MSBRegionBox
        region["Region Shape"] = "Box"
        region.scale = (msb_region.width, msb_region.depth, msb_region.height)
        region.empty_display_type = "CUBE"  # makes these regions much easier to click
    else:
        raise RegionImportError(f"Cannot import MSB region type/shape: {region_type_name}")

    return region


class BaseImportMSBRegion(LoggingOperator):

    REGION_TYPE_NAME: str  # e.g. 'Volume'
    REGION_TYPE_NAME_PLURAL: str  # e.g. 'Volumes'
    MSB_LIST_NAMES: list[str]  # e.g. ['spheres', 'cylinders', 'boxes']
    GAME_ENUM_NAME: str | None  # e.g. 'point_region' or 'volume_region' or `None` for all-region importers

    @classmethod
    def poll(cls, context):
        settings = cls.settings(context)
        msb_path = settings.get_import_msb_path()
        if not is_path_and_file(msb_path):
            return False
        if cls.GAME_ENUM_NAME is not None:
            region = getattr(context.scene.soulstruct_game_enums, cls.GAME_ENUM_NAME)
            if region in {"", "0"}:
                return False  # no enum option selected
        return True  # MSB exists and a region name is selected from enum

    def import_enum_region(self, context):

        region_name = getattr(context.scene.soulstruct_game_enums, self.GAME_ENUM_NAME)
        if region_name in {"", "0"}:
            return self.error(f"Invalid MSB {self.REGION_TYPE_NAME} selection: {region_name}")

        settings = self.settings(context)
        settings.save_settings()
        msb_import_settings = context.scene.msb_import_settings  # type: MSBImportSettings

        if not settings.get_import_map_path():  # validation
            return self.error("Game directory and map stem must be set in Blender's Soulstruct global settings.")

        # We always use the latest MSB, if the setting is enabled.
        msb_stem = settings.get_latest_map_stem_version()
        msb_path = settings.get_import_msb_path()  # will automatically use latest MSB version if known and enabled
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING
        collection_name = msb_import_settings.get_collection_name(msb_stem, self.REGION_TYPE_NAME_PLURAL)
        region_collection = get_collection(collection_name, context.scene.collection)

        # Get MSB region.
        region_list = getattr(msb, self.MSB_LIST_NAMES[0])
        try:
            region = region_list.find_entry_name(region_name)
        except KeyError:
            return self.error(f"MSB {self.REGION_TYPE_NAME} '{region_name}' not found in MSB.")

        try:
            # NOTE: Instance creator may not always use `map_stem` (e.g. characters).
            region_empty = create_region_empty(region)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Failed to import MSB {self.REGION_TYPE_NAME} region '{region.name}': {ex}")
        region_collection.objects.link(region_empty)

        # Select and frame view on new instance.
        self.set_active_obj(region_empty)
        bpy.ops.view3d.view_selected(use_all_regions=False)

        return {"FINISHED"}

    def import_all_regions(self, context):

        start_time = time.perf_counter()

        settings = self.settings(context)
        settings.save_settings()

        if not settings.get_import_map_path():  # validation
            return self.error("Game directory and map stem must be set in Blender's Soulstruct global settings.")

        msb_import_settings = context.scene.msb_import_settings  # type: MSBImportSettings
        is_name_match = msb_import_settings.get_name_match_filter()
        msb_stem = settings.get_latest_map_stem_version()
        msb_path = settings.get_import_msb_path()  # will automatically use latest MSB version if known and enabled
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING
        collection_name = msb_import_settings.get_collection_name(msb_stem, self.REGION_TYPE_NAME_PLURAL)
        region_collection = get_collection(collection_name, context.scene.collection)

        combined_region_list = []
        for region_list in [getattr(msb, name) for name in self.MSB_LIST_NAMES]:
            combined_region_list.extend(region_list)
        region_count = 0

        for region in [region for region in combined_region_list if is_name_match(region.name)]:
            try:
                region_empty = create_region_empty(region)
            except Exception as ex:
                traceback.print_exc()
                self.error(f"Failed to import MSB {self.REGION_TYPE_NAME} region '{region.name}': {ex}")
                continue
            region_collection.objects.link(region_empty)
            region_count += 1

        if region_count == 0:
            self.warning(
                f"No MSB {self.REGION_TYPE_NAME} regions found with {msb_import_settings.entry_name_match_mode} filter: "
                f"'{msb_import_settings.entry_name_match}'"
            )
            return {"CANCELLED"}

        self.info(
            f"Imported {region_count} / {len(combined_region_list)} MSB {self.REGION_TYPE_NAME} regions in "
            f"{time.perf_counter() - start_time:.3f} seconds (filter: '{msb_import_settings.entry_name_match}')."
        )

        # No change in view after importing all regions.

        return {"FINISHED"}


class ImportMSBPoint(BaseImportMSBRegion):
    bl_idname = "import_scene.msb_point_region"
    bl_label = "Import Point Region"
    bl_description = "Import MSB transform of selected MSB Point region"

    REGION_TYPE_NAME = "Point"
    REGION_TYPE_NAME_PLURAL = "Points"
    MSB_LIST_NAMES = ["points"]
    GAME_ENUM_NAME = "point_region"

    def execute(self, context):
        return self.import_enum_region(context)


class ImportMSBVolume(BaseImportMSBRegion):
    bl_idname = "import_scene.msb_volume_region"
    bl_label = "Import Volume Region"
    bl_description = "Import MSB transform and shape of selected MSB Volume region"

    REGION_TYPE_NAME = "Volume"
    REGION_TYPE_NAME_PLURAL = "Volumes"
    MSB_LIST_NAMES = ["spheres", "cylinders", "boxes"]
    GAME_ENUM_NAME = "volume_region"

    def execute(self, context):
        return self.import_enum_region(context)


class ImportAllMSBPoints(BaseImportMSBRegion):
    bl_idname = "import_scene.all_msb_point_regions"
    bl_label = "Import All Point Regions"
    bl_description = "Import MSB transform of every MSB Point region"

    REGION_TYPE_NAME = "Point"
    REGION_TYPE_NAME_PLURAL = "Points"
    MSB_LIST_NAMES = ["points"]
    GAME_ENUM_NAME = None

    def execute(self, context):
        return self.import_all_regions(context)


class ImportAllMSBVolumes(BaseImportMSBRegion):
    bl_idname = "import_scene.all_msb_volume_regions"
    bl_label = "Import All Volume Regions"
    bl_description = "Import MSB transform and shape of every MSB Volume region"

    REGION_TYPE_NAME = "Volume"
    REGION_TYPE_NAME_PLURAL = "Volumes"
    MSB_LIST_NAMES = ["spheres", "cylinders", "boxes"]
    GAME_ENUM_NAME = None

    def execute(self, context):
        return self.import_all_regions(context)


class RegionDrawSettings(bpy.types.PropertyGroup):

    draw_mode: bpy.props.EnumProperty(
        name="Draw Mode",
        description="When to draw MSB regions in the 3D view",
        items=[
            ("ACTIVE_COLLECTION", "Active Collection", "Draw all MSB regions in the active collection"),
            ("SELECTED", "Selected", "Draw only the selected MSB region"),
            ("MAP", "Map", "Draw all MSB regions in collection named '{map} Volumes'"),
            ("ALL", "All", "Draw all MSB regions in the scene"),
            ("NONE", "None", "Do not draw any MSB regions"),
        ],
        default="ACTIVE_COLLECTION",
    )

    draw_spheres: bpy.props.BoolProperty(
        name="Draw Spheres",
        description="Draw MSB Sphere regions",
        default=True,
    )

    draw_cylinders: bpy.props.BoolProperty(
        name="Draw Cylinders",
        description="Draw MSB Cylinder regions",
        default=True,
    )

    draw_boxes: bpy.props.BoolProperty(
        name="Draw Boxes",
        description="Draw MSB Box regions",
        default=True,
    )

    region_color: bpy.props.FloatVectorProperty(
        name="Region Color",
        description="Color of drawn MSB regions",
        subtype="COLOR",
        default=(1.0, 0.0, 0.0),
        min=0.0,
        max=1.0,
    )

    use_rgb_spheres: bpy.props.BoolProperty(
        name="Use RGB Spheres",
        description="Use RGB colors for MSB Sphere regions",
        default=False,
    )

    line_width: bpy.props.FloatProperty(
        name="Line Width",
        description="Width of lines used to draw MSB regions",
        default=1.0,
        min=0.1,
        max=10.0,
    )


UNIT_CIRCLE_32 = [
    [math.cos(angle), math.sin(angle), 0]
    for angle in np.linspace(0, 2 * math.pi, 32)
]
UNIT_CIRCLE_32_TOP = [
    [math.cos(angle), math.sin(angle), 1]
    for angle in np.linspace(0, 2 * math.pi, 32)
]
CIRCLE_Z_MAT = Matrix()
CIRCLE_Y_MAT = Matrix.Rotation(math.radians(90.0), 4, 'X')
CIRCLE_X_MAT = Matrix.Rotation(math.radians(90.0), 4, 'Y')
SHADER = gpu.shader.from_builtin(UNIFORM_COLOR_SHADER)
CIRCLE_BATCH = batch_for_shader(SHADER, "LINE_LOOP", {'pos': UNIT_CIRCLE_32})
CIRCLE_TOP_BATCH = batch_for_shader(SHADER, "LINE_LOOP", {'pos': UNIT_CIRCLE_32_TOP})

CYLINDER_VERTICES = [
    (1, 0, 0), (1, 0, 1),
    (-1, 0, 0), (-1, 0, 1),
    (0, 1, 0), (0, 1, 1),
    (0, -1, 0), (0, -1, 1),
]
CYLINDER_BATCH = batch_for_shader(SHADER, "LINES", {'pos': CYLINDER_VERTICES})

CUBE_VERTICES = np.array([
    (x, y, z)
    for x in (-1, 1)
    for y in (-1, 1)
    for z in (-1, 1)
])
CUBE_EDGES = [
    (0, 1), (1, 3), (3, 2), (2, 0),
    (4, 5), (5, 7), (7, 6), (6, 4),
    (0, 4), (1, 5), (2, 6), (3, 7),
]
CUBE_BATCH = batch_for_shader(SHADER, "LINES", {'pos': [CUBE_VERTICES[i] for edge in CUBE_EDGES for i in edge]})


def draw_regions():
    settings = bpy.context.scene.region_draw_settings  # type: RegionDrawSettings
    if settings.draw_mode == "NONE":
        return  # don't draw any regions

    volume_types = {"Sphere", "Cylinder", "Box"}

    # Find all regions to draw.
    regions = {
        "Sphere": [],
        "Cylinder": [],
        "Box": [],
    }

    match settings.draw_mode:
        case "ACTIVE_COLLECTION":
            region_collection = bpy.context.collection
            for obj in region_collection.objects:
                if obj.type == "EMPTY" and (shape := obj.get("Region Shape", "")) in volume_types:
                    regions[shape].append(obj)
        case "SELECTED":
            for obj in bpy.context.selected_objects:
                if obj.type == "EMPTY" and (shape := obj.get("Region Shape", "")) in volume_types:
                    regions[shape].append(obj)
        case "MAP":
            map_stem = bpy.context.scene.soulstruct_settings.map_stem
            collection_name = f"{map_stem} Volumes"
            try:
                collection = bpy.data.collections[collection_name]
            except KeyError:
                return  # no collection to draw
            for obj in collection.objects:
                if obj.type == "EMPTY" and (shape := obj.get("Region Shape", "")) in volume_types:
                    regions[shape].append(obj)
        case "ALL":
            for obj in bpy.context.scene.collection.all_objects:
                if obj.type == "EMPTY" and (shape := obj.get("Region Shape", "")) in volume_types:
                    regions[shape].append(obj)

    SHADER.bind()
    gpu.state.line_width_set(settings.line_width)
    # gpu.state.blend_set("ALPHA")

    SHADER.uniform_float("color", (*settings.region_color, 1.0))

    if settings.draw_cylinders:
        for cylinder in regions["Cylinder"]:
            cylinder_loc = Matrix.Translation(cylinder.location)
            cylinder_rot = cylinder.rotation_euler.to_matrix().to_4x4()
            cylinder_radius = max(cylinder.scale[0], cylinder.scale[1])
            cylinder_height = cylinder.scale[2]
            cylinder_scale = Matrix.Diagonal((cylinder_radius, cylinder_radius, cylinder_height, 1.0))

            gpu.matrix.push()
            gpu.matrix.multiply_matrix(cylinder_loc @ cylinder_rot @ cylinder_scale)
            CIRCLE_BATCH.draw(SHADER)
            CYLINDER_BATCH.draw(SHADER)
            CIRCLE_TOP_BATCH.draw(SHADER)
            gpu.matrix.pop()

    if settings.draw_boxes:
        for box in regions["Box"]:
            box_transform = Matrix.LocRotScale(box.location, box.rotation_euler, box.scale)
            gpu.matrix.push()
            gpu.matrix.multiply_matrix(box_transform)
            CUBE_BATCH.draw(SHADER)
            gpu.matrix.pop()

    # We draw spheres last so we can use the RGB color option.
    if settings.draw_spheres:
        if settings.use_rgb_spheres:
            sphere_colors = [
                (0.0, 0.0, 1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)
            ]
        else:
            sphere_colors = None

        for sphere in regions["Sphere"]:

            sphere_loc = Matrix.Translation(sphere.location)
            sphere_rot = sphere.rotation_euler.to_matrix().to_4x4()
            sphere_scale = Matrix.Scale(max(sphere.scale), 4)

            for i, circle_rot in enumerate((CIRCLE_Z_MAT, CIRCLE_Y_MAT, CIRCLE_X_MAT)):
                if sphere_colors:
                    SHADER.uniform_float("color", (*sphere_colors[i], 1.0))
                gpu.matrix.push()
                gpu.matrix.multiply_matrix(sphere_loc @ sphere_rot @ circle_rot @ sphere_scale)
                CIRCLE_BATCH.draw(SHADER)
                gpu.matrix.pop()

    # gpu.state.blend_set("NONE")
