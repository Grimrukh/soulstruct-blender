"""
Import HKX files (with/without DCX) into Blender 3.3+ (Python 3.10+ scripting required).

The HKX's subparts are imported as separate meshes, parented to a single Empty named after the collision. The only
relevant data aside from the mesh vertices/faces are `material_index` custom properties on each subpart.

TODO: Currently only supports map collision HKX files from Dark Souls Remastered.
"""
from __future__ import annotations

__all__ = ["ImportHKXMapCollision", "ImportHKXMapCollisionWithBinderChoice", "ImportHKXMapCollisionWithMSBChoice"]

import re
import traceback
import typing as tp
from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper
from mathutils import Color

from soulstruct.containers import Binder, BinderEntry

from soulstruct_havok.wrappers.hkx2015 import MapCollisionHKX

from io_soulstruct.utilities import *
from .utilities import *


HKX_BINDER_RE = re.compile(r"^.*?\.hkxbhd(\.dcx)?$")
MAP_NAME_RE = re.compile(r"^(m\d\d)_\d\d_\d\d_\d\d$")


class ImportHKXMapCollision(LoggingOperator, ImportHelper):
    bl_idname = "import_scene.hkx_map_collision"
    bl_label = "Import HKX Collision"
    bl_description = "Import a HKX collision file. Can import from BNDs and supports DCX-compressed files"

    # ImportHelper mixin class uses this
    filename_ext = ".hkx"

    filter_glob: bpy.props.StringProperty(
        default="*.hkx;*.hkx.dcx;*.hkxbhd",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    import_all_from_binder: bpy.props.BoolProperty(
        name="Import All From Binder",
        description="If a Binder file is opened, import all HKX files rather than being prompted to select one",
        default=False,
    )

    read_msb_transform: bpy.props.BoolProperty(
        name="Read MSB Transform",
        description="Look for matching MSB file in adjacent `MapStudio` folder and set Blender transform from "
                    "collision with this model",
        default=True,
    )

    use_material: bpy.props.BoolProperty(
        name="Use Material",
        description="If enabled, 'HKX Hi' or 'HKX Lo' material will be assigned or created for all collision meshes",
        default=True,
    )

    files: bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'},
    )

    directory: bpy.props.StringProperty(
        options={'HIDDEN'},
    )

    def execute(self, context):
        print("Executing HKX collision import...")

        def GO():

            file_paths = [Path(self.directory, file.name) for file in self.files]
            hkxs_with_paths = []  # type: list[tuple[Path, MapCollisionHKX | list[BinderEntry]]]

            for file_path in file_paths:

                if HKX_BINDER_RE.match(file_path.name):
                    binder = Binder.from_path(file_path)

                    # Find HKX entry.
                    hkx_entries = binder.find_entries_matching_name(r".*\.hkx(\.dcx)?")
                    if not hkx_entries:
                        raise HKXImportError(f"Cannot find any HKX files in binder {file_path}.")

                    if len(hkx_entries) > 1:
                        if self.import_all_from_binder:
                            for entry in hkx_entries:
                                try:
                                    hkx = entry.to_binary_file(MapCollisionHKX)
                                except Exception as ex:
                                    self.warning(f"Error occurred while reading HKX Binder entry '{entry.name}': {ex}")
                                else:
                                    hkx.path = Path(entry.name)  # also done in `GameFile`, but explicitly needed below
                                    hkxs_with_paths.append((file_path, hkx))
                        else:
                            # Queue up entire Binder; user will be prompted to choose entry below.
                            hkxs_with_paths.append((file_path, hkx_entries))
                    else:
                        try:
                            hkx = hkx_entries[0].to_binary_file(MapCollisionHKX)
                        except Exception as ex:
                            self.warning(f"Error occurred while reading HKX Binder entry '{hkx_entries[0].name}': {ex}")
                        else:
                            hkxs_with_paths.append((file_path, hkx))
                else:
                    # Loose HKX.
                    try:
                        hkx = MapCollisionHKX.from_path(file_path)
                    except Exception as ex:
                        self.warning(f"Error occurred while reading HKX file '{file_path.name}': {ex}")
                    else:
                        hkxs_with_paths.append((file_path, hkx))

            importer = HKXMapCollisionImporter(self, context)

            for file_path, hkx_or_entries in hkxs_with_paths:

                if isinstance(hkx_or_entries, list):
                    # Defer through entry selection operator.
                    ImportHKXMapCollisionWithBinderChoice.run(
                        importer=importer,
                        binder_file_path=Path(file_path),
                        read_msb_transform=self.read_msb_transform,
                        use_material=self.use_material,
                        hkx_entries=hkx_or_entries,
                    )
                    continue

                hkx = hkx_or_entries
                hkx_name = hkx.path.name.split(".")[0]

                self.info(f"Importing HKX: {hkx_name}")

                transform = None  # type: tp.Optional[Transform]
                if self.read_msb_transform:
                    # NOTE: It's unlikely that this MSB search will work for a loose HKX.
                    if MAP_NAME_RE.match(file_path.parent.name):
                        try:
                            transforms = get_msb_transforms(hkx_name=hkx_name, hkx_path=file_path)
                        except Exception as ex:
                            self.warning(f"Could not get MSB transform. Error: {ex}")
                        else:
                            if len(transforms) > 1:
                                importer.context = context
                                ImportHKXMapCollisionWithMSBChoice.run(
                                    importer=importer,
                                    hkx=hkx,
                                    hkx_name=hkx_name,
                                    use_material=self.use_material,
                                    transforms=transforms,
                                )
                                continue
                            transform = transforms[0][1]
                    else:
                        self.warning(f"Cannot read MSB transform for HKX in unknown directory: {file_path}.")

                # Import single HKX without MSB transform.
                try:
                    importer.import_hkx(hkx, name=hkx_name, transform=transform, use_material=self.use_material)
                except Exception as ex:
                    # Delete any objects created prior to exception.
                    for obj in importer.all_bl_objs:
                        bpy.data.objects.remove(obj)
                    traceback.print_exc()  # for inspection in Blender console
                    return self.error(f"Cannot import HKX: {file_path.name}. Error: {ex}")

        import cProfile
        import pstats

        with cProfile.Profile() as pr:
            GO()
        p = pstats.Stats(pr)
        p = p.strip_dirs()
        p.sort_stats("tottime").print_stats(40)

        return {"FINISHED"}


# noinspection PyUnusedLocal
def get_binder_entry_choices(self, context):
    return ImportHKXMapCollisionWithBinderChoice.enum_options


# noinspection PyUnusedLocal
def get_msb_choices(self, context):
    return ImportHKXMapCollisionWithMSBChoice.enum_options


class ImportHKXMapCollisionWithBinderChoice(LoggingOperator):
    """Presents user with a choice of enums from `enum_choices` class variable (set prior).

    See: https://blender.stackexchange.com/questions/6512/how-to-call-invoke-popup
    """
    bl_idname = "wm.hkx_map_collision_binder_choice_operator"
    bl_label = "Choose HKX Collision Binder Entry"

    # For deferred import in `execute()`.
    importer: tp.Optional[HKXMapCollisionImporter] = None
    binder: tp.Optional[Binder] = None
    binder_file_path: Path = Path()
    enum_options: list[tuple[tp.Any, str, str]] = []
    read_msb_transform: bool = False
    use_material: bool = True
    hkx_entries: tp.Sequence[BinderEntry] = []

    choices_enum: bpy.props.EnumProperty(items=get_binder_entry_choices)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "choices_enum", expand=False)

    def execute(self, context):
        choice = int(self.choices_enum)
        entry = self.hkx_entries[choice]
        hkx = entry.to_binary_file(MapCollisionHKX)
        hkx_name = entry.name.split(".")[0]

        self.importer.operator = self
        self.importer.context = context

        transform = None
        if self.read_msb_transform:
            if MAP_NAME_RE.match(self.binder_file_path.parent.name):
                try:
                    transforms = get_msb_transforms(hkx_name=hkx_name, hkx_path=self.binder_file_path)
                except Exception as ex:
                    self.warning(f"Could not get MSB transform. Error: {ex}")
                else:
                    if len(transforms) > 1:
                        ImportHKXMapCollisionWithMSBChoice.run(
                            importer=self.importer,
                            hkx=hkx,
                            hkx_name=hkx_name,
                            use_material=self.use_material,
                            transforms=transforms,
                        )
                        return {"FINISHED"}
                    transform = transforms[0][1]
            else:
                self.warning(f"Cannot read MSB transform for HKX in unknown directory: {self.binder_file_path}.")
        try:
            self.importer.import_hkx(hkx, name=hkx_name, transform=transform)
        except Exception as ex:
            for obj in self.importer.all_bl_objs:
                bpy.data.objects.remove(obj)
            traceback.print_exc()
            return self.error(f"Cannot import HKX {hkx_name} from '{self.binder_file_path.name}'. Error: {ex}")

        return {'FINISHED'}

    @classmethod
    def run(
        cls,
        importer: HKXMapCollisionImporter,
        binder_file_path: Path,
        read_msb_transform: bool,
        use_material: bool,
        hkx_entries: list[BinderEntry],
    ):
        cls.importer = importer
        cls.binder_file_path = binder_file_path
        cls.enum_options = [(str(i), entry.name, "") for i, entry in enumerate(hkx_entries)]
        cls.read_msb_transform = read_msb_transform
        cls.use_material = use_material
        cls.hkx_entries = hkx_entries
        # noinspection PyUnresolvedReferences
        bpy.ops.wm.hkx_map_collision_binder_choice_operator("INVOKE_DEFAULT")


class ImportHKXMapCollisionWithMSBChoice(LoggingOperator):
    """Presents user with a choice of enums from `enum_choices` class variable (set prior).

    See: https://blender.stackexchange.com/questions/6512/how-to-call-invoke-popup
    """
    bl_idname = "wm.hkx_map_collision_msb_choice_operator"
    bl_label = "Choose MSB Entry"

    # For deferred import in `execute()`.
    importer: tp.Optional[HKXMapCollisionImporter] = None
    hkx: tp.Optional[MapCollisionHKX] = None
    hkx_name: str = ""
    enum_options: list[tuple[tp.Any, str, str]] = []
    use_material: bool = True
    transforms: tp.Sequence[Transform] = []

    choices_enum: bpy.props.EnumProperty(items=get_msb_choices)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "choices_enum", expand=True)

    def execute(self, context):
        choice = int(self.choices_enum)
        transform = self.transforms[choice]

        self.importer.operator = self
        self.importer.context = context

        try:
            self.importer.import_hkx(self.hkx, name=self.hkx_name, transform=transform, use_material=self.use_material)
        except Exception as ex:
            for obj in self.importer.all_bl_objs:
                bpy.data.objects.remove(obj)
            traceback.print_exc()
            return self.error(f"Cannot import HKX: {self.file_path.name}. Error: {ex}")

        return {'FINISHED'}

    @classmethod
    def run(
        cls,
        importer: HKXMapCollisionImporter,
        hkx: MapCollisionHKX,
        hkx_name: str,
        use_material: bool,
        transforms: list[tuple[str, Transform]],
    ):
        cls.importer = importer
        cls.hkx = hkx
        cls.hkx_name = hkx_name
        cls.enum_options = [(str(i), name, "") for i, (name, _) in enumerate(transforms)]
        cls.use_material = use_material
        cls.transforms = [tf for _, tf in transforms]
        # noinspection PyUnresolvedReferences
        bpy.ops.wm.hkx_msb_choice_operator("INVOKE_DEFAULT")


class HKXMapCollisionImporter:
    """Manages imports for a batch of HKX files imported simultaneously."""

    hkx: tp.Optional[MapCollisionHKX]
    name: str

    def __init__(
        self,
        operator: ImportHKXMapCollision,
        context,
    ):
        self.operator = operator
        self.context = context

        self.hkx = None
        self.name = ""
        self.all_bl_objs = []

    def import_hkx(self, hkx: MapCollisionHKX, name: str, transform: Transform = None, use_material=True):
        """Read a HKX into a collection of Blender mesh objects."""
        self.hkx = hkx
        self.name = name  # should not have extensions (e.g. `h0100B0A10`)

        # Set mode to OBJECT and deselect all objects.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action="DESELECT")
        if bpy.ops.object.mode_set.poll():  # just to be safe
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        # Empty parent.
        hkx_parent = bpy.data.objects.new(self.name, None)
        self.context.scene.collection.objects.link(hkx_parent)
        if transform is not None:
            hkx_parent.location = transform.bl_translate
            hkx_parent.rotation_euler = transform.bl_rotate
            hkx_parent.scale = transform.bl_scale

        self.all_bl_objs = [hkx_parent]

        meshes = self.hkx.to_meshes()
        material_indices = self.hkx.map_collision_physics_data.get_subpart_materials()
        for i, hkx_subpart in enumerate(meshes):
            mesh_name = f"{self.name} Submesh {i}"
            bl_mesh = self.create_mesh_obj(hkx_subpart, material_indices[i], mesh_name)
            if use_material:
                # TODO: From HSV, with H jumping up by something like
                material_name = "HKX Lo" if name.startswith("l") else "HKX Hi"  # hi is default for weird names
                material_name += " (Mat 1)" if material_indices[i] == 1 else " (Not Mat 1)"
                try:
                    bl_material = bpy.data.materials[material_name]
                except KeyError:
                    # Create basic material: orange (lo) or blue (hi/other), lighter for material 1 (most common).
                    color = Color()
                    # Hue rotates between 10 values. Material index 1 (very common) is mapped to nice blue hue 0.6.
                    hue = 0.1 * ((material_indices[i] + 5) % 10)
                    saturation = 0.4 if name.startswith("l") else 0.8
                    value = 0.5
                    color.hsv = (hue, saturation, value)
                    bl_material = self.create_basic_material(material_name, (color.r, color.g, color.b, 1.0))
                bl_mesh.data.materials.append(bl_material)

    def create_mesh_obj(
        self,
        hkx_mesh: tuple[list[tuple[float, float, float]], list[tuple[int, ...]]],
        material_index: int,
        mesh_name: str,
    ):
        """Create a Blender mesh object. The only custom property for HKX is material index."""
        bl_mesh = bpy.data.meshes.new(name=mesh_name)

        vertices = [(-v[0], -v[2], v[1]) for v in hkx_mesh[0]]  # forward is -Z, up is Y, X is mirrored
        edges = []  # no edges in HKX
        faces = hkx_mesh[1]
        bl_mesh.from_pydata(vertices, edges, faces)

        bl_mesh_obj = self.create_obj(mesh_name, bl_mesh)
        bl_mesh_obj["material_index"] = material_index

        return bl_mesh_obj

    @staticmethod
    def create_basic_material(material_name: str, color: tuple[float, float, float, float]):
        bl_material = bpy.data.materials.new(name=material_name)
        bl_material.use_nodes = True
        nt = bl_material.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = color
        return bl_material

    def create_obj(self, name: str, data=None):
        """Create a new Blender object and parent it to main Empty."""
        obj = bpy.data.objects.new(name, data)
        self.context.scene.collection.objects.link(obj)
        self.all_bl_objs.append(obj)
        obj.parent = self.all_bl_objs[0]
        return obj
