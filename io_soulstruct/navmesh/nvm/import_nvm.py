"""
Import NVM files (with/without DCX) into Blender 3.3+ (Python 3.10+ scripting required).

NVM files are just basic meshes that contain:
    - per-triangle obstacle counts and flags for AI navigation
    - a quaternary box tree containing all triangles in leaf nodes
    - event entity references that allow specific triangle flags to be toggled from EMEVD

This file format is only used in DeS and DS1 (PTDE/DSR).
"""
from __future__ import annotations

__all__ = ["ImportNVM", "ImportNVMWithBinderChoice", "QuickImportNVM"]

import time
import traceback
import typing as tp
from pathlib import Path

import bpy
import bmesh
from bpy_extras.io_utils import ImportHelper
from mathutils import Vector

from soulstruct.containers import Binder, BinderEntry, EntryNotFoundError
from soulstruct.darksouls1r.maps import MSB
from soulstruct.darksouls1r.maps.navmesh.nvm import NVM, NVMBox, NVMEventEntity

from io_soulstruct.utilities import *
from io_soulstruct.general import *
from io_soulstruct.general.cached import get_cached_file
from .utilities import *


class NVMImportInfo(tp.NamedTuple):
    """Holds information about a navmesh to import into Blender."""
    path: Path  # source file for NVM (likely a Binder path)
    model_file_stem: str  # generally stem of NVM file or Binder entry
    bl_name: str  # name to assign to Blender object (usually same as `model_file_stem`)
    nvm: NVM  # parsed NVM


class NVMImportChoiceInfo(tp.NamedTuple):
    """Holds information about a Binder entry choice that the user will make in deferred operator."""
    path: Path  # Binder path
    entries: list[BinderEntry]  # entries from which user must choose


class ImportNVMMixin:

    # Type hints for `LoggingOperator`.
    error: tp.Callable[[str], set[str]]
    warning: tp.Callable[[str], set[str]]
    info: tp.Callable[[str], set[str]]

    navmesh_model_id: int
    import_all_from_binder: bool

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

    def check_nvm_entry_model_id(self, nvm_entry: BinderEntry) -> bool:
        """Checks if the given NVM Binder entry matches the given navmesh model ID."""
        try:
            entry_model_id = int(nvm_entry.name[1:5])  # e.g. 'n1234' -> 1234
        except ValueError:
            return False  # not a match (weird NVM name)
        return entry_model_id == self.navmesh_model_id


class ImportNVM(LoggingOperator, ImportHelper, ImportNVMMixin):
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

        for file_path in file_paths:

            is_binder = NVMBND_NAME_RE.match(file_path.name) is not None

            if is_binder:
                binder = Binder.from_path(file_path)
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

        parent_obj = None

        importer = NVMImporter(
            self,
            context,
            use_linked_duplicates=False,
            parent_obj=parent_obj,
        )

        for import_info in import_infos:

            if isinstance(import_info, NVMImportChoiceInfo):
                # Defer through entry selection operator.
                ImportNVMWithBinderChoice.run(
                    importer=importer,
                    binder_file_path=import_info.path,
                    use_material=self.use_material,
                    create_quadtree_boxes=self.create_quadtree_boxes,
                    nvm_entries=import_info.entries,
                )
                continue

            self.info(f"Importing NVM model {import_info.model_file_stem} as '{import_info.bl_name}'.")

            # Import single NVM.
            try:
                importer.import_nvm(
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

        return {"FINISHED"}


# noinspection PyUnusedLocal
def get_binder_entry_choices(self, context):
    return ImportNVMWithBinderChoice.enum_options


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

        try:
            self.importer.import_nvm(
                import_info,
                use_material=self.use_material,
                create_quadtree_boxes=self.create_quadtree_boxes,
            )
        except Exception as ex:
            for obj in self.importer.all_bl_objs:
                bpy.data.objects.remove(obj)
            traceback.print_exc()
            return self.error(f"Cannot import NVM {nvm_model_name} from '{self.binder_file_path.name}'. Error: {ex}")

        return {"FINISHED"}

    @classmethod
    def run(
        cls,
        importer: NVMImporter,
        binder_file_path: Path,
        use_material: bool,
        create_quadtree_boxes: bool,
        nvm_entries: list[BinderEntry],
    ):
        cls.importer = importer
        cls.binder_file_path = binder_file_path
        cls.enum_options = [(str(i), entry.name, "") for i, entry in enumerate(nvm_entries)]
        cls.use_material = use_material
        cls.create_quadtree_boxes = create_quadtree_boxes
        cls.nvm_entries = nvm_entries
        # noinspection PyUnresolvedReferences
        bpy.ops.wm.nvm_binder_choice_operator("INVOKE_DEFAULT")


class QuickImportNVM(LoggingOperator):
    """Import a NVM from the current selected value of listed game map NVMs."""
    bl_idname = "import_scene.quick_nvm"
    bl_label = "Import NVM"
    bl_description = "Import selected NVM from game map directory's NVMBND binder"

    # TODO: Currently no way to change these property defaults in GUI.

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

    @classmethod
    def poll(cls, context):
        game_lists = context.scene.soulstruct_game_enums  # type: SoulstructGameEnums
        return game_lists.nvm not in {"", "0"}

    def execute(self, context):

        start_time = time.perf_counter()

        settings = SoulstructSettings.get_scene_settings(context)
        map_path = SoulstructSettings.get_selected_map_path(context)
        if not map_path:
            return self.error("Game directory and map stem must be set in Blender's Soulstruct global settings.")
        settings.save_settings()

        nvmbnd_dcx_type = settings.resolve_dcx_type("Auto", "Binder", False, context)
        nvmbnd_path = nvmbnd_dcx_type.process_path(map_path / f"{settings.map_stem}.nvmbnd")
        if settings.use_bak_file:
            nvmbnd_path = nvmbnd_path.with_name(nvmbnd_path.name + ".bak")
            if not nvmbnd_path.is_file():
                return self.error(f"Could not find NVMBND '.bak' file for map '{settings.map_stem}'.")
        if not nvmbnd_path.is_file():
            return self.error(f"Could not find NVMBND file for map '{settings.map_stem}': {nvmbnd_path}")

        transform = None  # type: tp.Optional[Transform]

        if settings.msb_import_mode:
            try:
                part_name, nvm_stem = context.scene.soulstruct_game_enums.nvm.split("|")
            except ValueError:
                return self.error("Invalid MSB navmesh selection.")
            msb_path = settings.get_selected_map_msb_path(context)

            # Get MSB part transform.
            msb = get_cached_file(msb_path, settings.get_game_msb_class(context))  # type: MSB
            navmesh_part = msb.navmeshes.find_entry_name(part_name)
            transform = Transform.from_msb_part(navmesh_part)

            dcx_type = settings.resolve_dcx_type("Auto", "NVM", False, context)
            nvm_entry_name = f"{nvm_stem}.nvm"
            nvm_entry_name = dcx_type.process_path(nvm_entry_name)
            bl_name = part_name
        else:
            nvm_entry_name = context.scene.soulstruct_game_enums.nvm
            bl_name = nvm_entry_name.split(".")[0]

        nvmbnd = Binder.from_path(nvmbnd_path)
        try:
            nvm_entry = nvmbnd.find_entry_name(nvm_entry_name)
        except EntryNotFoundError:
            return self.error(f"Could not find NVM entry '{nvm_entry_name}' in NVMBND file '{nvmbnd_path.name}'.")

        import_info = NVMImportInfo(
            nvmbnd_path, nvm_entry.minimal_stem, bl_name, nvm_entry.to_binary_file(NVM)
        )

        parent_obj = find_or_create_bl_empty(f"{map_path.stem} Navmeshes", context)

        importer = NVMImporter(
            self,
            context,
            use_linked_duplicates=False,
            parent_obj=parent_obj,
        )

        self.info(f"Importing NVM model {import_info.model_file_stem} as '{import_info.bl_name}'.")

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
            # Assign Model File Stem to navmesh.
            nvm_obj["Model File Stem"] = import_info.model_file_stem

        p = time.perf_counter() - start_time
        self.info(f"Finished importing NVM {nvm_entry_name} from {nvmbnd_path.name} in {p} s.")

        return {"FINISHED"}


class NVMImporter:
    """Manages imports for a batch of NVM files imported simultaneously."""

    nvm: NVM | None
    bl_name: str
    use_linked_duplicates: bool

    parent_obj: bpy.types.Object | None
    imported_models: dict[str, bpy.types.Object]  # model file stem -> Blender object

    def __init__(
        self,
        operator: LoggingOperator,
        context,
        use_linked_duplicates=False,
        parent_obj: bpy.types.Object | None = None,
    ):
        self.operator = operator
        self.context = context
        self.use_linked_duplicates = use_linked_duplicates

        self.parent_obj = parent_obj
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

        for f_i, face in enumerate(bm.faces):
            nvm_triangle = nvm.triangles[f_i]
            face[flags_layer] = nvm_triangle.flags
            face[obstacle_count_layer] = nvm_triangle.obstacle_count

        for event in nvm.event_entities:
            bl_event = self.create_event_entity(event, bm.faces, import_info.bl_name)
            self.context.scene.collection.objects.link(bl_event)
            self.all_bl_objs.append(bl_event)
            bl_event.parent = mesh_obj

        bm.to_mesh(bl_mesh)
        del bm

        if create_quadtree_boxes:
            self.create_nvm_quadtree(mesh_obj, nvm, import_info.bl_name)

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

    @staticmethod
    def create_event_entity(
        nvm_event_entity: NVMEventEntity, bm_faces: bmesh.types.BMFaceSeq | list[bmesh.types.BMFace], bl_nvm_name: str
    ):
        """Create an Empty child that just holds the ID and triangle indices of a NVM event entity.

        Object is placed at the centroid of the faces it references, but this is just for convenience, and does not
        affect export. The user should move the event around if they change the attached faces.
        """
        bl_event = bpy.data.objects.new(f"{bl_nvm_name} Event {nvm_event_entity.entity_id}", None)
        bl_event.empty_display_type = "CUBE"  # to distinguish it from node spheres

        # Get the average position of the faces.
        avg_pos = Vector((0, 0, 0))
        for i in nvm_event_entity.triangle_indices:
            avg_pos += bm_faces[i].calc_center_median()
        avg_pos /= len(nvm_event_entity.triangle_indices)
        bl_event.location = avg_pos

        bl_event["entity_id"] = nvm_event_entity.entity_id
        bl_event["triangle_indices"] = nvm_event_entity.triangle_indices
        return bl_event
