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

import traceback
import typing as tp
from pathlib import Path

import bpy
import bmesh
from bpy_extras.io_utils import ImportHelper

from soulstruct.containers import Binder, BinderEntry, BinderEntryNotFoundError
from soulstruct.darksouls1r.maps import MSB
from soulstruct.darksouls1r.maps.navmesh.nvm import NVM, NVMBox

from io_soulstruct.utilities import *
from .utilities import *


class NVMImportInfo(tp.NamedTuple):
    """Holds information about a navmesh to import into Blender."""
    path: Path  # source file for NVM (likely a Binder path)
    model_file_stem: str  # generally stem of NVM file or Binder entry
    bl_name: str  # name to assign to Blender object (usually same as `nvm_name`)
    nvm: NVM  # parsed NVM


class NVMImportChoiceInfo(tp.NamedTuple):
    """Holds information about a Binder entry choice that the user will make in deferred operator."""
    path: Path  # Binder path
    entries: list[BinderEntry]  # entries from which user must choose


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

    navmesh_model_id: bpy.props.IntProperty(
        name="Navmesh Model ID",
        description="Model ID of the navmesh model to import (e.g. 200 for 'n0200'). Leave as -1 to have a choice "
                    "pop-up appear",
        default=-1,
    )

    import_all_from_binder: bpy.props.BoolProperty(
        name="Import All From NVMBND",
        description="If a NVMBND binder file is opened, import all NVM files rather than being prompted to select one",
        default=False,
    )

    import_all_msb_parts: bpy.props.BoolProperty(
        name="Import All MSB Parts",
        description="If a single NVMBND file is opened, find corresponding MSB and import each model used by its "
                    "Navmesh parts (with linked duplicates for reused models)",
        default=False,
    )

    read_msb_transform: bpy.props.BoolProperty(
        name="Read MSB Transform",
        description="Look for matching MSB file in adjacent `MapStudio` folder and set Blender transform from "
                    "navmesh with this model",
        default=True,
    )

    use_material: bpy.props.BoolProperty(
        name="Use Material",
        description="If enabled, 'NVM' material will be assigned or created for all imported navmeshes",
        default=True,
    )

    create_quadtree_boxes: bpy.props.BoolProperty(
        name="Create Quadtree Boxes",
        description="If enabled, create quadtree boxes for all imported navmeshes",
        default=False,
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
        import_infos = []  # type: list[NVMImportInfo | NVMImportChoiceInfo]

        if self.import_all_msb_parts:
            if len(file_paths) != 1 or not NVMBND_NAME_RE.match(file_paths[0].name):
                return self.error("Must import exactly one NVMBND file when importing all MSB parts.")
            nvmbnd_path = file_paths[0]
            nvmbnd_stem = nvmbnd_path.name.split(".")[0]
            msb_path = (nvmbnd_path.parent / f"../MapStudio/{nvmbnd_stem}.msb").resolve()
            if not msb_path.is_file():
                return self.error(f"Could not find matching MSB file for NVMBND file '{nvmbnd_path.name}': {msb_path}.")
        else:
            msb_path = None

        for file_path in file_paths:

            is_binder = NVMBND_NAME_RE.match(file_path.name) is not None

            if is_binder:
                binder = Binder.from_path(file_path)
                if msb_path:
                    map_area = msb_path.stem[1:3]
                    msb = MSB.from_path(msb_path)
                    new_import_infos = self.load_msb_part_models_from_binder(binder, file_path, msb, map_area)
                else:
                    new_import_infos = self.load_from_binder(binder, file_path)
                import_infos.extend(new_import_infos)
            else:
                # Loose NVM.
                try:
                    nvm = NVM.from_path(file_path)
                except Exception as ex:
                    self.warning(f"Error occurred while reading NVM file '{file_path.name}': {ex}")
                else:
                    model_file_stem = file_path.name.split(".")[0]
                    new_non_choice_import_infos = [NVMImportInfo(file_path, model_file_stem, model_file_stem, nvm)]
                    import_infos.extend(new_non_choice_import_infos)

        importer = NVMImporter(
            self,
            context,
            use_linked_duplicates=self.import_all_msb_parts,
            parent_obj_name=f"{msb_path.stem} Navmeshes" if msb_path else "",
        )

        for import_info in import_infos:

            if isinstance(import_info, NVMImportChoiceInfo):
                # Defer through entry selection operator.
                ImportNVMWithBinderChoice.run(
                    importer=importer,
                    binder_file_path=import_info.path,
                    read_msb_transform=self.read_msb_transform,
                    use_material=self.use_material,
                    create_quadtree_boxes=self.create_quadtree_boxes,
                    nvm_entries=import_info.entries,
                )
                continue

            self.info(f"Importing NVM model {import_info.model_file_stem} as '{import_info.bl_name}'.")

            transform = None  # type: tp.Optional[Transform]
            if self.read_msb_transform:
                # NOTE: It's unlikely that this MSB search will work for a loose NVM, but we can try.
                if MAP_STEM_RE.match(import_info.path.parent.name):
                    msb_model_name = import_info.model_file_stem[:7]
                    try:
                        transforms = get_navmesh_msb_transforms(msb_model_name, nvm_path=import_info.path)
                    except Exception as ex:
                        self.warning(f"Could not get MSB transform for '{import_info.model_file_stem}'. Error: {ex}")
                    else:
                        if len(transforms) > 1:
                            importer.context = context
                            ImportNVMWithMSBChoice.run(
                                importer=importer,
                                import_info=import_info,
                                use_material=self.use_material,
                                create_quadtree_boxes=self.create_quadtree_boxes,
                                transforms=transforms,
                            )
                            continue
                        transform = transforms[0][1]
                else:
                    self.warning(f"Cannot read MSB transform for NVM in unknown directory: {import_info.path}.")

            # Import single NVM.
            try:
                nvm_obj = importer.import_nvm(
                    import_info,
                    use_material=self.use_material,
                    create_quadtree_boxes=self.create_quadtree_boxes,
                )
            except Exception as ex:
                # Delete any objects created prior to exception.
                for obj in importer.all_bl_objs:
                    bpy.data.objects.remove(obj)
                traceback.print_exc()  # for inspection in Blender console
                return self.error(f"Cannot import NVM: {import_info.path}. Error: {ex}")

            if transform is not None:
                # Assign detected MSB transform to navmesh.
                nvm_obj.location = transform.bl_translate
                nvm_obj.rotation_euler = transform.bl_rotate
                nvm_obj.scale = transform.bl_scale

        return {"FINISHED"}

    def load_from_binder(self, binder: Binder, file_path: Path) -> list[NVMImportInfo | NVMImportChoiceInfo]:
        """Load one or more `NVM` files from a `Binder` and queue them for import.

        Will queue up a list of Binder entries if `self.import_all_from_binder` is False and `navmesh_model_id`
        import setting is -1.

        Returns a list of `NVMImportInfo` or `NVMImportChoiceInfo` objects, depending on whether the Binder contains
        multiple entries that the user may need to choose from.
        """
        nvm_entries = binder.find_entries_matching_name(ANY_NVM_NAME_RE)
        if not nvm_entries:
            raise NVMImportError(f"Cannot find any '.nvm{{.dcx}}' files in binder {file_path}.")

        # Filter by `navmesh_model_id` if needed.
        if self.navmesh_model_id != -1:
            nvm_entries = [entry for entry in nvm_entries if self.check_nvm_entry_model_id(entry)]
        if not nvm_entries:
            raise NVMImportError(
                f"Found '.nvm{{.dcx}}' files, but none with model ID {self.navmesh_model_id} in binder {file_path}."
            )

        if len(nvm_entries) > 1:
            # Binder contains multiple (matching) entries.
            if self.import_all_from_binder:
                # Load all detected/matching KX entries in binder and queue them for import.
                new_import_infos = []  # type: list[NVMImportInfo]
                for entry in nvm_entries:
                    try:
                        nvm = entry.to_binary_file(NVM)
                    except Exception as ex:
                        self.warning(f"Error occurred while reading NVM Binder entry '{entry.name}': {ex}")
                    else:
                        nvm.path = Path(entry.name)  # also done in `GameFile`, but explicitly needed below
                        new_import_infos.append(NVMImportInfo(file_path, entry.minimal_stem, entry.minimal_stem, nvm))
                return new_import_infos

            # Queue up all matching Binder entries instead of loaded NVM instances; user will choose entry in pop-up.
            return [NVMImportChoiceInfo(file_path, nvm_entries)]

        # Binder only contains one (matching) NVM.
        try:
            nvm = nvm_entries[0].to_binary_file(NVM)
        except Exception as ex:
            self.warning(f"Error occurred while reading NVM Binder entry '{nvm_entries[0].name}': {ex}")
            return []

        return [NVMImportInfo(file_path, nvm_entries[0].minimal_stem, nvm_entries[0].minimal_stem, nvm)]

    def load_msb_part_models_from_binder(
        self, binder: Binder, file_path: Path, msb: MSB, map_area: str
    ) -> list[NVMImportInfo | NVMImportChoiceInfo]:
        """Load each `NVM` file from a `Binder` used in the given MSB and queue them for import.

        NOTE: Requires that each model file exists only once in the NVMBND.
        """
        # Load all models used by MSB parts.
        new_import_infos = []  # type: list[NVMImportInfo]
        for navmesh_part in msb.navmeshes:
            model_file_name = navmesh_part.model.name + f"A{map_area}.nvm"
            try:
                entry = binder.find_entry_matching_name(model_file_name)
            except BinderEntryNotFoundError:
                raise NVMImportError(
                    f"Could not find NVMBND model file '{model_file_name}' for MSB navmesh '{navmesh_part.name}'."
                )
            except ValueError:
                raise NVMImportError(
                    f"Found multiple matches for NVMBND model file '{model_file_name}' in NVMBND."
                )
            try:
                nvm = entry.to_binary_file(NVM)
            except Exception as ex:
                self.warning(f"Error occurred while reading NVMBND entry '{entry.name}': {ex}")
            else:
                nvm.path = Path(entry.name)  # also done in `GameFile`, but explicitly needed below
                # May involve duplicate models, which will be handled by importer.
                new_import_infos.append(NVMImportInfo(file_path, entry.minimal_stem, navmesh_part.name, nvm))
        return new_import_infos

    def check_nvm_entry_model_id(self, nvm_entry: BinderEntry) -> bool:
        """Checks if the given NVM Binder entry matches the given navmesh model ID."""
        try:
            entry_model_id = int(nvm_entry.name[1:5])  # e.g. 'n1234' -> 1234
        except ValueError:
            return False  # not a match (weird NVM name)
        return entry_model_id == self.navmesh_model_id


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
    nvm_entries: tp.Sequence[BinderEntry] = []
    enum_options: list[tuple[tp.Any, str, str]] = []

    read_msb_transform: bool = False
    use_material: bool = True
    create_quadtree_boxes: bool = False

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
        import_info = NVMImportInfo(self.binder_file_path, entry.minimal_stem, entry.minimal_stem, nvm)
        nvm_model_name = entry.name.split(".")[0]

        self.importer.operator = self
        self.importer.context = context

        transform = None
        if self.read_msb_transform:
            if MAP_STEM_RE.match(self.binder_file_path.parent.name):
                msb_model_name = import_info.model_file_stem[:7]
                try:
                    transforms = get_navmesh_msb_transforms(msb_model_name, nvm_path=self.binder_file_path)
                except Exception as ex:
                    self.warning(f"Could not get MSB transform. Error: {ex}")
                else:
                    if len(transforms) > 1:
                        ImportNVMWithMSBChoice.run(
                            importer=self.importer,
                            import_info=import_info,
                            use_material=self.use_material,
                            create_quadtree_boxes=self.create_quadtree_boxes,
                            transforms=transforms,
                        )
                        return {"FINISHED"}
                    transform = transforms[0][1]
            else:
                self.warning(f"Cannot read MSB transform for NVM in unknown directory: {self.binder_file_path}.")
        try:
            nvm_obj = self.importer.import_nvm(
                import_info,
                use_material=self.use_material,
                create_quadtree_boxes=self.create_quadtree_boxes,
            )
        except Exception as ex:
            for obj in self.importer.all_bl_objs:
                bpy.data.objects.remove(obj)
            traceback.print_exc()
            return self.error(f"Cannot import NVM {nvm_model_name} from '{self.binder_file_path.name}'. Error: {ex}")

        if transform is not None:
            # Assign detected MSB transform to navmesh.
            nvm_obj.location = transform.bl_translate
            nvm_obj.rotation_euler = transform.bl_rotate
            nvm_obj.scale = transform.bl_scale

        return {"FINISHED"}

    @classmethod
    def run(
        cls,
        importer: NVMImporter,
        binder_file_path: Path,
        read_msb_transform: bool,
        use_material: bool,
        create_quadtree_boxes: bool,
        nvm_entries: list[BinderEntry],
    ):
        cls.importer = importer
        cls.binder_file_path = binder_file_path
        cls.enum_options = [(str(i), entry.name, "") for i, entry in enumerate(nvm_entries)]
        cls.read_msb_transform = read_msb_transform
        cls.use_material = use_material
        cls.create_quadtree_boxes = create_quadtree_boxes
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
    import_info: NVMImportInfo | None = None
    enum_options: list[tuple[tp.Any, str, str]] = []
    use_material: bool = True
    create_quadtree_boxes: bool = False
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
            nvm_obj = self.importer.import_nvm(
                self.import_info,
                use_material=self.use_material,
                create_quadtree_boxes=self.create_quadtree_boxes,
            )
        except Exception as ex:
            for obj in self.importer.all_bl_objs:
                bpy.data.objects.remove(obj)
            traceback.print_exc()
            return self.error(f"Cannot import NVM: {self.import_info.bl_name}. Error: {ex}")

        if transform is not None:
            # Assign detected MSB transform to navmesh.
            nvm_obj.location = transform.bl_translate
            nvm_obj.rotation_euler = transform.bl_rotate
            nvm_obj.scale = transform.bl_scale

        return {"FINISHED"}

    @classmethod
    def run(
        cls,
        importer: NVMImporter,
        import_info: NVMImportInfo,
        use_material: bool,
        create_quadtree_boxes: bool,
        transforms: list[tuple[str, Transform]],
    ):
        cls.importer = importer
        cls.import_info = import_info
        cls.enum_options = [(str(i), name, "") for i, (name, _) in enumerate(transforms)]
        cls.use_material = use_material
        cls.create_quadtree_boxes = create_quadtree_boxes
        cls.transforms = [tf for _, tf in transforms]
        # noinspection PyUnresolvedReferences
        bpy.ops.wm.nvm_msb_choice_operator("INVOKE_DEFAULT")


class NVMImporter:
    """Manages imports for a batch of NVM files imported simultaneously."""

    nvm: tp.Optional[NVM]
    bl_name: str
    use_linked_duplicates: bool

    parent_obj: bpy.types.Object | None
    imported_models: dict[str, bpy.types.Object]  # model file stem -> Blender object

    def __init__(
        self,
        operator: ImportNVM,
        context,
        use_linked_duplicates=False,
        parent_obj_name: str = None,
    ):
        self.operator = operator
        self.context = context
        self.use_linked_duplicates = use_linked_duplicates

        if parent_obj_name:
            self.parent_obj = bpy.data.objects.new(parent_obj_name, None)
            self.context.scene.collection.objects.link(self.parent_obj)
        else:
            self.parent_obj = None
        self.all_bl_objs = []
        self.imported_models = {}

    def import_nvm(self, import_info: NVMImportInfo, use_material=True, create_quadtree_boxes=False):
        """Read a NVM into a collection of Blender mesh objects."""

        if self.use_linked_duplicates and import_info.model_file_stem in self.imported_models:
            # Model already imported. Create a linked duplicate Blender object.
            mesh_data = self.imported_models[import_info.model_file_stem].data
            duplicate_obj = bpy.data.objects.new(import_info.bl_name, mesh_data)
            self.context.scene.collection.objects.link(duplicate_obj)
            self.all_bl_objs = [duplicate_obj]
            if self.parent_obj:
                duplicate_obj.parent = self.parent_obj
            if create_quadtree_boxes:
                self.create_nvm_quadtree(duplicate_obj, import_info.nvm, import_info.bl_name)
            return duplicate_obj

        # Set mode to OBJECT and deselect all objects.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action="DESELECT")
        if bpy.ops.object.mode_set.poll():  # just to be safe
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        # Create mesh.
        nvm = import_info.nvm
        bl_mesh = bpy.data.meshes.new(name=import_info.bl_name)
        vertices = [GAME_TO_BL_VECTOR(v) for v in nvm.vertices]
        edges = []  # no edges in NVM
        faces = [triangle.vertex_indices for triangle in nvm.triangles]
        bl_mesh.from_pydata(vertices, edges, faces)
        mesh_obj = bpy.data.objects.new(import_info.bl_name, bl_mesh)
        self.context.scene.collection.objects.link(mesh_obj)
        self.all_bl_objs = [mesh_obj]

        if use_material:
            for bl_face, nvm_triangle in zip(bl_mesh.polygons, nvm.triangles):
                set_face_material(bl_mesh, bl_face, nvm_triangle.flags)

        # Create `BMesh` (as we need to assign face flag data to a custom `int` layer).
        bm = bmesh.new()
        bm.from_mesh(bl_mesh)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        flags_layer = bm.faces.layers.int.new("nvm_face_flags")
        obstacle_count_layer = bm.faces.layers.int.new("nvm_face_obstacle_count")

        # TODO: Is there any chance the face count could change, e.g. if some NVM faces were degenerate and ignored
        #  by Blender during BMesh construction?
        for f_i, face in enumerate(bm.faces):
            nvm_triangle = nvm.triangles[f_i]
            face[flags_layer] = nvm_triangle.flags
            face[obstacle_count_layer] = nvm_triangle.obstacle_count

        bm.to_mesh(bl_mesh)
        del bm

        if create_quadtree_boxes:
            self.create_nvm_quadtree(mesh_obj, nvm, import_info.bl_name)

        # TODO: Event entities?

        self.imported_models[import_info.model_file_stem] = mesh_obj

        if self.parent_obj:
            mesh_obj.parent = self.parent_obj

        return mesh_obj

    def create_nvm_quadtree(self, bl_mesh, nvm: NVM, bl_name: str) -> list[bpy.types.Object]:
        """Create box tree (depth first creation order).

        NOTE: These boxes should be imported for inspection only. They are automatically generated from the mesh
        min/max vertex coordinates on NVM export.
        """
        boxes = []
        for box, indices in nvm.get_all_boxes(nvm.root_box):
            if not indices:
                box_name = f"{bl_name} Box ROOT"
            else:
                indices_string = "-".join(str(i) for i in indices)
                box_name = f"{bl_name} Box {indices_string}"
            bl_box = self.create_box(box)
            bl_box.name = box_name
            boxes.append(bl_box)
            self.all_bl_objs.append(bl_box)
            bl_box.parent = bl_mesh
        return boxes

    @staticmethod
    def create_box(box: NVMBox):
        """Create an AABB prism representing `box`. Position is baked into mesh data fully, just like the navmesh."""
        start_vec = GAME_TO_BL_VECTOR(box.start_corner)
        end_vec = GAME_TO_BL_VECTOR(box.end_corner)
        bpy.ops.mesh.primitive_cube_add()
        bl_box = bpy.context.active_object
        # noinspection PyTypeChecker
        box_data = bl_box.data  # type: bpy.types.Mesh
        for vertex in box_data.vertices:
            vertex.co[0] = start_vec.x if vertex.co[0] == -1.0 else end_vec.x
            vertex.co[1] = start_vec.y if vertex.co[1] == -1.0 else end_vec.y
            vertex.co[2] = start_vec.z if vertex.co[2] == -1.0 else end_vec.z
        bpy.ops.object.modifier_add(type="WIREFRAME")
        bl_box.modifiers[0].thickness = 0.02
        return bl_box
