from __future__ import annotations

__all__ = [
    "find_flver_model",
    "BaseMSBEntrySelectOperator",
    "batch_import_flver_models",
]

import abc
import re
import shutil
import tempfile
import time
import traceback
import typing as tp
from pathlib import Path

import bpy
from io_soulstruct.exceptions import FLVERError, MissingPartModelError
from io_soulstruct.flver.models import BlenderFLVER
from io_soulstruct.flver.image.image_import_manager import ImageImportManager
from io_soulstruct.general.cached import get_cached_file
from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities import *
from soulstruct.containers import Binder, BinderEntry
from soulstruct.base.maps.msb import MSB, MSBEntry  # must not be imported under `TYPE_CHECKING` guard
from soulstruct.base.models.flver import FLVER
from soulstruct.base.models.flver.mesh_tools import MergedMesh


def find_flver_model(model_name: str) -> BlenderFLVER:
    """Find the model of the given type in a 'Models' collection in the current scene.

    Used by Map Pieces, Collisions, and Navmeshes (assets stored per map).
    """
    model = find_obj(name=model_name, find_stem=True, soulstruct_type=SoulstructType.FLVER)
    if model is None:
        raise MissingPartModelError(f"FLVER model '{model_name}' not found in Blender data.")
    try:
        return BlenderFLVER(model)
    except FLVERError:
        raise MissingPartModelError(f"Blender object '{model_name}' is not a valid FLVER model mesh.")


class BaseMSBEntrySelectOperator(LoggingOperator):

    # Set by `invoke` when entry choices are written to temp directory.
    msb: MSB  # NOTE: must NOT be imported under `TYPE_CHECKING` guard, as Blender loads annotations

    temp_directory: bpy.props.StringProperty(
        name="Temp MSB Directory",
        description="Temporary directory containing MSB entry choices",
        default="",
        options={'HIDDEN'},
    )

    filter_glob: bpy.props.StringProperty(
        default="*",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Chosen MSB entry",
        maxlen=1024,
        subtype="FILE_PATH",
    )
    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: bpy.props.StringProperty(options={'HIDDEN'})

    ENTRY_NAME_RE = re.compile(r"\((\d+)\) (.+)")

    @classmethod
    @abc.abstractmethod
    def get_msb_list_names(cls, context) -> list[str]:
        """Subclass must implement this function to retrieve MSB list names to unpack and offer."""
        ...

    @classmethod
    def poll(cls, context):
        settings = cls.settings(context)
        try:
            settings.get_import_msb_path()
        except FileNotFoundError:
            return False
        return True

    def cancel(self, context):
        """Make sure we clear the directory even when cancelled."""
        if self.temp_directory:
            shutil.rmtree(self.temp_directory, ignore_errors=True)
            self.temp_directory = ""

    def invoke(self, context, event):
        """Unpack valid MSB entry choices to temp directory for user to select from."""
        if self.temp_directory:
            shutil.rmtree(self.temp_directory, ignore_errors=True)
            self.temp_directory = ""

        settings = self.settings(context)
        # We always use the latest MSB, if the setting is enabled.
        msb_path = settings.get_import_msb_path()  # will automatically use latest MSB version if known and enabled
        self.msb = get_cached_file(msb_path, settings.get_game_msb_class())

        entry_list_names = self.get_msb_list_names(context)
        if not entry_list_names:
            return self.error("No MSB entry list names set to select from.")

        self.temp_directory = tempfile.mkdtemp(suffix="_" + msb_path.stem)
        for entry_list_name in entry_list_names:
            entry_list = getattr(self.msb, entry_list_name)
            entry_list_dir = Path(self.temp_directory, entry_list_name)
            entry_list_dir.mkdir(exist_ok=True)
            for i, entry in enumerate(entry_list):
                # We use the index to ensure unique file names while allowing duplicate entry names (e.g. Regions).
                file_name = f"({i}) {entry.name}"
                file_path = entry_list_dir / file_name
                with file_path.open("w") as f:
                    f.write(entry.name)

        if len(entry_list_names) == 1:
            # Start inside sole subtype.
            self.directory = self.temp_directory + f"/{entry_list_names[0]}"
        else:
            # User chooses subtype directory first.
            self.directory = self.temp_directory
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        try:
            entry = self.get_selected_entry()
            if entry:
                self._import_entry(context, entry)
                return {"FINISHED"}
            return {"CANCELLED"}  # relevant error already reported
        finally:
            if self.temp_directory:
                shutil.rmtree(self.temp_directory, ignore_errors=True)
                self.temp_directory = ""

    def get_selected_entry(self) -> MSBEntry | None:
        if not getattr(self, "msb", None):
            self.error("No MSB loaded. Did you cancel the file selection?")
            return None

        path = Path(self.filepath)
        match = self.ENTRY_NAME_RE.match(path.stem)
        if not match:
            self.error(f"Selected file does not match expected format '(i) Name': {self.filepath}")
            return None

        entry_list_name = path.parent.name

        try:
            entry_list = getattr(self.msb, entry_list_name)
        except AttributeError:
            self.error(f"MSB entry list '{entry_list_name}' not found in MSB.")
            return None

        entry_id, entry_name = int(match.group(1)), match.group(2)
        if entry_id >= len(entry_list):
            self.error(
                f"Selected entry ID {entry_id} ('{entry_name}') is out of range for MSB entry list '{entry_list_name}'."
            )
            return None

        return entry_list[entry_id]

    @abc.abstractmethod
    def _import_entry(self, context: Context, entry: MSBEntry):
        """Subclass must implement this function to handle the chosen MSB entry."""
        ...


def batch_import_flver_models(
    operator: LoggingOperator,
    context: Context,
    flver_sources: dict[str, BinderEntry | Path],
    map_stem: str,
    part_subtype_title: str,
    flver_source_binders: dict[str, Binder] = None,
    image_import_callback: tp.Callable[[ImageImportManager, FLVER], None] = None,
):
    flver_import_settings = context.scene.flver_import_settings
    flver_source_binders = flver_source_binders or {}

    operator.info(f"Importing {len(flver_sources)} {part_subtype_title} FLVERs in parallel.")

    p = time.perf_counter()

    if all(isinstance(data, Path) for data in flver_sources.values()):
        flvers_list = FLVER.from_path_batch(list(flver_sources.values()))
    elif all(isinstance(data, BinderEntry) for data in flver_sources.values()):
        flvers_list = FLVER.from_binder_entry_batch(list(flver_sources.values()))
    else:
        raise ValueError("All FLVER model data for batch importing must be either `BinderEntry` or `Path` objects.")
    # Drop failed FLVERs immediately.
    flvers = {
        model_name: flver
        for model_name, flver in zip(flver_sources.keys(), flvers_list)
        if flver is not None
    }

    operator.info(f"Imported {len(flvers)} {part_subtype_title} FLVERs in {time.perf_counter() - p:.2f} seconds.")
    p = time.perf_counter()

    if flver_import_settings.import_textures:
        image_import_manager = ImageImportManager(operator, context)
        # Find textures for all loaded FLVERs.
        for model_name, flver in flvers.items():
            source_binder = flver_source_binders.get(model_name, None)
            image_import_manager.find_flver_textures(
                source_binder.path if source_binder else flver.path,
                source_binder,
            )
            if image_import_callback:
                image_import_callback(image_import_manager, flver)
    else:
        image_import_manager = None

    # Brief non-parallel excursion: create Blender materials and `MergedMesh` arguments for each `FLVER`.
    flver_bl_materials = {}
    flver_merged_mesh_args = []
    bl_materials_by_matdef_name = {}  # can re-use cache across all FLVERs!
    merge_submesh_vertices = flver_import_settings.merge_submesh_vertices
    for model_name, flver in flvers.items():
        bl_materials, submesh_bl_material_indices, bl_material_uv_layer_names = BlenderFLVER.create_materials(
            operator,
            context,
            flver,
            model_name,
            material_blend_mode=flver_import_settings.material_blend_mode,
            image_import_manager=image_import_manager,
            bl_materials_by_matdef_name=bl_materials_by_matdef_name,
        )
        flver_bl_materials[model_name] = bl_materials
        flver_merged_mesh_args.append(
            (submesh_bl_material_indices, bl_material_uv_layer_names, merge_submesh_vertices)
        )

    operator.info(
        f"Created materials for {len(flvers)} {part_subtype_title} FLVERs in {time.perf_counter() - p:.2f} seconds."
    )
    p = time.perf_counter()

    # Merge meshes in parallel. Empty meshes will be `None`.
    flver_merged_meshes_list = MergedMesh.from_flver_batch(list(flvers.values()), flver_merged_mesh_args)
    flver_merged_meshes = {  # nothing dropped
        model_name: merged_mesh
        for model_name, merged_mesh in zip(flvers.keys(), flver_merged_meshes_list)
    }

    operator.info(f"Merged {len(flvers)} {part_subtype_title} FLVERs in {time.perf_counter() - p:.2f} seconds.")
    p = time.perf_counter()

    if part_subtype_title in {"Character", "Object", "Asset", "Equipment"}:
        # Not map-specific.
        model_collection = get_or_create_collection(
            context.scene.collection,
            "Models",
            f"{part_subtype_title} Models",
        )
    else:
        model_collection = get_or_create_collection(
            context.scene.collection,
            f"{map_stem} Models",
            f"{map_stem} {part_subtype_title} Models",
        )
    for model_name, flver in flvers.items():
        try:
            BlenderFLVER.new_from_soulstruct_obj(
                operator,
                context,
                flver,
                name=model_name,
                image_import_manager=image_import_manager,
                collection=model_collection,
                merged_mesh=flver_merged_meshes[model_name],
                bl_materials=flver_bl_materials[model_name],
            )
        except Exception as ex:
            traceback.print_exc()  # for inspection in Blender console
            operator.error(f"Cannot import FLVER: {flver.path_name}. Error: {ex}")

    operator.info(f"Imported {len(flvers)} {part_subtype_title} FLVERs in {time.perf_counter() - p:.2f} seconds.")
