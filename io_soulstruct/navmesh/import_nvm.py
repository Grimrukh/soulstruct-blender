"""
Import NVM files (with/without DCX) into Blender 3.3+ (Python 3.10+ scripting required).

NVM files are just basic meshes that contain:
    - per-triangle obstacle counts and flags for AI navigation
    - a quaternary box tree containing all triangles in leaf nodes
    - event entity references that allow specific triangle flags to be toggled from EMEVD

This file format is only used in DeS and DS1 (PTDE/DSR).
"""
from __future__ import annotations

__all__ = ["ImportNVM", "ImportNVMWithBinderChoice", "ImportNVMWithMSBChoice"]

import re
import traceback
import typing as tp
from pathlib import Path

import bpy
import bmesh
from bpy_extras.io_utils import ImportHelper
from mathutils import Color

from soulstruct.containers import Binder, BinderEntry
from soulstruct.darksouls1r.maps.nvm import *

from io_soulstruct.utilities import *
from .utilities import *


NVM_BINDER_RE = re.compile(r"^.*?\.nvmbnd(\.dcx)?$")
MAP_NAME_RE = re.compile(r"^(m\d\d)_\d\d_\d\d_\d\d$")


def hsv_color(hue: float, saturation: float, value: float, alpha=1.0) -> tuple[float, float, float, float]:
    color = Color()
    color.hsv = (hue, saturation, value)
    return color.r, color.g, color.b, alpha


RED = hsv_color(0.0, 0.5, 0.5)
ORANGE = hsv_color(0.066, 0.5, 0.5)
YELLOW = hsv_color(0.15, 0.5, 0.5)
GREEN = hsv_color(0.33, 0.5, 0.5)
CYAN = hsv_color(0.5, 0.5, 0.5)
SKY_BLUE = hsv_color(0.6, 0.5, 0.5)
DEEP_BLUE = hsv_color(0.66, 0.5, 0.5)
PURPLE = hsv_color(0.7, 0.8, 0.5)
MAGENTA = hsv_color(0.8, 0.5, 0.5)
PINK = hsv_color(0.95, 0.5, 0.5)
WHITE = hsv_color(0.0, 0.0, 1.0)
GREY = hsv_color(0.0, 0.0, 0.25)
BLACK = hsv_color(0.0, 0.5, 0.0)


# In descending priority order. All flags can be inspected in custom properties.
NAVMESH_FLAG_COLORS = {
    NavmeshType.Solid: BLACK,
    NavmeshType.Degenerate: BLACK,
    NavmeshType.Obstacle: PINK,
    NavmeshType.ObstacleExit: RED,
    NavmeshType.Hole: RED,
    NavmeshType.Ladder: ORANGE,
    NavmeshType.ClosedDoor: ORANGE,
    NavmeshType.Exit: ORANGE,
    NavmeshType.Door: YELLOW,
    NavmeshType.InsideWall: YELLOW,
    NavmeshType.Cliff: YELLOW,
    NavmeshType.WallTouchingFloor: YELLOW,
    NavmeshType.LandingPoint: ORANGE,
    NavmeshType.WideSpace: DEEP_BLUE,
    NavmeshType.Event: GREEN,
    NavmeshType.Wall: CYAN,
    NavmeshType.Default: PURPLE,
}


class ImportNVM(LoggingOperator, ImportHelper):
    bl_idname = "import_scene.nvm"
    bl_label = "Import NVM"
    bl_description = "Import a NVM navmesh file. Can import from BNDs and supports DCX-compressed files"

    filename_ext = ".nvm"

    filter_glob: bpy.props.StringProperty(
        default="*.nvm;*.nvm.dcx;*.nvmbnd;*.nvmbnd.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    import_all_from_binder: bpy.props.BoolProperty(
        name="Import All From Binder",
        description="If a Binder file is opened, import all NVM files rather than being prompted to select one",
        default=False,
    )

    read_msb_transform: bpy.props.BoolProperty(
        name="Read MSB Transform",
        description="Look for matching MSB file in adjacent `MapStudio` folder and set Blender transform from "
                    "navmesh with this model",
        default=True,
    )

    # TODO: Make use?
    use_material: bpy.props.BoolProperty(
        name="Use Material",
        description="If enabled, 'NVM' material will be assigned or created for all imported navmeshes",
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
        print("Executing NVM import...")

        file_paths = [Path(self.directory, file.name) for file in self.files]
        nvms_with_paths = []  # type: list[tuple[Path, NVM | list[BinderEntry]]]

        for file_path in file_paths:

            if NVM_BINDER_RE.match(file_path.name):
                binder = Binder.from_path(file_path)

                # Find NVM entry.
                nvm_entries = binder.find_entries_matching_name(r".*\.nvm(\.dcx)?")
                if not nvm_entries:
                    raise NVMImportError(f"Cannot find any NVM files in binder {file_path}.")

                if len(nvm_entries) > 1:
                    if self.import_all_from_binder:
                        for entry in nvm_entries:
                            try:
                                nvm = entry.to_binary_file(NVM)
                            except Exception as ex:
                                self.warning(f"Error occurred while reading NVM Binder entry '{entry.name}': {ex}")
                            else:
                                nvm.path = Path(entry.name)
                                nvms_with_paths.append((file_path, nvm))
                    else:
                        # Queue up entire Binder; user will be prompted to choose entry below.
                        nvms_with_paths.append((file_path, nvm_entries))
                else:
                    try:
                        nvm = nvm_entries[0].to_binary_file(NVM)
                    except Exception as ex:
                        self.warning(f"Error occurred while reading NVM Binder entry '{nvm_entries[0].name}': {ex}")
                    else:
                        nvms_with_paths.append((file_path, nvm))
            else:
                # Loose NVM.
                try:
                    nvm = NVM.from_path(file_path)
                except Exception as ex:
                    self.warning(f"Error occurred while reading NVM file '{file_path.name}': {ex}")
                else:
                    nvms_with_paths.append((file_path, nvm))

        importer = NVMImporter(self, context)

        for file_path, nvm_or_entries in nvms_with_paths:

            if isinstance(nvm_or_entries, list):
                # Defer through entry selection operator.
                ImportNVMWithBinderChoice.run(
                    importer=importer,
                    binder_file_path=Path(file_path),
                    read_msb_transform=self.read_msb_transform,
                    use_material=self.use_material,
                    nvm_entries=nvm_or_entries,
                )
                continue

            nvm = nvm_or_entries
            nvm_name = nvm.path.name.split(".")[0]

            self.info(f"Importing NVM: {nvm_name}")

            transform = None  # type: tp.Optional[Transform]
            if self.read_msb_transform:
                # NOTE: It's unlikely that this MSB search will work for a loose NVM.
                if MAP_NAME_RE.match(file_path.parent.name):
                    try:
                        transforms = get_navmesh_msb_transforms(nvm_name=nvm_name, nvm_path=file_path)
                    except Exception as ex:
                        self.warning(f"Could not get MSB transform. Error: {ex}")
                    else:
                        if len(transforms) > 1:
                            importer.context = context
                            ImportNVMWithMSBChoice.run(
                                importer=importer,
                                nvm=nvm,
                                nvm_name=nvm_name,
                                use_material=self.use_material,
                                transforms=transforms,
                            )
                            continue
                        transform = transforms[0][1]
                else:
                    self.warning(f"Cannot read MSB transform for NVM in unknown directory: {file_path}.")

            # Import single NVM without MSB transform.
            try:
                importer.import_nvm(nvm, name=nvm_name, transform=transform, use_material=self.use_material)
            except Exception as ex:
                # Delete any objects created prior to exception.
                for obj in importer.all_bl_objs:
                    bpy.data.objects.remove(obj)
                traceback.print_exc()  # for inspection in Blender console
                return self.error(f"Cannot import NVM: {file_path.name}. Error: {ex}")
            
        return {"FINISHED"}


# noinspection PyUnusedLocal
def get_binder_entry_choices(self, context):
    return ImportNVMWithBinderChoice.enum_options


# noinspection PyUnusedLocal
def get_msb_choices(self, context):
    return ImportNVMWithMSBChoice.enum_options


class ImportNVMWithBinderChoice(LoggingOperator):
    """Presents user with a choice of enums from `enum_choices` class variable (set prior).

    See: https://blender.stackexchange.com/questions/6512/how-to-call-invoke-popup
    """
    bl_idname = "wm.nvm_binder_choice_operator"
    bl_label = "Choose NVM Binder Entry"

    # For deferred import in `execute()`.
    importer: tp.Optional[NVMImporter] = None
    binder: tp.Optional[Binder] = None
    binder_file_path: Path = Path()
    enum_options: list[tuple[tp.Any, str, str]] = []
    read_msb_transform: bool = False
    use_material: bool = True
    nvm_entries: tp.Sequence[BinderEntry] = []

    choices_enum: bpy.props.EnumProperty(items=get_binder_entry_choices)

    # noinspection PyUnusedLocal
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    # noinspection PyUnusedLocal
    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "choices_enum", expand=False)

    def execute(self, context):
        choice = int(self.choices_enum)
        entry = self.nvm_entries[choice]
        nvm = entry.to_binary_file(NVM)
        nvm_name = entry.name.split(".")[0]

        self.importer.operator = self
        self.importer.context = context

        transform = None
        if self.read_msb_transform:
            if MAP_NAME_RE.match(self.binder_file_path.parent.name):
                try:
                    transforms = get_navmesh_msb_transforms(nvm_name=nvm_name, nvm_path=self.binder_file_path)
                except Exception as ex:
                    self.warning(f"Could not get MSB transform. Error: {ex}")
                else:
                    if len(transforms) > 1:
                        ImportNVMWithMSBChoice.run(
                            importer=self.importer,
                            nvm=nvm,
                            nvm_name=self.nvm_name,
                            use_material=self.use_material,
                            transforms=transforms,
                        )
                        return {"FINISHED"}
                    transform = transforms[0][1]
            else:
                self.warning(f"Cannot read MSB transform for NVM in unknown directory: {self.binder_file_path}.")
        try:
            self.importer.import_nvm(nvm, name=nvm_name, transform=transform)
        except Exception as ex:
            for obj in self.importer.all_bl_objs:
                bpy.data.objects.remove(obj)
            traceback.print_exc()
            return self.error(f"Cannot import NVM {nvm_name} from '{self.binder_file_path.name}'. Error: {ex}")

        return {"FINISHED"}

    @classmethod
    def run(
        cls,
        importer: NVMImporter,
        binder_file_path: Path,
        read_msb_transform: bool,
        use_material: bool,
        nvm_entries: list[BinderEntry],
    ):
        cls.importer = importer
        cls.binder_file_path = binder_file_path
        cls.enum_options = [(str(i), entry.name, "") for i, entry in enumerate(nvm_entries)]
        cls.read_msb_transform = read_msb_transform
        cls.use_material = use_material
        cls.nvm_entries = nvm_entries
        # noinspection PyUnresolvedReferences
        bpy.ops.wm.nvm_binder_choice_operator("INVOKE_DEFAULT")


class ImportNVMWithMSBChoice(LoggingOperator):
    """Presents user with a choice of enums from `enum_choices` class variable (set prior).

    See: https://blender.stackexchange.com/questions/6512/how-to-call-invoke-popup
    """
    bl_idname = "wm.nvm_msb_choice_operator"
    bl_label = "Choose MSB Entry"

    # For deferred import in `execute()`.
    importer: tp.Optional[NVMImporter] = None
    nvm: tp.Optional[NVM] = None
    nvm_name: str = ""
    enum_options: list[tuple[tp.Any, str, str]] = []
    use_material: bool = True
    transforms: tp.Sequence[Transform] = []

    choices_enum: bpy.props.EnumProperty(items=get_msb_choices)

    # noinspection PyUnusedLocal
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    # noinspection PyUnusedLocal
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
            self.importer.import_nvm(self.nvm, name=self.nvm_name, transform=transform, use_material=self.use_material)
        except Exception as ex:
            for obj in self.importer.all_bl_objs:
                bpy.data.objects.remove(obj)
            traceback.print_exc()
            return self.error(f"Cannot import NVM: {self.file_path.name}. Error: {ex}")

        return {"FINISHED"}

    @classmethod
    def run(
        cls,
        importer: NVMImporter,
        nvm: NVM,
        nvm_name: str,
        use_material: bool,
        transforms: list[tuple[str, Transform]],
    ):
        cls.importer = importer
        cls.nvm = nvm
        cls.nvm_name = nvm_name
        cls.enum_options = [(str(i), name, "") for i, (name, _) in enumerate(transforms)]
        cls.use_material = use_material
        cls.transforms = [tf for _, tf in transforms]
        # noinspection PyUnresolvedReferences
        bpy.ops.wm.nvm_msb_choice_operator("INVOKE_DEFAULT")


class NVMImporter:
    """Manages imports for a batch of NVM files imported simultaneously."""

    nvm: tp.Optional[NVM]
    name: str

    def __init__(
        self,
        operator: ImportNVM,
        context,
    ):
        self.operator = operator
        self.context = context

        self.nvm = None
        self.name = ""
        self.all_bl_objs = []

    def import_nvm(self, nvm: NVM, name: str, transform: Transform = None, use_material=True):
        """Read a NVM into a collection of Blender mesh objects."""
        self.nvm = nvm
        self.name = name  # should not have extensions (e.g. `h0100B0A10`)
        self.operator.info(f"Importing NVM: {name}")

        # Set mode to OBJECT and deselect all objects.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action="DESELECT")
        if bpy.ops.object.mode_set.poll():  # just to be safe
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        # Create mesh.
        bl_mesh = bpy.data.meshes.new(name=name)
        vertices = [(-v[0], -v[2], v[1]) for v in nvm.vertices]  # forward is -Z, up is Y, X is mirrored
        edges = []  # no edges in NVM
        faces = [triangle.vertex_indices for triangle in nvm.triangles]
        bl_mesh.from_pydata(vertices, edges, faces)
        mesh_obj = bpy.data.objects.new(self.name, bl_mesh)
        self.context.scene.collection.objects.link(mesh_obj)
        if transform is not None:
            mesh_obj.location = transform.bl_translate
            mesh_obj.rotation_euler = transform.bl_rotate
            mesh_obj.scale = transform.bl_scale
        self.all_bl_objs = [mesh_obj]

        # TODO: Do colors up here with normal mesh.
        if use_material:
            mesh_materials = []
            for bl_face, nvm_face in zip(bl_mesh.polygons, nvm.triangles):
                # Color face according to its single `flag` if present.
                if nvm_face.flag is None:
                    material_name = "Navmesh Flag <Unknown>"
                else:
                    material_name = f"Navmesh Flag {nvm_face.flag.name}"

                try:
                    bl_face.material_index = mesh_materials.index(material_name)
                except ValueError:
                    # Material not added to mesh.
                    try:
                        bl_material = bl_mesh.materials.data.materials[material_name]
                    except KeyError:
                        # Create new material with color from dictionary.
                        color = NAVMESH_FLAG_COLORS[nvm_face.flag] if nvm_face.flag is not None else WHITE
                        bl_material = self.create_basic_material(material_name, color)
                    # Add material to mesh.
                    bl_mesh.materials.append(bl_material)
                    bl_face.material_index = len(mesh_materials)
                    mesh_materials.append(material_name)

        # Create BMESH (as we need to assign face flag data).
        bm = bmesh.new()
        bm.from_mesh(bl_mesh)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        navmesh_type_layers = {}
        for navmesh_type in NavmeshType:
            if navmesh_type == NavmeshType.Default:
                continue  # redundant
            navmesh_type_layers[navmesh_type] = bm.faces.layers.int.new(f"{navmesh_type.name}")

        # TODO: Is there any chance the face count could change, e.g. if some NVM faces were degenerate and ignored?
        for f_i, face in enumerate(bm.faces):
            nvm_face = nvm.triangles[f_i]
            for navmesh_type, navmesh_layer in navmesh_type_layers.items():
                face[navmesh_layer] = int(nvm_face.all_flags & navmesh_type == navmesh_type)

        bm.to_mesh(bl_mesh)
        del bm

        # TODO: There are always three levels of boxes, it seems, so this is very potentially automatable.

        # Create box tree (depth first creation order). Nesting info in name is used to export.
        for box, indices in nvm.get_all_boxes(nvm.root_box):
            if not indices:
                box_name = f"{self.name} Box ROOT"
            else:
                indices_string = "-".join(str(i) for i in indices)
                box_name = f"{self.name} Box {indices_string}"
            bl_box = self.create_box(box)
            bl_box.name = box_name
        # TODO: How to store triangles linked to each box?
        #  If each triangle is only linked to ONE box, can store the box name on the triangle itself.
        #  Otherwise, can store a list of face indices on each box, but that seems finicky to edit.
        #  Of course, moving a triangle will require the box to move anyway, so it's always going to be finicky.

        # TODO: Event entities?

    @staticmethod
    def create_basic_material(material_name: str, color: tuple[float, float, float, float]):
        bl_material = bpy.data.materials.new(name=material_name)
        bl_material.use_nodes = True
        nt = bl_material.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = color
        return bl_material

    def create_box(self, box: NVMBox):
        """Create an AABB prism representing `box`. Position is baked into mesh data fully, just like the navmesh."""
        start_vec = GAME_TO_BL_VECTOR(box.start_corner)
        end_vec = GAME_TO_BL_VECTOR(box.end_corner)
        bpy.ops.mesh.primitive_cube_add()
        bl_box = bpy.context.active_object
        self.all_bl_objs.append(bl_box)
        for vertex in bl_box.data.vertices:
            vertex.co[0] = start_vec.x if vertex.co[0] == -1.0 else end_vec.x
            vertex.co[1] = start_vec.y if vertex.co[1] == -1.0 else end_vec.y
            vertex.co[2] = start_vec.z if vertex.co[2] == -1.0 else end_vec.z
        bpy.ops.object.modifier_add(type="WIREFRAME")
        bl_box.modifiers[0].thickness = 0.02
        bl_box.parent = self.all_bl_objs[0]
        return bl_box
