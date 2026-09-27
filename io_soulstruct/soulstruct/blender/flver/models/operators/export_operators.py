from __future__ import annotations

__all__ = [
    "ExportAnyFLVER",
    "ExportFLVERIntoAnyBinder",
    "ExportMapPieceFLVERs",
    "ExportCharacterFLVER",
    "ExportObjectFLVER",
    "ExportEquipmentFLVER",
]

import re
import traceback
import typing as tp
from pathlib import Path

import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty

from soulstruct.flver import FLVER
from soulstruct.containers import Binder, BinderEntry, EntryNotFoundError, TPF
from soulstruct.dcx import DCXType
from soulstruct.games import *

import pyrelink.core as pyre_core
import pyrelink.flver as pyre_flver

from ....base.operators import *
from ....base.register import io_soulstruct_operator
from ....exceptions import *
from ....general import *
from ...image import *
from ...image.export_operators import export_map_area_textures
from ..types import BlenderFLVER, FLVERModelType

if tp.TYPE_CHECKING:
    from ....type_checking import CHRBND_TYPING, OBJBND_TYPING, PARTSBND_TYPING


# region Generic Exporters

@io_soulstruct_operator
class ExportAnyFLVER(LoggingExportOperator):
    """Export one FLVER model from a Blender Armature parent to a file using a browser window."""
    bl_idname = "export_scene.flver"
    bl_label = "Export Any FLVER"
    bl_description = "Export Blender Armature/Mesh to a standalone FromSoftware FLVER model file"

    filename_ext = ".flver"

    filter_glob: StringProperty(
        default="*.flver;*.flver.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    dcx_type: get_dcx_enum_property()

    @classmethod
    def poll(cls, context) -> bool:
        """One FLVER Armature or Mesh object must be selected.

        If a Mesh is selected and it does not have an Armature parent object, a default FLVER skeleton with a single
        eponymous bone at the origin will be exported (which is fine for, e.g., most map pieces).
        """
        if not context.active_object:
            return False
        return BlenderFLVER.is_obj_type(context.active_object)

    def invoke(self, context, _event):
        """Set default export name to name of object (before first space and without Blender dupe suffix)."""
        if not context.active_object:
            return super().invoke(context, _event)

        bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        settings = self.settings(context)
        self.filepath = settings.game.process_dcx_path(f"{bl_flver.game_name}.flver")
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        try:
            bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        except SoulstructTypeError as ex:
            return self.error(str(ex))
        settings = self.settings(context)

        # Standard game DCX (unless overridden by this operator) applies to loose FLVER files.
        dcx_type = settings.resolve_dcx_type(self.dcx_type, "flver")

        flver_file_path = Path(self.filepath)  # set by user
        self.to_object_mode(context)

        try:
            # No textures collected and FLVER model type unknown (will be guessed).
            flver = bl_flver.to_soulstruct_obj(self, context, flver_model_type=FLVERModelType.Unknown)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot get exported FLVER. Error: {ex}")

        if isinstance(flver, pyre_flver.FLVER):
            flver.dcx_type = pyre_core.DCXType(dcx_type.value)  # pyrelink DCXType
        else:
            flver.dcx_type = dcx_type  # soulstruct DCXType

        try:
            # Will create a `.bak` file automatically if absent.
            if isinstance(flver, pyre_flver.FLVER):
                written_paths = [flver.write_to_path(flver_file_path)]  # pyrelink only returns one Path
            else:  # soulstruct
                written_paths = flver.write(flver_file_path)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write exported FLVER. Error: {ex}")
        self.info(f"Exported FLVER to: {str(written_paths[0])}")

        return {"FINISHED"}


@io_soulstruct_operator
class ExportFLVERIntoAnyBinder(LoggingImportOperator):
    """Export a single FLVER model from a Blender mesh into a chosen game binder (BND/BHD).

    TODO: Does not support Binders with multiple FLVERs yet (e.g. some OBJBNDs).
    """
    bl_idname = "export_scene.flver_binder"
    bl_label = "Export FLVER Into Any Binder"
    bl_description = "Export a FLVER model file into a FromSoftware Binder (BND/BHD)"

    filter_glob: StringProperty(
        default="*.chrbnd;*.chrbnd.dcx;*.objbnd;*.objbnd.dcx;*.geombnd;*.geombnd.dcx;*.partsbnd;*.partsbnd.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    # DCX type to apply to entries, not Binder.
    dcx_type: get_dcx_enum_property(default=DCXType.Null)

    overwrite_existing: BoolProperty(
        name="Overwrite Existing Entry",
        description="Overwrite first existing '.flver{.dcx}' entry in Binder",
        default=True,
    )

    default_entry_id: IntProperty(
        name="Default ID",
        description="Binder entry ID to use if a '.flver{.dcx}' entry does not already exist in Binder. If left as -1, "
                    "an existing entry MUST be found, or export will fail",
        default=-1,  # TODO: default can very likely be set to 200 across all games
        min=-1,
    )

    default_entry_flags: IntProperty(
        name="Default Flags",
        description="Flags to set to Binder FLVER entry if it needs to be created",
        default=0x2,
    )

    default_entry_path: StringProperty(
        name="Default Path",
        description="Path to use for Binder FLVER entry if it needs to be created. Use {name} as a format "
                    "placeholder for the stem of the exported FLVER. Default is for DS1R `chrbnd.dcx` binders",
        default="N:\\FRPG\\data\\INTERROOT_x64\\chr\\{name}\\{name}.flver",
    )

    @classmethod
    def poll(cls, context) -> bool:
        """At least one Blender mesh selected."""
        if not context.active_object:
            return False
        return BlenderFLVER.is_obj_type(context.active_object)

    def execute(self, context):
        try:
            bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        except SoulstructTypeError as ex:
            return self.error(str(ex))

        # Automatic DCX for FLVERs in Binders is Null.
        dcx_type = DCXType.from_member_name(self.dcx_type) if self.dcx_type != "AUTO" else DCXType.Null

        self.to_object_mode(context)
        binder_file_path = Path(self.filepath)
        # TODO: Use pyrelink Binder if enabled.
        try:
            binder = Binder.from_path(binder_file_path)
        except Exception as ex:
            return self.error(f"Could not load Binder file '{binder_file_path}'. Error: {ex}.")

        # Check for FLVER entry before doing any exporting.
        flver_entries = binder.find_entries_by_name_regex(r".*\.flver(\.dcx)?")
        if not flver_entries:
            if self.default_entry_id == -1:
                return self.error("No FLVER files found in Binder and default entry ID was left as -1.")
            flver_entry = binder.set_default_entry(
                entry_spec=self.default_entry_id,
                new_path=self.default_entry_path.format(name=bl_flver.game_name),
                new_flags=self.default_entry_flags,
            )  # no data yet
            if flver_entry.data and not self.overwrite_existing:
                return self.error(
                    f"Binder entry {self.default_entry_id} already exists in Binder and overwrite is disabled."
                )
        else:
            if not self.overwrite_existing:
                return self.error("FLVER file already exists in Binder and overwrite is disabled.")

            if len(flver_entries) > 1:
                # Look for FLVER with matching name.
                for entry in flver_entries:
                    if entry.stem == bl_flver.game_name:
                        self.info(
                            f"Multiple FLVER files found in Binder. Replacing entry with matching stem: "
                            f"{bl_flver.game_name}"
                        )
                        flver_entry = entry
                        break
                else:
                    return self.error(
                        f"Multiple FLVER files found in Binder, none of which have stem '{bl_flver.game_name}'. "
                        f"Change the start of your exported object's name or erase one or more existing FLVERs first."
                    )
            else:
                flver_entry = flver_entries[0]

        try:
            # No texture collection and FLVER model type unknown (will be guessed).
            flver = bl_flver.to_soulstruct_obj(self, context, flver_model_type=FLVERModelType.Unknown)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot create exported FLVER from Blender Mesh '{bl_flver.name}'. Error: {ex}")

        if isinstance(flver, pyre_flver.FLVER):
            flver.dcx_type = pyre_core.DCXType(dcx_type.value)  # pyrelink DCXType
        else:
            flver.dcx_type = dcx_type  # soulstruct DCXType

        try:
            if isinstance(flver, pyre_flver.FLVER):
                # TODO: Still using soulstruct Binder at the moment, so convert to bytes here.
                flver_entry.set_uncompressed_data(flver.to_bytes())
            else:  # soulstruct
                flver_entry.set_from_binary_file(flver)  # DCX will default to `None` here from exporter function
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write exported FLVER. Error: {ex}")

        try:
            # Will create a `.bak` file automatically if absent.
            written_path = binder.write()
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write Binder with new FLVER. Error: {ex}")

        self.info(f"Exported FLVER into Binder file: {written_path}")

        return {"FINISHED"}

# endregion


# region Type-Specific Game Exporters and Operators

@io_soulstruct_operator
class ExportMapPieceFLVERs(LoggingOperator):
    bl_idname = "export_scene.map_piece_flver"
    bl_label = "Export Map Pieces"
    bl_description = (
        "Export selected Blender armatures/meshes to map piece FLVER model files in appropriate game map(s)"
    )

    @classmethod
    def poll(cls, context) -> bool:
        """One or more 'm*' Armatures or Meshes selected."""
        if not cls.settings(context).can_auto_export or not context.selected_objects:
            return False
        for obj in context.selected_objects:
            if not BlenderFLVER.is_obj_type(obj):
                return False
        return True

    def execute(self, context):
        try:
            bl_flvers = BlenderFLVER.get_selected_flvers(context, sort=True)
        except FLVERError as ex:
            return self.error(str(ex))

        settings = self.settings(context)

        # TODO: Later games (e.g. Elden Ring) use Binders like 'mapbnd' for map pieces, but this is not yet supported.
        #  This assumes loose FLVERs in the map folder. MAPBND support will require insertion into existing MAPBNDs,
        #  as the `.grass` files inside them will be left untouched.
        if not settings.map_stem and not settings.auto_detect_export_map:
            return self.error(
                "No game map directory specified in Soulstruct settings and `Detect Map from Collection` is disabled."
            )

        flver_export_settings = context.scene.flver_export_settings
        flver_dcx_type = settings.resolve_dcx_type("AUTO", "flver")

        self.to_object_mode(context)
        active_object = context.active_object  # to restore later

        map_area_textures = {}  # maps area stems 'mAA' to dictionaries of Blender images to export

        all_exported_paths = []

        for bl_flver in bl_flvers:

            map_stem = settings.get_map_stem_for_export(bl_flver.mesh, oldest=True)

            if not map_stem:
                self.error(
                    f"Cannot detect a map stem for `{bl_flver.name}` (and none set in settings)."
                )
                continue

            relative_map_path = Path(f"map/{map_stem}")
            texture_collection = DDSTextureCollection()

            try:
                # We also pass the model name as the default bone name.
                flver = bl_flver.to_soulstruct_obj(
                    self,
                    context,
                    texture_collection,
                    flver_model_type=FLVERModelType.MapPiece,
                )
            except Exception as ex:
                traceback.print_exc()
                return self.error(
                    f"Cannot export Map Piece FLVER '{bl_flver.game_name}' from '{bl_flver.name}'. Error: {ex}"
                )

            if isinstance(flver, pyre_flver.FLVER):
                flver.dcx_type = pyre_core.DCXType(flver_dcx_type.value)  # pyrelink DCXType
            else:
                flver.dcx_type = flver_dcx_type  # soulstruct DCXType
            relative_flver_path = relative_map_path / f"{bl_flver.game_name}.flver"
            exported_paths = settings.export_file(self, flver, relative_flver_path)
            all_exported_paths += exported_paths

            if flver_export_settings.export_textures:
                # Collect all Blender images for batched map area export.
                area = settings.map_stem[:3]
                area_textures = map_area_textures.setdefault(area, DDSTextureCollection())
                area_textures |= texture_collection

            if (
                settings.is_game(GameType.DemonsSouls)
                and relative_flver_path.name.endswith(".dcx")
                and settings.demonssouls.export_debug_files
            ):
                # DeS loose FLVER has DCX by default, but we want a non-DCX Map Piece too.
                for export_path in exported_paths:
                    non_dcx_path = settings.create_non_dcx_file(export_path)
                    all_exported_paths.append(non_dcx_path)
                    self.info(f"Also exported non-DCX Map Piece FLVER to: {str(non_dcx_path)}")

        if map_area_textures:  # only non-empty if texture export enabled
            for map_area, texture_collection in map_area_textures.items():
                all_exported_paths += export_map_area_textures(self, context, map_area, texture_collection)

        # Select original active object.
        if active_object:
            context.view_layer.objects.active = active_object

        return {"FINISHED" if all_exported_paths else "CANCELLED"}


class BaseGameFLVERBinderExportOperator(LoggingOperator):
    """Base class for operator that exports a FLVER directly into game Binder (MAPBND, CHRBND, OBJBND, PARTSBND)."""

    @staticmethod
    def _get_binder_path(settings: SoulstructSettings, model_stem: str) -> Path:
        raise NotImplementedError

    @tp.overload
    def get_binder_and_flver(
        self,
        context: bpy.types.Context,
        settings: SoulstructSettings,
        binder_class: type[CHRBND_TYPING],
        flver_model_type: FLVERModelType,
    ) -> tuple[str, CHRBND_TYPING, FLVER | pyre_flver.FLVER, DDSTextureCollection]:
        ...

    @tp.overload
    def get_binder_and_flver(
        self,
        context: bpy.types.Context,
        settings: SoulstructSettings,
        binder_class: type[OBJBND_TYPING],
        flver_model_type: FLVERModelType,
    ) -> tuple[str, OBJBND_TYPING, FLVER | pyre_flver.FLVER, DDSTextureCollection]:
        ...

    @tp.overload
    def get_binder_and_flver(
        self,
        context: bpy.types.Context,
        settings: SoulstructSettings,
        binder_class: type[PARTSBND_TYPING],
        flver_model_type: FLVERModelType,
    ) -> tuple[str, PARTSBND_TYPING, FLVER | pyre_flver.FLVER, DDSTextureCollection]:
        ...

    def get_binder_and_flver(
        self,
        context: bpy.types.Context,
        settings: SoulstructSettings,
        binder_class: type[CHRBND_TYPING | OBJBND_TYPING | PARTSBND_TYPING],
        flver_model_type: FLVERModelType,
    ) -> tuple[str, CHRBND_TYPING | OBJBND_TYPING | PARTSBND_TYPING, FLVER | pyre_flver.FLVER, DDSTextureCollection]:
        """Export FLVER from Blender object and return Binder, FLVER, and texture collection.

        NOTE: Returned Binder does not load FLVER entries automatically (and they typically aren't needed).
        """
        bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        cls_name = binder_class.__name__

        # We prepare and retrieve the Binder to be exported into. If a project Binder already exists, it will be used
        # as the initial Binder to modify. The user should delete this Binder if they, e.g., want to start fresh with
        # the textures and other files from the game directory's Binder.
        relative_binder_path = self._get_binder_path(settings, bl_flver.game_name)
        try:
            binder = settings.get_initial_binder(self, relative_binder_path, binder_class)
        except Exception as ex:
            raise FLVERExportError(
                f"Cannot find {cls_name} binder for {bl_flver.name}: '{relative_binder_path}'. Error: {ex}"
            )

        self.to_object_mode(context)
        texture_collection = DDSTextureCollection()
        try:
            flver = bl_flver.to_soulstruct_obj(
                self,
                context,
                texture_collection=texture_collection,
                flver_model_type=flver_model_type,
            )
        except Exception as ex:
            traceback.print_exc()
            raise FLVERExportError(
                f"Cannot create exported FLVER '{bl_flver.game_name}' from Mesh '{bl_flver.name}'. Error: {ex}"
            )

        if isinstance(flver, pyre_flver.FLVER):
            flver.dcx_type = pyre_core.DCXType.Null  # no DCX inside any Binder here
        else:
            flver.dcx_type = DCXType.Null  # no DCX inside any Binder here

        return bl_flver.game_name, binder, flver, texture_collection

    @staticmethod
    def _get_binder_stem(model_stem: str) -> str:
        """Get the stem of the Binder that FLVER `model_stem` belongs in. Only needs overriding for Binders that can
        hold multiple FLVERs, whose extra FLVERs have suffixes like '_1' (e.g. `WP_A_0204_1` weapon sheath)."""
        return model_stem

    def export_flver_group_into_binder(
        self,
        context: bpy.types.Context,
        settings: SoulstructSettings,
        binder_class: type[OBJBND_TYPING | PARTSBND_TYPING],
        flver_model_type: FLVERModelType,
    ) -> tuple[str, OBJBND_TYPING | PARTSBND_TYPING, list[str], DDSTextureCollection]:
        """Export the active FLVER AND any other FLVERs belonging to the same multi-FLVER Binder into that Binder.

        Binders like PARTSBND and OBJBND can hold extra FLVERs, named with suffixes like '_1', which are imported as
        separate Blender FLVERs (e.g. `WP_A_0204_1`, the sheath of weapon `WP_A_0204`). Each FLVER is written into
        its own existing Binder entry (matched by name), or into a new entry with the next free ID, and exporting any
        member of the group also exports its siblings (see `_get_flver_group()`) so their edits are not lost.

        Returns `(binder_stem, binder, exported_model_stems, texture_collection)`.
        """
        bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        binder_stem = self._get_binder_stem(bl_flver.game_name)
        bl_flvers = self._get_flver_group(context, bl_flver, binder_stem)
        cls_name = binder_class.__name__

        relative_binder_path = self._get_binder_path(settings, binder_stem)
        try:
            binder = settings.get_initial_binder(self, relative_binder_path, binder_class)
        except Exception as ex:
            raise FLVERExportError(
                f"Cannot find {cls_name} binder for {bl_flver.name}: '{relative_binder_path}'. Error: {ex}"
            )

        self.to_object_mode(context)
        texture_collection = DDSTextureCollection()  # shared by all FLVERs (keyed by texture stem)
        exported_model_stems = []
        for group_bl_flver in bl_flvers:
            try:
                flver = group_bl_flver.to_soulstruct_obj(
                    self,
                    context,
                    texture_collection=texture_collection,
                    flver_model_type=flver_model_type,
                )
            except Exception as ex:
                traceback.print_exc()
                raise FLVERExportError(
                    f"Cannot create exported FLVER '{group_bl_flver.game_name}' from Mesh '{group_bl_flver.name}'. "
                    f"Error: {ex}"
                )
            self._set_flver_binder_entry(binder, group_bl_flver.game_name, flver)
            exported_model_stems.append(group_bl_flver.game_name)

        if len(exported_model_stems) > 1:
            self.info(f"Exported {len(exported_model_stems)} FLVERs into {cls_name}: {', '.join(exported_model_stems)}")

        return binder_stem, binder, exported_model_stems, texture_collection

    def _get_flver_group(
        self, context: bpy.types.Context, bl_flver: BlenderFLVER, binder_stem: str
    ) -> list[BlenderFLVER]:
        """Get `bl_flver` (first) and every other Blender FLVER that belongs in Binder `binder_stem`, as found among
        selected objects and objects in the same collection(s) as `bl_flver`. Selected FLVERs take priority over
        unselected ones if multiple Blender FLVERs have the same game name.
        """
        group = {bl_flver.game_name.lower(): bl_flver}

        def _candidates(objs) -> list[BlenderFLVER]:
            found = {}
            for obj in objs:
                try:
                    candidate = BlenderFLVER.from_armature_or_mesh(obj)
                except SoulstructTypeError:
                    continue
                if self._get_binder_stem(candidate.game_name).lower() != binder_stem.lower():
                    continue
                found.setdefault(candidate.mesh.name, candidate)
            return list(found.values())

        selected = _candidates(context.selected_objects)
        collection_objs = [obj for coll in bl_flver.mesh.users_collection for obj in coll.objects]
        unselected = [c for c in _candidates(collection_objs) if c.mesh.name not in {s.mesh.name for s in selected}]

        for candidates in (selected, unselected):
            by_name = {}
            for candidate in candidates:
                by_name.setdefault(candidate.game_name.lower(), []).append(candidate)
            for name, name_candidates in by_name.items():
                if name in group:
                    continue  # already have a (higher priority) FLVER with this name
                if len(name_candidates) > 1:
                    self.warning(
                        f"Found multiple Blender FLVERs for '{name_candidates[0].game_name}' in Binder "
                        f"'{binder_stem}': {', '.join(c.name for c in name_candidates)}. Not exporting any of them. "
                        f"Select the one you want to export with '{bl_flver.name}'."
                    )
                    continue
                group[name] = name_candidates[0]

        return list(group.values())

    def _set_flver_binder_entry(self, binder: Binder, model_stem: str, flver: FLVER | pyre_flver.FLVER):
        """Write `flver` into the Binder entry named `{model_stem}.flver[.dcx]`, or create a new entry for it with the
        next free ID after any existing FLVER entries.

        We do NOT use `FLVERBinder.set_flver()` here: on write, that assigns managed FLVERs to entry IDs 200, 201, ...
        in sorted name order, so a lone '_1' FLVER would overwrite the Binder's main FLVER in entry 200.
        """
        if isinstance(flver, pyre_flver.FLVER):
            flver.dcx_type = pyre_core.DCXType.Null  # no DCX inside any Binder here
        else:
            flver.dcx_type = DCXType.Null  # no DCX inside any Binder here

        flver_entries = binder.find_entries_by_name_regex(r".*\.flver(\.dcx)?", flags=re.IGNORECASE)
        matching_entries = [
            entry for entry in flver_entries
            if re.fullmatch(rf"{re.escape(model_stem)}\.flver(\.dcx)?", entry.name, flags=re.IGNORECASE)
        ]
        if len(matching_entries) > 1:
            raise FLVERExportError(f"Multiple FLVER entries named '{model_stem}' found in Binder '{binder.path}'.")
        if matching_entries:
            flver_entry = matching_entries[0]
        else:
            used_ids = {entry.entry_id for entry in binder.entries}
            entry_id = max(
                (entry.entry_id for entry in flver_entries), default=binder.FLVER_FIRST_ENTRY_ID - 1
            ) + 1
            while entry_id in used_ids:
                entry_id += 1
            flver_entry = BinderEntry(
                data=b"",  # filled below
                entry_id=entry_id,
                path=binder.get_flver_entry_path(model_stem),
                flags=0x2,
            )
            binder.add_entry(flver_entry)
            self.info(f"Created new Binder entry {entry_id} for FLVER '{model_stem}': {flver_entry.path}")

        if isinstance(flver, pyre_flver.FLVER):
            # TODO: Still using soulstruct Binder at the moment, so convert to bytes here.
            flver_entry.set_uncompressed_data(flver.to_bytes())
        else:
            flver_entry.set_from_binary_file(flver)

    def export_textures_to_binder_tpf(
        self,
        context,
        binder: CHRBND_TYPING | OBJBND_TYPING | PARTSBND_TYPING,
        texture_collection: DDSTextureCollection,
        exported_model_stems: tp.Sequence[str] = (),
    ) -> TPF | None:
        """Replace the Binder's TPF with the textures in `texture_collection`.

        If `exported_model_stems` is given and the Binder contains other FLVERs that were not just exported, textures
        in the existing TPF that are not being replaced are kept, as those other FLVERs may still use them.
        """
        multi_tpf = texture_collection.to_multi_texture_tpf(
            self,
            context,
            enforce_max_chrbnd_tpf_size=binder.cls_name == "CHRBND",
            find_same_format=None,  # TODO: Get existing textures to resolve 'SAME' option for DDS format
        )
        if multi_tpf is None:
            return None  # textures exceeded bundled CHRBND capacity; handled by caller (game-specific)

        if exported_model_stems:
            exported = {stem.lower() for stem in exported_model_stems}
            flver_entry_stems = [
                entry.name.split(".")[0]
                for entry in binder.find_entries_by_name_regex(r".*\.flver(\.dcx)?", flags=re.IGNORECASE)
            ]
            other_flver_stems = [stem for stem in flver_entry_stems if stem.lower() not in exported]
            if other_flver_stems and binder.tpf is not None:
                new_stems = {texture.stem.lower() for texture in multi_tpf.textures}
                kept = [texture for texture in binder.tpf.textures if texture.stem.lower() not in new_stems]
                multi_tpf.textures.extend(kept)
                if kept:
                    self.info(
                        f"Kept {len(kept)} existing textures in {binder.cls_name} TPF, as it also contains FLVERs "
                        f"that were not exported: {', '.join(other_flver_stems)}"
                    )

        multi_tpf.dcx_type = DCXType.Null  # never DCX inside these Binders
        binder.tpf = multi_tpf  # will replace existing TPF
        self.info(f"Exported {len(multi_tpf.textures)} textures into multi-texture TPF in {binder.cls_name}.")
        return multi_tpf


@io_soulstruct_operator
class ExportCharacterFLVER(BaseGameFLVERBinderExportOperator):
    """Export a single FLVER model from a Blender mesh into same-named CHRBND in the game directory."""
    bl_idname = "export_scene.character_flver"
    bl_label = "Export Character"
    bl_description = "Export a FLVER model file into same-named game CHRBND (which must exist)"

    @staticmethod
    def _get_binder_path(settings: SoulstructSettings, model_stem: str) -> Path:
        if settings.is_game(GameType.DemonsSouls):
            # Nested inside character subfolder.
            return Path(f"chr/{model_stem}/{model_stem}.chrbnd")
        # Not in subfolder.
        return Path(f"chr/{model_stem}.chrbnd")

    @classmethod
    def poll(cls, context) -> bool:
        """Must have an Armature parent for a character FLVER. No chance of a default skeleton!

        Name of character must also start with 'c'.
        """
        if not cls.settings(context).can_auto_export or not context.active_object:
            return False
        try:
            bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        except SoulstructTypeError:
            return False
        if not bl_flver.armature:
            # Character MUST have an Armature.
            return False
        return bl_flver.name.startswith("c")

    def execute(self, context):
        settings = self.settings(context)

        try:
            chrbnd_class = settings.game.from_game_submodule_import(
                "models.chrbnd", "CHRBND"
            )  # type: type[CHRBND_TYPING]
            model_stem, chrbnd, flver, textures = self.get_binder_and_flver(
                context,
                settings,
                chrbnd_class,
                flver_model_type=FLVERModelType.Character,
            )
        except FLVERExportError as ex:
            return self.error(str(ex))

        # TODO: Currently this works for pyrelink FLVER because ultimately `chrbnd._flvers` exist only
        #  to have `bytes(flver)` called on them to convert to entries, which pyrelink `GameFile` bindings support.
        #  However, for simplicity, these export functions can just use a straightforward `Binder` instance anyway.
        chrbnd.set_flver(model_stem, flver)

        relative_chrbnd_path = self._get_binder_path(settings, model_stem)

        def _do_export() -> set[str]:
            exported_paths = settings.export_file(self, chrbnd, relative_chrbnd_path)

            if (
                settings.is_game(GameType.DemonsSouls)
                and settings.demonssouls.export_debug_files
            ):
                if chrbnd.dcx_type != DCXType.Null:
                    # Export non-DCX CHRBND too.
                    for exported_chrbnd_path in exported_paths:
                        non_dcx_path = settings.create_non_dcx_file(exported_chrbnd_path)
                        self.info(f"Also exported non-DCX CHRBND to: {str(non_dcx_path)}")
                # Export loose non-DCX FLVER next to CHRBND too.
                flver_path = relative_chrbnd_path.with_name(f"{model_stem}.flver")
                exported_paths += settings.export_file(self, flver, flver_path)

            return {"FINISHED" if exported_paths else "CANCELLED"}

        flver_export_settings = context.scene.flver_export_settings
        if not flver_export_settings.export_textures:
            # Export CHRBND now with FLVER.
            return _do_export()

        self.info("Exporting Blender textures into CHRBND...")

        # Export textures. This may or may not involve file(s) outside the CHRBND, depending on the game.
        multi_tpf, post_export_action = self.get_export_textures_action(
            context,
            settings,
            chrbnd,
            model_stem,
            textures,
        )

        if _do_export() == {"CANCELLED"}:
            return self.error("CHRBND export failed. Not exporting textures.")

        if post_export_action:
            # Only do this if CHRBND export was successful, as it may create/delete adjacent files/folders.
            post_export_action()

        if (
            settings.is_game(GameType.DemonsSouls)
            and settings.demonssouls.export_debug_files
            and multi_tpf is not None
        ):
            # Export non-DCX TPF next to CHRBND too.
            tpf_path = relative_chrbnd_path.with_name(f"{model_stem}.tpf")
            settings.export_file(self, multi_tpf, tpf_path)
            self.info(f"Also exported non-DCX TPF to: {str(tpf_path)}")

        return {"FINISHED"}  # CHRBND write definitely already succeeded

    def get_export_textures_action(
        self,
        context,
        settings: SoulstructSettings,
        chrbnd: CHRBND_TYPING,
        model_stem: str,
        texture_collection: DDSTextureCollection,
    ) -> tuple[TPF | None, tp.Callable[[], list[Path]] | None]:
        """Returns (binder_tpf | None, post-export action) tuple."""

        multi_tpf = self.export_textures_to_binder_tpf(
            context,
            chrbnd,
            texture_collection,
        )

        if settings.is_game(GameType.DarkSoulsPTDE):

            relative_tpf_dir_path = Path(f"chr/{model_stem}")

            if multi_tpf is not None:

                def post_export_action() -> list[Path]:
                    if project_root := settings.project_root:
                        export_dir = project_root.get_dir_path_if_exists(relative_tpf_dir_path)
                        if export_dir:
                            # Delete loose TPF folder (in favor of new Binder TPF).
                            export_dir.rmdir()
                    if settings.also_export_to_game and (game_root := settings.game_root):
                        import_dir = game_root.get_dir_path_if_exists(relative_tpf_dir_path)
                        if import_dir:
                            import_dir.rmdir()

                    return []  # no new files exported

                return multi_tpf, post_export_action

            # Otherwise, create loose folder with individual TPFs.
            paths_and_tpfs = texture_collection.to_single_texture_tpfs(
                self,
                DCXType.Null,  # no DCX in PTDE
                find_same_format=None,  # TODO
            )
            # Remove DDS conversion failure cases.
            valid_paths_and_tpfs = [x for x in paths_and_tpfs if x is not None]  # type: list[tuple[Path, TPF]]

            def post_export_action() -> list[Path]:
                exported_tpf_paths = []
                if valid_paths_and_tpfs:
                    for tpf_path, tpf in valid_paths_and_tpfs:
                        # TPF `path` already set correctly to name.
                        exported_tpf_paths += settings.export_file(self, tpf, relative_tpf_dir_path / tpf_path.name)
                    self.info(
                        f"Exported {len(valid_paths_and_tpfs)} textures into loose character TPF folder '{model_stem}'."
                    )

                return exported_tpf_paths

            return None, post_export_action

        elif settings.is_game(GameType.DarkSoulsDSR):

            relative_chrtpfbdt_path = Path(f"chr/{model_stem}.chrtpfbdt")  # no DCX

            if multi_tpf is not None:
                try:
                    # Remove old CHRTPFBHD header entry (in favor of new TPF).
                    chrbnd.remove_entry_name(f"{model_stem}.chrtpfbhd")
                except EntryNotFoundError:
                    pass

                def post_export_action() -> list[Path]:
                    if root := settings.project_root:
                        export_path = root.get_file_path_if_exists(relative_chrtpfbdt_path)
                        if export_path:
                            # Delete CHRTPFBDT (in favor of new TPF).
                            export_path.unlink()
                    if settings.also_export_to_game and (root := settings.game_root):
                        import_path = root.get_file_path_if_exists(relative_chrtpfbdt_path)
                        if import_path:
                            import_path.unlink()

                    return []  # no new files exported

                return None, post_export_action

            # Otherwise, create CHRTPFBXF. This method will put the header in `chrbnd`.
            chrtpfbdt_bytes, entry_count = self.create_chrtpfbxf(
                context, settings, chrbnd, model_stem, texture_collection
            )

            def post_export_action() -> list[Path]:
                if chrtpfbdt_bytes:
                    exported_chrtpfbdt_paths = settings.export_file_data(
                        self, chrtpfbdt_bytes, relative_chrtpfbdt_path, "CHRTPFBDT"
                    )
                    self.info(
                        f"Exported {entry_count} textures into split CHRTPFBHD (in CHRBND) and adjacent CHRTPFBDT."
                    )

                    return exported_chrtpfbdt_paths

                return []

            return None, post_export_action

        self.warning(f"Cannot handled CHRBND 'overflow' texture export for game {settings.game.name}.")
        return None, None

    def create_chrtpfbxf(
        self,
        context,
        settings: SoulstructSettings,
        chrbnd: CHRBND_TYPING,
        model_stem: str,
        texture_collection: DDSTextureCollection,
    ) -> tuple[bytes, int]:
        """Create CHRTPFBXF, put its header into CHRBND, and return the split data as bytes, along with entry count."""
        chrtpfbhd_entry_name = f"{model_stem}.chrtpfbhd"  # no DCX

        # TODO: Get existing textures to resolve 'SAME' option for DDS format.
        chrtpfbxf = texture_collection.to_tpfbhd(
            self,
            context,
            tpf_dcx_type=settings.game.get_dcx_type("tpf"),
            entry_path_parent=f"\\{model_stem}\\",
        )
        chrtpfbxf.dcx_type = DCXType.Null  # no DCX

        try:
            chrtpfbhd_entry = chrbnd[chrtpfbhd_entry_name]
        except EntryNotFoundError:
            try:
                chrtpfbhd_entry_id = getattr(chrbnd, "CHRTPFBHD_ENTRY_ID")
            except AttributeError:
                self.warning(f"Cannot create a new CHRTPFBHD entry for game {settings.game}.")
                return b"", 0

            chrtpfbhd_entry = BinderEntry(
                data=b"",  # filled below
                entry_id=chrtpfbhd_entry_id,
                path=chrbnd.get_chrtpfbhd_entry_path(model_stem),
                flags=0x2,
            )
            chrbnd.add_entry(chrtpfbhd_entry)

        packed_bhd, packed_bdt = chrtpfbxf.get_split_bytes()
        chrtpfbhd_entry.set_uncompressed_data(packed_bhd)
        return packed_bdt, len(chrtpfbxf.entries)


@io_soulstruct_operator
class ExportObjectFLVER(BaseGameFLVERBinderExportOperator):
    """Export a FLVER model from a Blender mesh into same-named OBJBND in the game directory.

    If the Blender object name has an underscore in it, the string before that underscore will be used to find the
    OBJBND (which supports multiple FLVERs). Each FLVER is written into its own existing Binder entry (e.g. `o0100_1`
    into the `o0100_1.flver` entry 201 of `o0100.objbnd`) or a new entry with the next free ID. All other FLVERs for the
    same OBJBND that are selected or in the same collection are exported with it.
    """
    bl_idname = "export_scene.object_flver"
    bl_label = "Export Object"
    bl_description = "Export a FLVER model file into same-named game OBJBND (which must exist)"

    @staticmethod
    def _get_binder_stem(model_stem: str) -> str:
        """We split on underscore, as OBJBNDs can contain multiple FLVERs with suffices like '_1'."""
        return model_stem.split("_")[0]

    @staticmethod
    def _get_binder_path(settings: SoulstructSettings, model_stem: str) -> Path:
        return Path(f"obj/{model_stem.split('_')[0]}.objbnd")

    @classmethod
    def poll(cls, context) -> bool:
        """Name of model must also start with 'o'.

        NOTE: Armature is NOT required. Could easily have Map Piece-like, non-animated Objects.
        """
        if not cls.settings(context).can_auto_export or not context.active_object:
            return False
        try:
            bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        except SoulstructTypeError:
            return False
        return bl_flver.name.startswith("o")

    def execute(self, context):
        settings = self.settings(context)

        try:
            objbnd_class = settings.game.from_game_submodule_import(
                "models.objbnd", "OBJBND"
            )  # type: type[OBJBND_TYPING]
            # NOTE: OBJBND stem ignores FLVER underscores (so `o1234_1` is found in `o1234.objbnd`).
            model_stem, objbnd, exported_model_stems, textures = self.export_flver_group_into_binder(
                context,
                settings,
                objbnd_class,
                flver_model_type=FLVERModelType.Object,
            )
        except FLVERExportError as ex:
            return self.error(str(ex))

        flver_export_settings = context.scene.flver_export_settings
        if flver_export_settings.export_textures:
            # TPF always added into OBJBND, never loose/separate.
            self.export_textures_to_binder_tpf(context, objbnd, textures, exported_model_stems)

        relative_objbnd_path = self._get_binder_path(settings, model_stem)
        exported_paths = settings.export_file(self, objbnd, relative_objbnd_path)

        if (
            settings.is_game(GameType.DemonsSouls)
            and settings.demonssouls.export_debug_files
        ):
            if objbnd.dcx_type != DCXType.Null:
                # Export non-DCX OBJBND too.
                for exported_objbnd_path in exported_paths:
                    non_dcx_path = settings.create_non_dcx_file(exported_objbnd_path)
                    self.info(f"Also exported non-DCX OBJBND to: {str(non_dcx_path)}")

        return {"FINISHED" if exported_paths else "CANCELLED"}


@io_soulstruct_operator
class ExportAssetFLVER(BaseGameFLVERBinderExportOperator):
    """Export a single FLVER model from a Blender mesh into same-named GEOMBND in the game directory."""
    bl_idname = "export_scene.asset_flver"
    bl_label = "Export Asset"
    bl_description = "Export a FLVER model file into same-named game GEOMBND (which must exist)"

    @staticmethod
    def _get_binder_path(settings: SoulstructSettings, model_stem: str) -> Path:
        return Path(f"asset/{model_stem[:6]}/{model_stem}.geombnd")

    @classmethod
    def poll(cls, context):
        """Name of model must also start with 'aeg' (not case-sensitive).

        NOTE: Armature is NOT required. Could easily have Map Piece-like, non-animated Assets.
        """
        if not cls.settings(context).can_auto_export or not context.active_object:
            return False
        try:
            bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        except SoulstructTypeError:
            return False
        return bl_flver.name.lower().startswith("aeg")

    def execute(self, context):
        settings = self.settings(context)

        try:
            model_stem, geombnd, flver, exporter = self.get_binder_and_flver(
                context,
                settings,
                settings.game.from_game_submodule_import("models.geombnd", "GEOMBND"),
                flver_model_type=FLVERModelType.Object,
            )
        except FLVERExportError as ex:
            return self.error(str(ex))

        geombnd.set_flver(model_stem, flver)

        # GEOMBND does not contain textures.
        # TODO: Could try to export textures to AET.

        relative_geombnd_path = self._get_binder_path(settings, model_stem)

        exported_paths = settings.export_file(self, geombnd, relative_geombnd_path)
        return {"FINISHED" if exported_paths else "CANCELLED"}


@io_soulstruct_operator
class ExportEquipmentFLVER(BaseGameFLVERBinderExportOperator):
    """Export a FLVER model from a Blender mesh into same-named PARTSBND in the game directory.

    PARTSBNDs can contain extra FLVERs with suffixes like '_1' (e.g. `WP_A_0204_1`, the sheath of weapon `WP_A_0204`),
    which are exported into the PARTSBND of their main FLVER. All FLVERs for the same PARTSBND that are selected or in
    the same collection as the active one are exported together, so exporting either the weapon or its sheath writes
    both.
    """
    bl_idname = "export_scene.equipment_flver"
    bl_label = "Export Equipment"
    bl_description = "Export a FLVER equipment model file into appropriate game PARTSBND"

    # Standard equipment name, e.g. `WP_A_0204` or `AM_M_1000_M`, optionally followed by an extra FLVER index suffix.
    _PARTS_NAME_RE: tp.ClassVar[re.Pattern] = re.compile(
        r"^(?P<stem>[a-z]{2}_[a-z]_\d{4}(?:_[a-z]+)?)(?:_\d+)?$", flags=re.IGNORECASE
    )

    @classmethod
    def _get_binder_stem(cls, model_stem: str) -> str:
        """Strip any extra FLVER index suffix like '_1' (e.g. `WP_A_0204_1` sheath -> `WP_A_0204`). Note that the
        standard equipment name itself contains underscores (and may end with a skin suffix like '_M')."""
        if match := cls._PARTS_NAME_RE.match(model_stem):
            return match.group("stem")
        return model_stem

    @staticmethod
    def _get_binder_path(settings: SoulstructSettings, model_stem: str) -> Path:
        return Path(f"parts/{model_stem}.partsbnd")

    @classmethod
    def poll(cls, context):
        """Must have an Armature parent for a parts FLVER. No chance of a default skeleton!"""
        if not cls.settings(context).can_auto_export or not context.active_object:
            return False
        try:
            bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        except SoulstructTypeError:
            return False
        if not bl_flver.armature:
            # Equipment MUST have an Armature.
            return False
        return True

    def execute(self, context):
        settings = self.settings(context)

        try:
            partsbnd_class = settings.game.from_game_submodule_import(
                "models.partsbnd", "PARTSBND"
            )  # type: type[PARTSBND_TYPING]
            model_stem, partsbnd, exported_model_stems, textures = self.export_flver_group_into_binder(
                context,
                settings,
                partsbnd_class,
                flver_model_type=FLVERModelType.Equipment,
            )
        except FLVERExportError as ex:
            return self.error(str(ex))

        flver_export_settings = context.scene.flver_export_settings
        if flver_export_settings.export_textures:
            # TPF always added into PARTSBND, never loose/separate.
            self.export_textures_to_binder_tpf(context, partsbnd, textures, exported_model_stems)

        relative_partsbnd_path = self._get_binder_path(settings, model_stem)

        try:
            exported_paths = settings.export_file(self, partsbnd, relative_partsbnd_path)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write PARTSBND with new FLVER '{model_stem}'. Error: {ex}")

        if (
            settings.is_game(GameType.DemonsSouls)
            and settings.demonssouls.export_debug_files
        ):
            if partsbnd.dcx_type != DCXType.Null:
                # Export non-DCX PARTSBND too.
                for exported_partsbnd_path in exported_paths:
                    non_dcx_path = settings.create_non_dcx_file(exported_partsbnd_path)
                    self.info(f"Also exported non-DCX PARTSBND to: {str(non_dcx_path)}")

        return {"FINISHED" if exported_paths else "CANCELLED"}

# endregion
