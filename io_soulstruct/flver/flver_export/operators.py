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

from io_soulstruct.general import *
from io_soulstruct.utilities import *
from io_soulstruct.flver.textures.export_textures import *
from io_soulstruct.flver.utilities import *
from .core import FLVERExporter

if tp.TYPE_CHECKING:
    from io_soulstruct.type_checking import CHRBND_TYPING, OBJBND_TYPING, PARTSBND_TYPING
    from .settings import FLVERExportSettings


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
        return len(context.selected_objects) == 1 and context.selected_objects[0].type in {"MESH", "ARMATURE"}

    def invoke(self, context, _event):
        """Set default export name to name of object (before first space and without Blender dupe suffix)."""
        if not context.selected_objects:
            return super().invoke(context, _event)

        obj = context.selected_objects[0]
        if obj.get("Model Name", None) is not None:
            self.filepath = obj["Model Name"] + ".flver"
        self.filepath = obj.name.split(" ")[0].split(".")[0] + ".flver"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        try:
            mesh, armature = get_selected_flver(context)
        except FLVERError as ex:
            return self.error(str(ex))
        settings = self.settings(context)

        # Standard game DCX (unless overridden by this operator) applies to loose FLVER files.
        dcx_type = settings.resolve_dcx_type(self.dcx_type, "flver")

        flver_file_path = Path(self.filepath)  # set by user
        self.to_object_mode()
        exporter = FLVERExporter(self, context, settings, settings.get_mtdbnd(self))

        # NOTE: As the exported FLVER model stem may differ from the Blender object, we need to pass both to the
        # exporter. The exported name is used to create a default bone (the only place in the FLVER file where the model
        # stem appears internally) and the current Blender model stem is used to strip prefixes from dummies and
        # materials.
        flver_file_stem = flver_file_path.name.split(".")[0]
        blender_stem = get_default_flver_stem(mesh, armature, self)

        try:
            flver = exporter.export_flver(
                mesh,
                armature,
                dummy_material_prefix=blender_stem,
                dummy_prefix_must_match=True,  # for safety, as this may be equipment/c0000
                default_bone_name=flver_file_stem,
            )
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
        self.info(f"Exported FLVER to: {written_path}")

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

    dcx_type: get_dcx_enum_property(default="Null")

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
        return len(context.selected_objects) == 1 and context.selected_objects[0].type in {"MESH", "ARMATURE"}

    def execute(self, context):
        try:
            mesh, armature = get_selected_flver(context)
        except FLVERError as ex:
            return self.error(str(ex))

        blender_stem = get_default_flver_stem(mesh, armature, self)

        settings = self.settings(context)
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
                new_path=self.default_entry_path.format(name=blender_stem),
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
                    if entry.minimal_stem == blender_stem:
                        self.info(
                            f"Multiple FLVER files found in Binder. Replacing entry with matching stem: {blender_stem}"
                        )
                        flver_entry = entry
                        break
                else:
                    return self.error(
                        f"Multiple FLVER files found in Binder, none of which have stem '{blender_stem}'. Change the "
                        f"name of your exported object or erase one or more existing FLVERs first."
                    )
            else:
                flver_entry = flver_entries[0]

        exporter = FLVERExporter(self, context, settings, settings.get_mtdbnd(self))

        try:
            flver = exporter.export_flver(
                mesh,
                armature,
                dummy_material_prefix=blender_stem,
                dummy_prefix_must_match=True,  # for safety, as this may be equipment/c0000
                default_bone_name="",  # not permitted here (TODO: what about ER MAPBND?)
            )
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot create exported FLVER from Blender Mesh '{blender_stem}'. Error: {ex}")

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


# region Type-Specific Game Exporters

class ExportMapPieceFLVERs(LoggingOperator):
    bl_idname = "export_scene.map_piece_flver"
    bl_label = "Export Map Pieces"
    bl_description = (
        "Export selected Blender armatures/meshes to map piece FLVER model files in appropriate game map(s)"
    )

    @classmethod
    def poll(cls, context):
        """One or more 'm*' Armatures or Meshes selected."""
        return (
            cls.settings(context).can_auto_export
            and len(context.selected_objects) > 0
            and all(
                obj.type in {"MESH", "ARMATURE"} and obj.name.startswith("m")
                for obj in context.selected_objects
            )
        )

    def execute(self, context):
        try:
            meshes_armatures = get_selected_flvers(context)
        except FLVERError as ex:
            return self.error(str(ex))

        settings = self.settings(context)
        settings.save_settings()

        # TODO: Later games (e.g. Elden Ring) use Binders like 'mapbnd' for map pieces, but this is not yet supported.
        #  This assumes loose FLVERs in the map folder. MAPBND support will require existing MAPBNDs, as the `.grass`
        #  files inside them will be left untouched.
        if not settings.map_stem and not settings.detect_map_from_collection:
            return self.error(
                "No game map directory specified in Soulstruct settings and `Detect Map from Collection` is disabled."
            )

        flver_export_settings = context.scene.flver_export_settings  # type: FLVERExportSettings
        flver_dcx_type = settings.game.get_dcx_type("flver")

        self.to_object_mode()
        exporter = FLVERExporter(self, context, settings)
        active_object = context.active_object

        map_area_textures = {}  # maps area stems 'mAA' to dictionaries of Blender images to export

        for mesh, armature in meshes_armatures:

            map_stem = settings.get_map_stem_for_export(armature or mesh, oldest=True)
            relative_map_path = Path(f"map/{map_stem}")

            # If 'Model Name' is not defined, model stem uses the 'stem' of the object name and area suffix 'AXX'.
            blender_stem = get_default_flver_stem(mesh, armature, self)
            default_file_stem = blender_stem + f"A{relative_map_path.name[1:3]}"
            model_file_stem = mesh.get("Model Name", default_file_stem)
            if model_file_stem != default_file_stem:
                self.warning(
                    f"Custom property 'Model Name' '{model_file_stem}' will override conflicting name from object "
                    f"name '{default_file_stem}'."
                )

            try:
                flver = exporter.export_flver(mesh, armature, blender_stem, False, model_file_stem)
            except Exception as ex:
                traceback.print_exc()
                return self.error(f"Cannot export Map Piece FLVER '{model_file_stem}' from {mesh.name}. Error: {ex}")

            flver.dcx_type = flver_dcx_type
            settings.export_file(self, flver, relative_map_path / f"{model_file_stem}.flver")

            if flver_export_settings.export_textures:
                # Collect all Blender images for batched map area export.
                area = settings.map_stem[:3]
                area_textures = map_area_textures.setdefault(area, {})
                area_textures |= exporter.collected_texture_images

        if map_area_textures:  # only non-empty if texture export enabled
            export_map_area_textures(
                self,
                context,
                settings,
                map_area_textures,
            )

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
        binder_path_template: str,
        binder_class: type[CHRBND_TYPING | OBJBND_TYPING | PARTSBND_TYPING],
    ) -> tuple[str, CHRBND_TYPING | OBJBND_TYPING | PARTSBND_TYPING, FLVER, FLVERExporter]:
        mesh, armature = get_selected_flver(context)
        if armature is None:
            raise FLVERExportError("Must select an Armature parent to quick-export a FLVER.")

        model_stem = get_default_flver_stem(mesh, armature, self)
        cls_name = binder_class.__name__

        # We prepare and retrieve the binder to be exported into.
        relative_binder_path = Path(binder_path_template.format(model_stem=model_stem))
        try:
            binder_path = settings.prepare_project_file(relative_binder_path, overwrite_existing=False, must_exist=True)
        except FileNotFoundError as ex:
            raise FLVERExportError(
                f"Cannot find {cls_name} binder for {model_stem}: {relative_binder_path}. Error: {ex}"
            )

        binder = binder_class.from_path(binder_path)

        self.to_object_mode()
        exporter = FLVERExporter(self, context, settings, settings.get_mtdbnd(self))
        try:
            flver = exporter.export_flver(
                mesh, armature, model_stem, dummy_prefix_must_match=True, default_bone_name=""
            )
        except Exception as ex:
            traceback.print_exc()
            raise FLVERExportError(f"Cannot create exported FLVER from Blender Mesh '{model_stem}'. Error: {ex}")

        flver.dcx_type = DCXType.Null  # no DCX inside any Binder here
        # noinspection PyTypeChecker
        return model_stem, binder, flver, exporter

    def export_textures_to_binder_tpf(
        self,
        context,
        binder: CHRBND_TYPING | OBJBND_TYPING | PARTSBND_TYPING,
        images: dict[str, bpy.types.Image],
    ) -> bool:
        # TODO: Get existing textures to resolve 'SAME' option for DDS format.
        multi_tpf = export_images_to_tpf(context, self, images, enforce_max_chrbnd_tpf_size=binder.cls_name == "CHRBND")
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
        """Must select an Armature parent for a character FLVER. No chance of a default skeleton!

        Name of character must also start with 'c'.
        """
        return (
            cls.settings(context).can_auto_export
            and len(context.selected_objects) == 1
            and context.selected_objects[0].type == "ARMATURE"
            and context.selected_objects[0].name.startswith("c")  # TODO: could require 'c####' template also
        )

    def execute(self, context):
        settings = self.settings(context)

        try:
            model_stem, chrbnd, flver, exporter = self.get_binder_and_flver(
                context,
                settings,
                "chr/{model_stem}.chrbnd",
                settings.game.from_game_submodule_import("models.chrbnd", "CHRBND"),
            )
        except FLVERExportError as ex:
            return self.error(str(ex))

        flver_export_settings = context.scene.flver_export_settings  # type: FLVERExportSettings

        if not flver_export_settings.export_textures:
            # Export CHRBND now with FLVER.
            return settings.export_file(self, chrbnd, Path(f"chr/{model_stem}.chrbnd"))

        # Export textures. This may or may not involve file(s) outside the CHRBND, depending on the game.
        post_export_action = self.export_textures(
            context,
            settings,
            chrbnd,
            model_stem,
            exporter.collected_texture_images,
        )
        result = settings.export_file(self, chrbnd, Path(f"chr/{model_stem}.chrbnd"))
        if result == {"FINISHED"} and post_export_action:
            # Only do this if CHRBND export was successful, as it may create/delete adjacent files/folders.
            post_export_action()
        return result

    def export_textures(
        self,
        context,
        settings: SoulstructSettings,
        chrbnd: CHRBND_TYPING,
        model_stem: str,
        images: dict[str, bpy.types.Image],
    ) -> tp.Callable[[], None] | None:

        multi_tpf_succeeded = self.export_textures_to_binder_tpf(
            context,
            chrbnd,
            images,
        )

        if settings.is_game(DARK_SOULS_PTDE):

            relative_tpf_dir_path = Path(f"chr/{model_stem}")

            if multi_tpf_succeeded:

                def post_export_action():
                    export_tpf_dir_path = settings.get_project_path(relative_tpf_dir_path)
                    if is_path_and_dir(export_tpf_dir_path):
                        # Delete loose TPF folder (in favor of new Binder TPF).
                        export_tpf_dir_path.rmdir()
                    if settings.also_export_to_game:
                        import_tpf_dir_path = settings.get_game_path(relative_tpf_dir_path)
                        if is_path_and_dir(import_tpf_dir_path):
                            import_tpf_dir_path.rmdir()

                return post_export_action

            # Otherwise, create loose folder with individual TPFs.
            tpfs = export_images_to_multiple_tpfs(
                context,
                self,
                images,
                DCXType.Null,  # no DCX in PTDE
            )

            def post_export_action():

                if tpfs:
                    for texture_stem, tpf in tpfs.items():
                        settings.export_file(self, tpf, relative_tpf_dir_path / f"{texture_stem}.tpf")
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
                    export_chrtpfbdt_path = settings.get_project_path(relative_chrtpfbdt_path)
                    if is_path_and_file(export_chrtpfbdt_path):
                        # Delete CHRTPFBDT (in favor of new TPF).
                        export_chrtpfbdt_path.unlink()
                    if settings.also_export_to_game:
                        import_chrtpfbdt_path = settings.get_game_path(relative_chrtpfbdt_path)
                        if is_path_and_file(import_chrtpfbdt_path):
                            import_chrtpfbdt_path.unlink()

                return post_export_action

            # Otherwise, create CHRTPFBXF. This method will put the header in `chrbnd`.
            chrtpfbdt_bytes, entry_count = self.create_chrtpfbxf(context, settings, chrbnd, model_stem, images)

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
        images: dict[str, bpy.types.Image],
    ) -> tuple[bytes, int]:
        """Create CHRTPFBXF, put its header into CHRBND, and return the split data as bytes, along with entry count."""
        chrtpfbhd_entry_name = f"{model_stem}.chrtpfbhd"  # no DCX

        # TODO: Get existing textures to resolve 'SAME' option for DDS format.
        chrtpfbxf = export_images_to_tpfbhd(
            context, self, images, settings.game.get_dcx_type("tpf"), entry_path_parent=f"\\{model_stem}\\"
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
        """Must select an Armature parent for an object FLVER. No chance of a default skeleton!

        Name of character must also start with 'o'.
        """
        return (
            cls.settings(context).can_auto_export
            and len(context.selected_objects) == 1
            and context.selected_objects[0].type == "ARMATURE"
            and context.selected_objects[0].name.startswith("o")  # TODO: could require 'o####{_#}' template also
        )

    def execute(self, context):
        settings = self.settings(context)

        try:
            model_stem, objbnd, flver, exporter = self.get_binder_and_flver(
                context,
                settings,
                "obj/{model_stem}.objbnd",
                settings.game.from_game_submodule_import("models.objbnd", "OBJBND"),
            )
        except FLVERExportError as ex:
            return self.error(str(ex))

        objbnd.flvers[model_stem] = flver

        flver_export_settings = context.scene.flver_export_settings  # type: FLVERExportSettings
        if flver_export_settings.export_textures:
            # TPF always added to OBJBND.
            self.export_textures_to_binder_tpf(context, objbnd, exporter.collected_texture_images)

        return settings.export_file(self, objbnd, Path(f"obj/{model_stem}.objbnd"))


class ExportEquipmentFLVER(BaseGameFLVERBinderExportOperator):
    """Export a single FLVER model from a Blender mesh into same-named PARTSBND in the game directory."""
    bl_idname = "export_scene.equipment_flver"
    bl_label = "Export Equipment"
    bl_description = "Export a FLVER equipment model file into appropriate game PARTSBND"

    @classmethod
    def poll(cls, context):
        """Must select an Armature parent for an equipment FLVER. No chance of a default skeleton!"""
        return (
            cls.settings(context).can_auto_export
            and len(context.selected_objects) == 1
            and context.selected_objects[0].type == "ARMATURE"
            # No restriction on name.
        )

    def execute(self, context):
        settings = self.settings(context)

        try:
            model_stem, partsbnd, flver, exporter = self.get_binder_and_flver(
                context,
                settings,
                "parts/{model_stem}.partsbnd",
                settings.game.from_game_submodule_import("models.partsbnd", "PARTSBND"),
            )
        except FLVERExportError as ex:
            return self.error(str(ex))

        partsbnd.flvers[model_stem] = flver

        flver_export_settings = context.scene.flver_export_settings  # type: FLVERExportSettings
        if flver_export_settings.export_textures:
            # TPF always added to OBJBND.
            self.export_textures_to_binder_tpf(context, partsbnd, exporter.collected_texture_images)

        try:
            settings.export_file(self, partsbnd, Path(f"parts/{model_stem}.partsbnd"))
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write PARTSBND with new FLVER '{model_stem}'. Error: {ex}")

        return {"FINISHED"}

# endregion
