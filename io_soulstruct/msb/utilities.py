from __future__ import annotations

__all__ = [
    "find_flver_model",
    "BaseMSBEntrySelectOperator",
]

import abc
import re
import shutil
import tempfile
from pathlib import Path

import bpy
from io_soulstruct.exceptions import FLVERError, MissingPartModelError
from io_soulstruct.flver.models import BlenderFLVER
from io_soulstruct.general.cached import get_cached_file
from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities import *
from soulstruct.base.maps.msb import MSB, MSBEntry  # must not be imported under `TYPE_CHECKING` guard


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
        super().cancel(context)

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
    def _import_entry(self, context, entry: MSBEntry):
        """Subclass must implement this function to handle the chosen MSB entry."""
        ...
