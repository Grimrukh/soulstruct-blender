"""
Import FLVER files (with/without DCX) into Blender 3.3+ (Python 3.10+ scripting required).

Can find FLVERs in CHRBND, OBJBND, and PARTSBND binders (with or without DCX compression).

The FLVER is imported as an Armature object with all FLVER sub-meshes as Mesh children and model 'dummy points' as Empty
children.

New Blender materials will be created as needed that approximate in-game look (including conversion and loading of
located DDS textures), but existing materials with the same name as the FLVER materials will be used if the user selects
this option (on by default).

Critical FLVER information needed for export, but not represented anywhere else in Blender, is stored with custom
properties as necessary (on FLVER armatures, meshes, dummies, and materials).

NOTE: Currently only thoroughly tested for DS1/DSR.
"""
from __future__ import annotations

__all__ = [
    "ImportFLVER",
    "ImportMapPieceFLVER",
    "ImportCharacterFLVER",
    "ImportObjectFLVER",
    "ImportAssetFLVER",
    "ImportEquipmentFLVER",
]

import re
import time
import traceback
from pathlib import Path

import bpy
import bpy.ops

from soulstruct.flver import FLVERVersion, FLVER
from soulstruct.containers import Binder
from soulstruct.demonssouls.constants import CHARACTER_MODELS as DES_CHARACTER_MODELS
from soulstruct.darksouls1ptde.constants import CHARACTER_MODELS as DS1_CHARACTER_MODELS
from soulstruct.eldenring.constants import CHARACTER_MODELS as ER_CHARACTER_MODELS

from soulstruct.blender.flver.image.image_import_manager import ImageImportManager
from soulstruct.blender.flver.utilities import *
from soulstruct.blender.general import SoulstructSettings
from soulstruct.blender.utilities import *
from ..types import BlenderFLVER
from ..properties import FLVERImportSettings


FLVER_BINDER_RE = re.compile(r"^.*?\.(.*bnd)(\.dcx)?$")


class BaseFLVERImportOperator(LoggingImportOperator):

    def draw(self, context):
        import_settings = context.scene.flver_import_settings
        for prop_name in import_settings.__annotations__:
            self.layout.prop(import_settings, prop_name)

    def execute(self, context: bpy.types.Context):
        """Default import method for FLVERs."""

        p = time.perf_counter()

        flvers = []  # type: list[tuple[str, FLVER]]  # holds `(bl_name, flver)` pairs
        image_import_manager = ImageImportManager(self, context)

        import_settings = context.scene.flver_import_settings
        use_matbinbnd = False  # auto-set if first FLVER is from Sekiro/Elden Ring

        for source_path in self.file_paths:

            if FLVER_BINDER_RE.match(source_path.name):
                # NOTE: Will always import all FLVERs found in Binder.
                binder = Binder.from_path(source_path)
                binder_flvers = get_flvers_from_binder(binder, source_path, allow_multiple=True)
                if import_settings.import_textures:
                    image_import_manager.find_flver_textures(source_path, binder)
                    for flver in binder_flvers:
                        self.find_extra_textures(source_path, flver, image_import_manager)
                for flver in binder_flvers:
                    # TODO: Sekiro does NOT use MATBIN, so this test needs to change.
                    if flver.version == FLVERVersion.Sekiro_EldenRing:
                        use_matbinbnd = True
                    flvers.append((flver.path_minimal_stem, flver))
            else:  # e.g. loose Map Piece FLVER
                flver = FLVER.from_path(source_path)
                if import_settings.import_textures:
                    image_import_manager.find_flver_textures(source_path)
                    self.find_extra_textures(source_path, flver, image_import_manager)
                flvers.append((source_path.name.split(".")[0], flver))

        if use_matbinbnd:
            self.info("Using MATBINBND for Elden Ring FLVERs.")
        else:
            self.info("Using MTDBND for pre-Elden Ring FLVERs.")

        settings = self.settings(context)
        collection = self.get_collection(context, Path(self.directory).name)

        bl_flver = None
        for bl_name, flver in flvers:

            try:
                bl_flver = BlenderFLVER.new_from_soulstruct_obj(
                    self,
                    context,
                    flver,
                    name=bl_name,
                    image_import_manager=image_import_manager,
                    collection=collection,
                )
            except Exception as ex:
                # Delete any objects created prior to exception.
                traceback.print_exc()  # for inspection in Blender console
                return self.error(f"Cannot import FLVER: {bl_name}. Error: {ex}")

            self.post_process_flver(context, settings, import_settings, bl_flver)

        self.info(f"Imported {len(flvers)} FLVER(s) in {time.perf_counter() - p:.3f} s.")

        # Select and frame view on (final) newly imported Mesh.
        if bl_flver:
            self.set_active_obj(bl_flver.mesh)
            bpy.ops.view3d.view_selected(use_all_regions=False)

        return {"FINISHED"}

    def post_process_flver(
        self,
        context: bpy.types.Context,
        settings: SoulstructSettings,
        import_settings: FLVERImportSettings,
        bl_flver: BlenderFLVER,
    ):
        """Can be overridden to modify new FLVER model."""
        pass

    def get_collection(self, context: bpy.types.Context, file_directory_name: str):
        """Get collection to add imported FLVER to. Defaults to scene view layer collection."""
        return context.view_layer.active_layer_collection.collection

    def find_extra_textures(self, flver_source_path: Path, flver: FLVER, image_import_manager: ImageImportManager):
        """Can be overridden by importers for specific FLVER model types that know where their textures are."""
        pass

    def set_blender_parent(self, context, bl_flver_armature: bpy.types.ArmatureObject):
        """Set parent of imported FLVER armature, if needed."""
        pass


class ImportFLVER(BaseFLVERImportOperator):
    """This appears in the tooltip of the operator and in the generated docs."""
    bl_idname = "import_scene.flver"
    bl_label = "Import FLVER"
    bl_description = "Import a FromSoftware FLVER model file. Can import from BNDs and supports DCX-compressed files."

    filter_glob: bpy.props.StringProperty(
        default="*.flver;*.flver.dcx;*.chrbnd;*.chrbnd.dcx;*.objbnd;*.objbnd.dcx;"
                "*.partsbnd;*.partsbnd.dcx;*.mapbnd;*.mapbnd.dcx;*.geombnd;*.geombnd.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: bpy.props.StringProperty(options={'HIDDEN'}, subtype="DIR_PATH")


# region Game Folder Importers

class ImportMapPieceFLVER(BaseFLVERImportOperator):
    """Import a map piece FLVER from selected game map directory."""
    bl_idname = "import_scene.map_piece_flver"
    bl_label = "Import Map Piece"
    bl_description = "Import a Map Piece FLVER from selected game map directory"

    filter_glob: bpy.props.StringProperty(
        default="*.flver;*.flver.dcx;*.mapbnd;*.mapbnd.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: bpy.props.StringProperty(options={'HIDDEN'}, subtype="DIR_PATH")

    @classmethod
    def poll(cls, context) -> bool:
        try:
            cls.settings(context).get_import_map_dir_path()
            return True
        except NotADirectoryError:
            return False

    def invoke(self, context, _event):
        """Set the initial directory based on Global Settings."""
        settings = self.settings(context)
        map_piece_map_stem = settings.get_oldest_map_stem_version()
        try:
            map_dir = settings.get_import_map_dir_path(map_stem=map_piece_map_stem)
        except NotADirectoryError:
            return super().invoke(context, _event)
        self.directory = str(map_dir)
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def get_collection(self, context: bpy.types.Context, file_directory_name: str):
        """Assumes file directory name is a map stem."""
        return find_or_create_collection(
            context.scene.collection, f"{file_directory_name} Models", f"{file_directory_name} Map Piece Models"
        )

    def find_extra_textures(self, flver_source_path: Path, flver: FLVER, image_import_manager: ImageImportManager):
        """Some Map Pieces lazily use textures from other areas that are assumed to be loaded at the right time."""
        map_dir = flver_source_path.parent.parent  # assume FLVER is in a 'map' subdirectory
        image_import_manager.register_lazy_flver_map_textures(map_dir, flver)


class ImportCharacterFLVER(BaseFLVERImportOperator):
    """Shortcut for browsing for CHRBND Binders in game 'chr' directory."""
    bl_idname = "import_scene.character_flver"
    bl_label = "Import Character"
    bl_description = "Import character FLVER from a CHRBND in selected game 'chr' directory"

    filter_glob: bpy.props.StringProperty(
        default="*.chrbnd;*.chrbnd.dcx;*.chrbnd.bak;*.chrbnd.dcx.bak;",
        options={'HIDDEN'},
        maxlen=255,
    )

    DEFAULT_SUBDIR = "chr"
    POLL_DEFAULT_SUBDIR = True

    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: bpy.props.StringProperty(options={'HIDDEN'}, subtype="DIR_PATH")

    def draw(self, context):
        """Draw name of selected model, if known."""
        if isinstance(context.space_data, bpy.types.SpaceFileBrowser):
            file_name = context.space_data.params.filename
            try:
                model_stem = int(file_name.split(".")[0][1:5])
            except ValueError:
                model_stem = None
        else:
            model_stem = None

        model_name = "<N/A>"
        if model_stem:
            settings = self.settings(context)
            if settings.is_game_ds1():
                model_name = DS1_CHARACTER_MODELS.get(model_stem, "<Unknown>")
            elif settings.is_game("DEMONS_SOULS"):
                model_name = DES_CHARACTER_MODELS.get(model_stem, "<Unknown>")
            elif settings.is_game("ELDEN_RING"):
                model_name = ER_CHARACTER_MODELS.get(model_stem, "<Unknown>")

        self.layout.label(text=f"Character: {model_name}")
        # Now draw standard properties for File Browser.
        super().draw(context)

    # Base `execute` method is fine.

    def post_process_flver(
        self,
        context: bpy.types.Context,
        settings: SoulstructSettings,
        import_settings: FLVERImportSettings,
        bl_flver: BlenderFLVER,
    ):
        if import_settings.add_name_suffix:
            if settings.is_game_ds1():
                model_dict = DS1_CHARACTER_MODELS
            elif settings.is_game("DEMONS_SOULS"):
                model_dict = DES_CHARACTER_MODELS
            else:
                model_dict = {}

            if model_dict:
                # Add character description to model name.
                try:
                    model_id = int(bl_flver.name[1:5])
                    model_desc = model_dict[model_id]
                    # Don't trigger full rename.
                    bl_flver.obj.name += f" <{model_desc}>"
                    bl_flver.armature.name += f" <{model_desc}>"
                except (ValueError, KeyError):
                    pass

    def get_collection(self, context: bpy.types.Context, file_directory_name: str):
        return find_or_create_collection(context.scene.collection, "Models", "Character Models")

    # We do NOT look anywhere else for character textures.


class ImportObjectFLVER(BaseFLVERImportOperator):
    """Shortcut for browsing for OBJBND Binders in game 'obj' directory."""
    bl_idname = "import_scene.object_flver"
    bl_label = "Import Object"
    bl_description = "Import object FLVER from an OBJBND in selected game 'obj' directory"

    filter_glob: bpy.props.StringProperty(
        default="*.objbnd;*.objbnd.dcx;",
        options={'HIDDEN'},
        maxlen=255,
    )

    DEFAULT_SUBDIR = "obj"

    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: bpy.props.StringProperty(options={'HIDDEN'}, subtype="DIR_PATH")

    @classmethod
    def poll(cls, context) -> bool:
        settings = cls.settings(context)
        if settings.is_game("ELDEN_RING"):
            return False  # has 'assets' instead
        return settings.has_import_dir_path("obj")

    # Base `execute` method is fine.

    def get_collection(self, context: bpy.types.Context, file_directory_name: str):
        return find_or_create_collection(context.scene.collection, "Models", "Object Models")

    def find_extra_textures(self, flver_source_path: Path, flver: FLVER, image_import_manager: ImageImportManager):
        """Some Objects lazily use textures from the map area they expect to be placed in."""
        map_dir = flver_source_path.parent.parent / "map"  # assume OBJBND is in 'obj' next to 'map' subdirectory
        image_import_manager.register_lazy_flver_map_textures(map_dir, flver)


class ImportAssetFLVER(BaseFLVERImportOperator):
    """Shortcut for browsing for GEOMBND Binders in game 'asset' directory."""
    bl_idname = "import_scene.asset_flver"
    bl_label = "Import Asset"
    bl_description = "Import asset FLVER from a GEOMBND in selected game 'asset' directory"

    filter_glob: bpy.props.StringProperty(
        default="*.geombnd;*.geombnd.dcx;",
        options={'HIDDEN'},
        maxlen=255,
    )

    DEFAULT_SUBDIR = "asset/aeg"

    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: bpy.props.StringProperty(options={'HIDDEN'}, subtype="DIR_PATH")

    @classmethod
    def poll(cls, context) -> bool:
        settings = cls.settings(context)
        if settings.game_variable_name != "ELDEN_RING":
            return False  # only Elden Ring has 'assets'
        return settings.has_import_dir_path("asset/aeg")

    # Base `execute` method is fine.

    def get_collection(self, context: bpy.types.Context, file_directory_name: str):
        return find_or_create_collection(context.scene.collection, "Models", "Asset Models")


class ImportEquipmentFLVER(BaseFLVERImportOperator):
    """Import weapon/armor FLVER from a `partsbnd` Binder.

    NOTE: Earlier versions of Soulstruct forced you to select an imported `c0000` model, and the mesh and dummies of
    this equipment FLVER would be parented to that model. However, this was actually destructive, as it prevented the
    user from viewing or editing the partial c0000 Armature that is actually present in the equipment FLVER.

    If you want to animate equipment with c0000 animations, you can simply set those animations to this FLVER -- the
    Armature bones should all be compatible.
    """
    bl_idname = "import_scene.equipment_flver"
    bl_label = "Import Equipment"
    bl_description = "Import equipment FLVER from a PARTSBND in selected game 'parts' directory"

    filter_glob: bpy.props.StringProperty(
        default="*.partsbnd;*.partsbnd.dcx;",
        options={'HIDDEN'},
        maxlen=255,
    )

    DEFAULT_SUBDIR = "parts"
    POLL_DEFAULT_SUBDIR = True

    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'}, )
    directory: bpy.props.StringProperty(options={'HIDDEN'}, subtype="DIR_PATH")

    # Base `execute` method is fine.

    def get_collection(self, context: bpy.types.Context, file_directory_name: str):
        return find_or_create_collection(context.scene.collection, "Models", "Equipment Models")

# endregion
