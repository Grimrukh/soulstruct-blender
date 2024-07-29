from __future__ import annotations

__all__ = [
    "ExportStandaloneFLVER",
    "ExportFLVERIntoBinder",
    "ExportMapPieceFLVERs",
    "ExportCharacterFLVER",
    "ExportObjectFLVER",
    "ExportEquipmentFLVER",
]

import traceback
import typing as tp
from pathlib import Path

import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty
from bpy_extras.io_utils import ExportHelper

from soulstruct.base.models.flver import FLVER
from soulstruct.containers import Binder, BinderEntry, EntryNotFoundError
from soulstruct.dcx import DCXType
from soulstruct.games import *

from io_soulstruct.exceptions import *
from io_soulstruct.general import *
from io_soulstruct.utilities import *
from io_soulstruct.flver.image import *
from io_soulstruct.flver.image.export_operators import export_map_area_textures
from .types import BlenderFLVER

if tp.TYPE_CHECKING:
    from io_soulstruct.type_checking import CHRBND_TYPING, OBJBND_TYPING, PARTSBND_TYPING
    from .properties import FLVERExportSettings


# region Generic Exporters

class ExportStandaloneFLVER(LoggingOperator, ExportHelper):
    """Export one FLVER model from a Blender Armature parent to a file using a browser window."""
    bl_idname = "export_scene.flver"
    bl_label = "Export FLVER"
    bl_description = "Export Blender Armature/Mesh to a standalone FromSoftware FLVER model file"

    filename_ext = ".flver"

    filter_glob: StringProperty(
        default="*.flver;*.flver.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    dcx_type: get_dcx_enum_property()

    @classmethod
    def poll(cls, context):
        """One FLVER Armature or Mesh object must be selected.

        If a Mesh is selected and it does not have an Armature parent object, a default FLVER skeleton with a single
        eponymous bone at the origin will be exported (which is fine for, e.g., most map pieces).
        """
        if not context.active_object:
            return False
        return BlenderFLVER.test_obj(context.active_object)

    def invoke(self, context, _event):
        """Set default export name to name of object (before first space and without Blender dupe suffix)."""
        if not context.active_object:
            return super().invoke(context, _event)

        bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        settings = self.settings(context)
        self.filepath = settings.game.process_dcx_path(f"{bl_flver.tight_name}.flver")
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
        self.to_object_mode()

        try:
            # No textures collected.
            flver = bl_flver.to_soulstruct_obj(self, context)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot get exported FLVER. Error: {ex}")

        flver.dcx_type = dcx_type
        try:
            # Will create a `.bak` file automatically if absent.
            written_path = flver.write(flver_file_path)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write exported FLVER. Error: {ex}")
        self.info(f"Exported FLVER to: {written_path[0]}")

        return {"FINISHED"}


class ExportFLVERIntoBinder(LoggingOperator, ExportHelper):
    """Export a single FLVER model from a Blender mesh into a chosen game binder (BND/BHD).

    TODO: Does not support multiple FLVERs yet, but some Binders (e.g. OBJBNDs) can have more than one.
    """
    bl_idname = "export_scene.flver_binder"
    bl_label = "Export FLVER Into Binder"
    bl_description = "Export a FLVER model file into a FromSoftware Binder (BND/BHD)"

    filename_ext = ".chrbnd"

    filter_glob: StringProperty(
        default="*.chrbnd;*.chrbnd.dcx;*.objbnd;*.objbnd.dcx;*.partsbnd;*.partsbnd.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

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
    def poll(cls, context):
        """At least one Blender mesh selected."""
        if not context.active_object:
            return False
        return BlenderFLVER.test_obj(context.active_object)

    def execute(self, context):
        try:
            bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        except SoulstructTypeError as ex:
            return self.error(str(ex))

        # Automatic DCX for FLVERs in Binders is Null.
        dcx_type = DCXType[self.dcx_type] if self.dcx_type != "Auto" else DCXType.Null

        self.to_object_mode()
        binder_file_path = Path(self.filepath)
        try:
            binder = Binder.from_path(binder_file_path)
        except Exception as ex:
            return self.error(f"Could not load Binder file '{binder_file_path}'. Error: {ex}.")

        # Check for FLVER entry before doing any exporting.
        flver_entries = binder.find_entries_matching_name(r".*\.flver(\.dcx)?")
        if not flver_entries:
            if self.default_entry_id == -1:
                return self.error("No FLVER files found in Binder and default entry ID was left as -1.")
            flver_entry = binder.set_default_entry(
                entry_spec=self.default_entry_id,
                new_path=self.default_entry_path.format(name=bl_flver.tight_name),
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
                    if entry.minimal_stem == bl_flver.tight_name:
                        self.info(
                            f"Multiple FLVER files found in Binder. Replacing entry with matching stem: "
                            f"{bl_flver.tight_name}"
                        )
                        flver_entry = entry
                        break
                else:
                    return self.error(
                        f"Multiple FLVER files found in Binder, none of which have stem '{bl_flver.tight_name}'. "
                        f"Change the start of your exported object's name or erase one or more existing FLVERs first."
                    )
            else:
                flver_entry = flver_entries[0]

        try:
            flver = bl_flver.to_soulstruct_obj(self, context)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot create exported FLVER from Blender Mesh '{bl_flver.name}'. Error: {ex}")

        flver.dcx_type = dcx_type

        try:
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

class ExportMapPieceFLVERs(LoggingOperator):
    bl_idname = "export_scene.map_piece_flver"
    bl_label = "Export Map Pieces"
    bl_description = (
        "Export selected Blender armatures/meshes to map piece FLVER model files in appropriate game map(s)"
    )

    @classmethod
    def poll(cls, context):
        """One or more 'm*' Armatures or Meshes selected."""
        if not cls.settings(context).can_auto_export or not context.selected_objects:
            return False
        for obj in context.selected_objects:
            if not BlenderFLVER.test_obj(obj):
                return False
        return True

    def execute(self, context):
        try:
            bl_flvers = BlenderFLVER.get_selected_flvers(context)
        except FLVERError as ex:
            return self.error(str(ex))

        settings = self.settings(context)

        # TODO: Later games (e.g. Elden Ring) use Binders like 'mapbnd' for map pieces, but this is not yet supported.
        #  This assumes loose FLVERs in the map folder. MAPBND support will require existing MAPBNDs, as the `.grass`
        #  files inside them will be left untouched.
        if not settings.map_stem and not settings.detect_map_from_collection:
            return self.error(
                "No game map directory specified in Soulstruct settings and `Detect Map from Collection` is disabled."
            )

        flver_export_settings = context.scene.flver_export_settings
        flver_dcx_type = settings.game.get_dcx_type("flver")

        self.to_object_mode()
        active_object = context.active_object  # to restore later

        map_area_textures = {}  # maps area stems 'mAA' to dictionaries of Blender images to export

        for bl_flver in bl_flvers:

            map_stem = settings.get_map_stem_for_export(bl_flver.mesh, oldest=True)
            relative_map_path = Path(f"map/{map_stem}")
            texture_collection = DDSTextureCollection()

            try:
                # We also pass the model name as the default bone name.
                flver = bl_flver.to_soulstruct_obj(
                    self,
                    context,
                    texture_collection,
                )
            except Exception as ex:
                traceback.print_exc()
                return self.error(
                    f"Cannot export Map Piece FLVER '{bl_flver.tight_name}' from '{bl_flver.name}. Error: {ex}"
                )

            flver.dcx_type = flver_dcx_type
            settings.export_file(self, flver, relative_map_path / f"{bl_flver.tight_name}.flver")

            if flver_export_settings.export_textures:
                # Collect all Blender images for batched map area export.
                area = settings.map_stem[:3]
                area_textures = map_area_textures.setdefault(area, DDSTextureCollection())
                area_textures |= texture_collection

        if map_area_textures:  # only non-empty if texture export enabled
            for map_area, texture_collection in map_area_textures.items():
                export_map_area_textures(self, context, map_area, texture_collection)

        # Select original active object.
        if active_object:
            context.view_layer.objects.active = active_object

        return {"FINISHED"}


class BaseGameFLVERBinderExportOperator(LoggingOperator):
    """Base class for operator that exports a FLVER directly into game Binder (CHRBND, OBJBND, PARTSBND)."""

    def get_binder_and_flver(
        self,
        context: bpy.types.Context,
        settings: SoulstructSettings,
        binder_path_callback: tp.Callable[[BlenderFLVER], Path],
        binder_class: type[CHRBND_TYPING | OBJBND_TYPING | PARTSBND_TYPING],
    ) -> tuple[str, CHRBND_TYPING | OBJBND_TYPING | PARTSBND_TYPING, FLVER, DDSTextureCollection]:
        bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        cls_name = binder_class.__name__

        # We prepare and retrieve the binder to be exported into.
        relative_binder_path = binder_path_callback(bl_flver)
        try:
            binder_path = settings.prepare_project_file(relative_binder_path, must_exist=True)
        except FileNotFoundError as ex:
            raise FLVERExportError(
                f"Cannot find {cls_name} binder for {bl_flver.name}: {relative_binder_path}. Error: {ex}"
            )

        binder = binder_class.from_path(binder_path)

        self.to_object_mode()
        texture_collection = DDSTextureCollection()
        try:
            flver = bl_flver.to_soulstruct_obj(self, context, texture_collection=texture_collection)
        except Exception as ex:
            traceback.print_exc()
            raise FLVERExportError(
                f"Cannot create exported FLVER '{bl_flver.tight_name}' from Blender Mesh '{bl_flver.name}'. Error: {ex}"
            )

        flver.dcx_type = DCXType.Null  # no DCX inside any Binder here

        return bl_flver.tight_name, binder, flver, texture_collection

    def export_textures_to_binder_tpf(
        self,
        context,
        binder: CHRBND_TYPING | OBJBND_TYPING | PARTSBND_TYPING,
        texture_collection: DDSTextureCollection,
    ) -> bool:
        multi_tpf = texture_collection.to_multi_texture_tpf(
            self,
            context,
            enforce_max_chrbnd_tpf_size=binder.cls_name == "CHRBND",
            find_same_format=None,  # TODO: Get existing textures to resolve 'SAME' option for DDS format
        )
        if multi_tpf is None:
            return False  # textures exceeded bundled CHRBND capacity; handled by caller (game-specific)

        multi_tpf.dcx_type = DCXType.Null  # never DCX inside these Binders
        binder.tpf = multi_tpf  # will replace existing TPF
        self.info(f"Exported {len(multi_tpf.textures)} textures into multi-texture TPF in {binder.cls_name}.")
        return True


class ExportCharacterFLVER(BaseGameFLVERBinderExportOperator):
    """Export a single FLVER model from a Blender mesh into same-named CHRBND in the game directory."""
    bl_idname = "export_scene.character_flver"
    bl_label = "Export Character"
    bl_description = "Export a FLVER model file into same-named game CHRBND (which must exist)"

    @classmethod
    def poll(cls, context):
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
            model_stem, chrbnd, flver, textures = self.get_binder_and_flver(
                context,
                settings,
                lambda bl_flver: Path(f"chr/{bl_flver.tight_name}.chrbnd"),
                settings.game.from_game_submodule_import("models.chrbnd", "CHRBND"),
            )
        except FLVERExportError as ex:
            return self.error(str(ex))
        chrbnd.flvers[model_stem] = flver

        flver_export_settings = context.scene.flver_export_settings
        if not flver_export_settings.export_textures:
            # Export CHRBND now with FLVER.
            return settings.export_file(self, chrbnd, Path(f"chr/{model_stem}.chrbnd"))

        # Export textures. This may or may not involve file(s) outside the CHRBND, depending on the game.
        post_export_action = self.get_export_textures_action(
            context,
            settings,
            chrbnd,
            model_stem,
            textures,
        )
        result = settings.export_file(self, chrbnd, Path(f"chr/{model_stem}.chrbnd"))
        if result == {"FINISHED"} and post_export_action:
            # Only do this if CHRBND export was successful, as it may create/delete adjacent files/folders.
            post_export_action()
        return result

    def get_export_textures_action(
        self,
        context,
        settings: SoulstructSettings,
        chrbnd: CHRBND_TYPING,
        model_stem: str,
        texture_collection: DDSTextureCollection,
    ) -> tp.Callable[[], None] | None:

        multi_tpf_succeeded = self.export_textures_to_binder_tpf(
            context,
            chrbnd,
            texture_collection,
        )

        if settings.is_game(DARK_SOULS_PTDE):

            relative_tpf_dir_path = Path(f"chr/{model_stem}")

            if multi_tpf_succeeded:

                def post_export_action():
                    if settings.project_root:
                        export_dir = settings.project_root.get_dir_path(relative_tpf_dir_path, if_exist=True)
                        if export_dir:
                            # Delete loose TPF folder (in favor of new Binder TPF).
                            export_dir.rmdir()
                    if settings.also_export_to_game and settings.game_root:
                        import_dir = settings.game_root.get_dir_path(relative_tpf_dir_path, if_exist=True)
                        if import_dir:
                            import_dir.rmdir()

                return post_export_action

            # Otherwise, create loose folder with individual TPFs.
            tpfs = texture_collection.to_single_texture_tpfs(
                self,
                DCXType.Null,  # no DCX in PTDE
                find_same_format=None,  # TODO
            )

            def post_export_action():
                if tpfs:
                    for tpf in tpfs:
                        # TPF `path` already set correctly to name.
                        settings.export_file(self, tpf, relative_tpf_dir_path / tpf.path.name)
                    self.info(f"Exported {len(tpfs)} textures into loose character TPF folder '{model_stem}'.")

            return post_export_action

        elif settings.is_game(DARK_SOULS_DSR):

            relative_chrtpfbdt_path = Path(f"chr/{model_stem}.chrtpfbdt")  # no DCX

            if multi_tpf_succeeded:
                try:
                    # Remove old CHRTPFBHD header entry (in favor of new TPF).
                    chrbnd.remove_entry_name(f"{model_stem}.chrtpfbhd")
                except EntryNotFoundError:
                    pass

                def post_export_action():
                    if settings.project_root:
                        export_path = settings.project_root.get_file_path(relative_chrtpfbdt_path, if_exist=True)
                        if export_path:
                            # Delete CHRTPFBDT (in favor of new TPF).
                            export_path.unlink()
                    if settings.also_export_to_game and settings.game_root:
                        import_path = settings.game_root.get_file_path(relative_chrtpfbdt_path, if_exist=True)
                        if import_path:
                            import_path.unlink()

                return post_export_action

            # Otherwise, create CHRTPFBXF. This method will put the header in `chrbnd`.
            chrtpfbdt_bytes, entry_count = self.create_chrtpfbxf(
                context, settings, chrbnd, model_stem, texture_collection
            )

            def post_export_action():
                if chrtpfbdt_bytes:
                    settings.export_file_data(self, chrtpfbdt_bytes, relative_chrtpfbdt_path, "CHRTPFBDT")
                    self.info(
                        f"Exported {entry_count} textures into split CHRTPFBHD (in CHRBND) and adjacent CHRTPFBDT."
                    )

            return post_export_action

        self.warning(f"Cannot handled CHRBND 'overflow' texture export for game {settings.game.name}.")
        return None

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
                chrtpfbhd_entry_id = chrbnd.CHRTPFBHD_ENTRY_ID
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


class ExportObjectFLVER(BaseGameFLVERBinderExportOperator):
    """Export a single FLVER model from a Blender mesh into same-named OBJBND in the game directory.

    If the Blender object name has an underscore in it, the string before that underscore will be used to find the
    OBJBND (which supports multiple FLVERs) and the string after that will be used to offset the default FLVER entry ID
    in the Binder. For example, Blender FLVER `o0100_1` will be exported into `o0100.objbnd` as Binder entry 201 (for
    games with standard default FLVER ID 200) with FLVER name `o0100_1.flver`.
    """
    bl_idname = "export_scene.object_flver"
    bl_label = "Export Object"
    bl_description = "Export a FLVER model file into same-named game OBJBND (which must exist)"

    @classmethod
    def poll(cls, context):
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
            model_stem, objbnd, flver, textures = self.get_binder_and_flver(
                context,
                settings,
                lambda bl_flver: Path(f"obj/{bl_flver.tight_name}.objbnd"),
                settings.game.from_game_submodule_import("models.objbnd", "OBJBND"),
            )
        except FLVERExportError as ex:
            return self.error(str(ex))

        objbnd.flvers[model_stem] = flver

        flver_export_settings = context.scene.flver_export_settings
        if flver_export_settings.export_textures:
            # TPF always added to OBJBND.
            self.export_textures_to_binder_tpf(context, objbnd, textures)

        return settings.export_file(self, objbnd, Path(f"obj/{model_stem}.objbnd"))


class ExportAssetFLVER(BaseGameFLVERBinderExportOperator):
    """Export a single FLVER model from a Blender mesh into same-named GEOMBND in the game directory."""
    bl_idname = "export_scene.asset_flver"
    bl_label = "Export Asset"
    bl_description = "Export a FLVER model file into same-named game GEOMBND (which must exist)"

    @classmethod
    def poll(cls, context):
        """Name of model must also start with 'aeg.

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
                lambda bl_flver: Path(f"asset/{bl_flver.tight_name[:6]}/{bl_flver.tight_name}.geombnd"),
                settings.game.from_game_submodule_import("models.geombnd", "GEOMBND"),
            )
        except FLVERExportError as ex:
            return self.error(str(ex))

        geombnd.flvers[model_stem] = flver

        # GEOMBND does not contain textures.
        # TODO: Could try to export textures to AET.

        return settings.export_file(self, geombnd, Path(f"asset/{model_stem[:6]}/{model_stem}.geombnd"))


class ExportEquipmentFLVER(BaseGameFLVERBinderExportOperator):
    """Export a single FLVER model from a Blender mesh into same-named PARTSBND in the game directory."""
    bl_idname = "export_scene.equipment_flver"
    bl_label = "Export Equipment"
    bl_description = "Export a FLVER equipment model file into appropriate game PARTSBND"

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
            model_stem, partsbnd, flver, textures = self.get_binder_and_flver(
                context,
                settings,
                lambda bl_flver: Path(f"parts/{model_stem}.partsbnd"),
                settings.game.from_game_submodule_import("models.partsbnd", "PARTSBND"),
            )
        except FLVERExportError as ex:
            return self.error(str(ex))

        partsbnd.flvers[model_stem] = flver

        flver_export_settings = context.scene.flver_export_settings
        if flver_export_settings.export_textures:
            # TPF always added to OBJBND.
            self.export_textures_to_binder_tpf(context, partsbnd, textures)

        try:
            settings.export_file(self, partsbnd, Path(f"parts/{model_stem}.partsbnd"))
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write PARTSBND with new FLVER '{model_stem}'. Error: {ex}")

        return {"FINISHED"}

# endregion
