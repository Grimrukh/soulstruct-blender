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
    "QuickImportMapPieceFLVER",
    "QuickImportCharacterFLVER",
    "QuickImportObjectFLVER",
    "ImportEquipmentFLVER",
    "FLVERImportSettings",
    "FLVERImporter",
]

import math
import numpy as np
import re
import time
import traceback
import typing as tp
from dataclasses import dataclass, field
from pathlib import Path

import bmesh
import bpy
import bpy.ops
from bpy.props import StringProperty, FloatProperty, BoolProperty, EnumProperty, CollectionProperty
from bpy_extras.io_utils import ImportHelper
from mathutils import Vector, Matrix

from soulstruct.base.models.flver import FLVER, Dummy
from soulstruct.base.models.flver.mesh_tools import MergedMesh
from soulstruct.containers import Binder
from soulstruct.dcx import DCXType
from soulstruct.containers.tpf import TPFTexture, batch_get_tpf_texture_png_data
from soulstruct.utilities.maths import Vector3

from io_soulstruct.general import GlobalSettings, GameFiles, MTDBinderManager
from io_soulstruct.general.cached import get_cached_file
from io_soulstruct.utilities import *
from .utilities import *
from .materials import get_submesh_blender_material
from .textures.utilities import png_to_bl_image, TextureManager

if tp.TYPE_CHECKING:
    from soulstruct.darksouls1r.maps import MSB

FLVER_BINDER_RE = re.compile(r"^.*?\.(chr|obj|parts)bnd(\.dcx)?$")
MAP_NAME_RE = re.compile(r"^(m\d\d)_\d\d_\d\d_\d\d$")


class ImportFLVERMixin:

    # `LoggingOperator` type hints
    error: tp.Callable[[str], set[str]]
    warning: tp.Callable[[str], set[str]]
    info: tp.Callable[[str], set[str]]

    read_from_png_cache: BoolProperty(
        name="Read from PNG Cache",
        description="Read cached PNGs (instead of DDS files) from the above directory if available",
        default=True,
    )

    write_to_png_cache: BoolProperty(
        name="Write to PNG Cache",
        description="Write PNGs of any loaded textures (DDS files) to the above directory for future use",
        default=True,
    )

    find_game_tpfs: BoolProperty(
        name="Find Game TPF Files",
        description="Look for TPF (DDS) textures in known game locations for FLVER source type",
        default=True,
    )

    use_mtd_binder: BoolProperty(
        name="Use MTD Binder",
        description="Try to find MTD shaders in game 'mtd' folder to improve Blender shader accuracy",
        default=True,
    )

    material_blend_mode: EnumProperty(
        name="Alpha Blend Mode",
        description="Alpha mode to use for new single-texture FLVER materials",
        items=[
            ('OPAQUE', "Opaque", "Opaque Blend Mode"),
            ('CLIP', "Clip", "Clip Blend Mode"),
            ('HASHED', "Hashed", "Hashed Blend Mode"),
            ('BLEND', "Blend", "Sorted Blend Mode"),
        ],
        default="HASHED",
    )

    base_edit_bone_length: FloatProperty(
        name="Base Edit Bone Length",
        description="Length of edit bones corresponding to bone scale 1",
        default=0.2,
        min=0.01,
    )

    def get_import_settings(self, context, texture_manager: TextureManager):
        settings = GlobalSettings.get_scene_settings(context)
        return FLVERImportSettings(
            texture_manager=texture_manager,
            read_from_png_cache=self.read_from_png_cache,
            write_to_png_cache=self.write_to_png_cache,
            material_blend_mode=self.material_blend_mode,
            base_edit_bone_length=self.base_edit_bone_length,
            mtd_manager=settings.get_mtd_manager(context) if self.use_mtd_binder else None,
        )


class ImportFLVER(LoggingOperator, ImportHelper, ImportFLVERMixin):
    """This appears in the tooltip of the operator and in the generated docs."""
    bl_idname = "import_scene.flver"
    bl_label = "Import FLVER"
    bl_description = "Import a FromSoftware FLVER model file. Can import from BNDs and supports DCX-compressed files."

    filename_ext = ".flver"

    filter_glob: StringProperty(
        default="*.flver;*.flver.dcx;*.chrbnd;*.chrbnd.dcx;*.objbnd;*.objbnd.dcx;"
                "*.partsbnd;*.partsbnd.dcx;*.mapbnd;*.mapbnd.dcx;*.geombnd;*.geombnd.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'},
    )

    directory: StringProperty(
        options={'HIDDEN'},
    )

    def invoke(self, context, _event):
        """Set the initial directory based on Global Settings."""
        game_directory = GlobalSettings.get_scene_settings(context).game_directory
        if game_directory and Path(game_directory).is_dir():
            self.filepath = game_directory
        return super().invoke(context, _event)

    def execute(self, context):
        self.info("Executing FLVER import...")

        start_time = time.perf_counter()

        file_paths = [Path(self.directory, file.name) for file in self.files]
        flvers = []
        texture_manager = TextureManager()

        for file_path in file_paths:

            if FLVER_BINDER_RE.match(file_path.name):
                binder = Binder.from_path(file_path)
                flver = get_flver_from_binder(binder, file_path)
                if self.find_game_tpfs:
                    texture_manager.find_flver_textures(file_path, binder)
            else:  # e.g. loose Map Piece FLVER
                flver = FLVER.from_path(file_path)
                if self.find_game_tpfs:
                    texture_manager.find_flver_textures(file_path)
            flvers.append((file_path, flver))

        settings = bpy.context.scene.soulstruct_global_settings  # type: GlobalSettings
        settings.save_settings()
        importer = FLVERImporter(self, context, self.get_import_settings(context, texture_manager))

        for file_path, flver in flvers:

            try:
                name = file_path.name.split(".")[0]  # drop all extensions
                bl_armature, bl_mesh = importer.import_flver(flver, name=name)
            except Exception as ex:
                # Delete any objects created prior to exception.
                importer.abort_import()
                traceback.print_exc()  # for inspection in Blender console
                return self.error(f"Cannot import FLVER: {file_path.name}. Error: {ex}")

            # Select newly imported mesh.
            if bl_mesh:
                self.set_active_obj(bl_mesh)

        self.info(f"Imported {len(flvers)} FLVERs in {time.perf_counter() - start_time:.3f} seconds.")

        return {"FINISHED"}


class QuickImportMapPieceFLVER(LoggingOperator, ImportFLVERMixin):
    """Import a map piece FLVER from the current selected value of listed game map piece FLVERs."""
    bl_idname = "import_scene.quick_map_piece_flver"
    bl_label = "Import Map Piece"
    bl_description = "Import selected map piece FLVER from game map directory"

    @classmethod
    def poll(cls, context):
        game_lists = context.scene.game_files  # type: GameFiles
        return game_lists.map_piece not in {"", "0"}

    def execute(self, context):

        start_time = time.perf_counter()

        game_lists = context.scene.game_files  # type: GameFiles

        settings = GlobalSettings.get_scene_settings(context)
        settings.save_settings()

        transform = None  # type: Transform | None

        if settings.msb_import_mode:
            try:
                part_name, flver_stem = game_lists.map_piece.split("|")
            except ValueError:
                return self.error("Invalid MSB map piece selection.")
            msb_path = settings.get_selected_map_msb_path(context)

            # Get MSB part transform.
            msb = get_cached_file(msb_path, settings.get_game_msb_class(context))  # type: MSB
            map_piece_part = msb.map_pieces.find_entry_name(part_name)
            transform = Transform.from_msb_part(map_piece_part)

            dcx_type = settings.resolve_dcx_type("Auto", "FLVER", False, context)
            flver_path = Path(settings.game_directory, "map", settings.map_stem, f"{flver_stem}.flver")
            flver_path = dcx_type.process_path(flver_path)

            bl_name = part_name
        else:
            flver_path = game_lists.map_piece
            flver_stem = Path(flver_path).name.split(".")[0]
            if not flver_path:
                return self.error("No map piece FLVER selected.")
            flver_path = Path(flver_path)
            if not flver_path.is_file():
                return self.error(f"Map piece FLVER path is not a file: {flver_path}. Try refreshing game file lists.")
            bl_name = flver_path.name.split(".")[0]  # drop all extensions

        self.info(f"Importing map piece FLVER: {flver_path}")

        texture_manager = TextureManager()

        flver = FLVER.from_path(flver_path)
        if self.find_game_tpfs:
            texture_manager.find_flver_textures(flver_path)

        # Check all textures in FLVER for specific map 'mAA_' prefix textures and register TPFBHDs in those maps.
        area_re = re.compile(r"^m\d\d_")
        texture_map_areas = {
            texture_path.stem[:3]
            for texture_path in flver.get_all_texture_paths()
            if re.match(area_re, texture_path.stem)
        }
        for map_area in texture_map_areas:
            map_area_dir = (flver_path.parent / f"../{map_area}").resolve()
            texture_manager.find_specific_map_textures(map_area_dir)

        importer = FLVERImporter(self, context, self.get_import_settings(context, texture_manager))

        try:
            bl_armature, bl_mesh = importer.import_flver(flver, name=bl_name, transform=transform)
        except Exception as ex:
            # Delete any objects created prior to exception.
            importer.abort_import()
            traceback.print_exc()  # for inspection in Blender console
            return self.error(f"Cannot import FLVER: {flver_path.name}. Error: {ex}")

        # Set 'Model File Stem' if in MSB Import Mode. (This isn't used in MSB Export Mode, which gets its model from
        # the MSB part, but is a generally useful tracker of the FLVER file stem.)
        if transform is not None:
            bl_mesh["Model File Stem"] = flver_stem

        # Find or create Map Piece parent.
        map_piece_parent = find_or_create_bl_empty(f"{settings.map_stem} Map Pieces", context)
        bl_armature.parent = map_piece_parent

        # Select newly imported armature.
        if bl_armature:
            self.set_active_obj(bl_armature)

        self.info(f"Imported map piece FLVER in {time.perf_counter() - start_time:.3f} seconds.")

        return {"FINISHED"}


class QuickImportCharacterFLVER(LoggingOperator, ImportFLVERMixin):
    """Import a character FLVER from the current selected value of listed game map CHRBNDs."""
    bl_idname = "import_scene.quick_character_flver"
    bl_label = "Import Character"
    bl_description = "Import selected character's FLVER from game CHRBND"

    @classmethod
    def poll(cls, context):
        game_lists = context.scene.game_files  # type: GameFiles
        return game_lists.chrbnd not in {"", "0"}

    def execute(self, context):
        game_lists = context.scene.game_files  # type: GameFiles

        chrbnd_path = game_lists.chrbnd
        if not chrbnd_path:
            return self.error("No CHRBND selected.")
        chrbnd_path = Path(chrbnd_path)
        if not chrbnd_path.is_file():
            return self.error(f"CHRBND path is not a file: {chrbnd_path}.")

        self.info(f"Importing FLVER from CHRBND: {chrbnd_path}")

        chrbnd = Binder.from_path(chrbnd_path)
        flver = get_flver_from_binder(chrbnd, chrbnd_path)
        texture_manager = TextureManager()
        if self.find_game_tpfs:
            texture_manager.find_flver_textures(chrbnd_path, chrbnd)

        settings = bpy.context.scene.soulstruct_global_settings  # type: GlobalSettings
        settings.save_settings()

        importer = FLVERImporter(self, context, self.get_import_settings(context, texture_manager))

        transform = None  # type: Transform | None

        try:
            name = chrbnd_path.name.split(".")[0]  # drop all extensions
            bl_armature, bl_mesh = importer.import_flver(flver, name=name, transform=transform)
        except Exception as ex:
            # Delete any objects created prior to exception.
            importer.abort_import()
            traceback.print_exc()  # for inspection in Blender console
            return self.error(f"Cannot import FLVER from CHRBND: {chrbnd_path.name}. Error: {ex}")

        # Select newly imported mesh.
        if bl_mesh:
            self.set_active_obj(bl_mesh)

        return {"FINISHED"}


class QuickImportObjectFLVER(LoggingOperator, ImportFLVERMixin):
    """Import all object FLVERs from the current selected value of listed game map OBJBNDs."""
    bl_idname = "import_scene.quick_objbnd_flver"
    bl_label = "Import Object"
    bl_description = "Import selected object's FLVERs from game OBJBND"

    @classmethod
    def poll(cls, context):
        game_files = context.scene.game_files  # type: GameFiles
        settings = GlobalSettings.get_scene_settings(context)
        return settings.game_directory != "" and game_files.objbnd_name != ""

    def execute(self, context):
        game_files = context.scene.game_files  # type: GameFiles
        settings = GlobalSettings.get_scene_settings(context)

        if not settings.game_directory:
            return self.error("No game directory selected.")

        objbnd_name = game_files.objbnd_name
        if not objbnd_name:
            return self.error("No OBJBND name given.")

        objbnd_name = objbnd_name.removesuffix(".dcx").removesuffix(".objbnd") + ".objbnd"
        if GlobalSettings.resolve_dcx_type("Auto", "Binder", False, context) != DCXType.Null:
            objbnd_name += ".dcx"

        objbnd_path = Path(settings.game_directory, "obj", objbnd_name)
        if not objbnd_path.is_file():
            return self.error(f"OBJBND path does not exist: {objbnd_path}")

        self.info(f"Importing FLVERs from OBJBND: {objbnd_path}")

        objbnd = Binder.from_path(objbnd_path)
        flver_entries = objbnd.find_entries_matching_name(r".*\.flver(\.dcx)?")
        if not flver_entries:
            return self.error(f"No FLVERs found in OBJBND: {objbnd_path}")
        flvers = [
            (entry.minimal_stem, FLVER.from_binder_entry(entry)) for entry in flver_entries
        ]
        texture_manager = TextureManager()
        if self.find_game_tpfs:
            texture_manager.find_flver_textures(objbnd_path, objbnd)

        settings = bpy.context.scene.soulstruct_global_settings  # type: GlobalSettings
        settings.save_settings()

        importer = FLVERImporter(self, context, self.get_import_settings(context, texture_manager))

        for name, flver in flvers:
            try:
                bl_armature, bl_mesh = importer.import_flver(flver, name=name)
            except Exception as ex:
                # Delete any objects created prior to exception.
                importer.abort_import()
                traceback.print_exc()  # for inspection in Blender console
                return self.error(f"Cannot import FLVER from CHRBND: {objbnd_path.name}. Error: {ex}")

            # Select newly imported mesh.
            if bl_mesh:
                self.set_active_obj(bl_mesh)

        return {"FINISHED"}


class ImportEquipmentFLVER(LoggingOperator, ImportHelper, ImportFLVERMixin):
    """Import weapon/armor FLVER from a `partsbnd` binder and attach it to selected armature (c0000)."""
    bl_idname = "import_scene.equipment_flver"
    bl_label = "Import Equipment FLVER"
    bl_description = "Import a FromSoftware FLVER equipment model file from a PARTSBND file and attach to c0000."

    filename_ext = ".partsbnd"

    filter_glob: StringProperty(
        default="*.flver;*.flver.dcx;*.partsbnd;*.partsbnd.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'},
    )

    directory: StringProperty(
        options={'HIDDEN'},
    )

    @classmethod
    def poll(cls, context):
        """Animation's rigged armature must be selected (to extract bone names)."""
        if len(context.selected_objects) != 1:
            return False
        # TODO: Could check for c0000 bones specifically.
        obj = context.selected_objects[0]
        return obj.type == "ARMATURE"

    def invoke(self, context, _event):
        """Set the initial directory."""
        game_directory = GlobalSettings.get_scene_settings(context).game_directory
        if game_directory:
            if (parts_dir := Path(game_directory, "parts")).is_dir():
                self.filepath = str(parts_dir)
            elif Path(game_directory).is_dir():
                self.filepath = game_directory
        return super().invoke(context, _event)

    def execute(self, context):
        self.info("Executing Equipment FLVER import...")

        settings = bpy.context.scene.soulstruct_global_settings  # type: GlobalSettings
        settings.save_settings()

        c0000_armature = context.selected_objects[0]
        if c0000_armature.type == "MESH":
            # Search children for first armature.
            for child in c0000_armature.children:
                if child.type == "ARMATURE":
                    c0000_armature = child
                    break
            else:
                return self.error("Selected object is not an armature or does not have an armature child.")

        file_paths = [Path(self.directory, file.name) for file in self.files]
        flvers = []
        texture_manager = TextureManager()

        for file_path in file_paths:

            if FLVER_BINDER_RE.match(file_path.name):
                binder = Binder.from_path(file_path)
                flver = get_flver_from_binder(binder, file_path)
                if self.find_game_tpfs:
                    texture_manager.find_flver_textures(file_path, binder)
            else:  # loose equipment FLVER is unusual but supported, but TPFs may not be found
                flver = FLVER.from_path(file_path)
                if self.find_game_tpfs:
                    texture_manager.find_flver_textures(file_path)
                # No loose TPF sources (nowhere to look).
            flvers.append((file_path, flver))

        importer = FLVERImporter(self, context, self.get_import_settings(context, texture_manager))

        for file_path, flver in flvers:
            name = file_path.name.split(".")[0]  # drop all extensions
            try:
                bl_armature, bl_mesh = importer.import_flver(flver, name=name, existing_armature=c0000_armature)
            except Exception as ex:
                importer.abort_import()
                traceback.print_exc()  # for inspection in Blender console
                return self.error(f"Cannot import equipment FLVER: {file_path.name}. Error: {ex}")

            # Select newly imported mesh.
            if bl_mesh:
                self.set_active_obj(bl_mesh)

        return {"FINISHED"}


@dataclass(slots=True)
class FLVERImportSettings:
    """Settings for a batch of FLVER imports."""

    texture_manager: TextureManager = None
    read_from_png_cache: bool = True
    write_to_png_cache: bool = True
    material_blend_mode: str = "HASHED"
    base_edit_bone_length: float = 0.2
    mtd_manager: MTDBinderManager | None = None


@dataclass(slots=True)
class FLVERImporter:
    """Manages imports for a batch of FLVER files using the same settings.

    Call `import_flver()` to import a single FLVER file.
    """

    operator: LoggingOperator
    context: bpy.types.Context
    settings: FLVERImportSettings

    flver: FLVER | None = None  # current FLVER being imported
    name: str = ""  # name of root Blender mesh object that will be created
    bl_bone_names: list[str] = field(default_factory=list)  # list of Blender bone names in order of FLVER bones
    new_objs: list[bpy.types.Object] = field(default_factory=list)  # all new objects created during import
    new_images: list[bpy.types.Image] = field(default_factory=list)  # all new images created during import
    new_materials: list[bpy.types.Material] = field(default_factory=list)  # all new materials created during import

    def abort_import(self):
        """Delete all Blender objects, images, and materials created during this import."""
        for obj in self.new_objs:
            try:
                bpy.data.objects.remove(obj)
            except ReferenceError:
                pass
        for img in self.new_images:
            try:
                bpy.data.images.remove(img)
            except ReferenceError:
                pass
        for mat in self.new_materials:
            try:
                bpy.data.materials.remove(mat)
            except ReferenceError:
                pass
        self.flver = None
        self.name = ""
        self.bl_bone_names.clear()
        self.new_objs.clear()
        self.new_images.clear()
        self.new_materials.clear()

    def import_flver(
        self, flver: FLVER, name: str, transform: tp.Optional[Transform] = None, existing_armature=None
    ) -> tuple[bpy.types.ArmatureObject, bpy.types.MeshObject] | None:
        """Read a FLVER into a Blender mesh and Armature.

        If `existing_armature` is passed, the skeleton of `flver` will be ignored, and its mesh will be rigged to the
        bones of `existing_armature` instead (e.g. for parenting equipment models to c0000). Dummies should generally
        not be present in these FLVERs, but if they do exist, they will also be parented to the armature with their
        original FLVER name as a prefix to distinguish them from the dummies of `existing_armature`.
        """
        start_time = time.perf_counter()

        self.flver = flver
        self.name = name
        self.bl_bone_names.clear()
        self.new_objs.clear()
        self.new_images.clear()
        self.new_materials.clear()
        settings = self.settings

        # Create FLVER bone index -> Blender bone name dictionary. (Blender names are UTF-8.)
        # This is done even when `existing_armature` is given, as the order of bones in this new FLVER may be different
        # and the vertex weight indices need to be directed to the names of bones in `existing_armature` correctly.
        for bone in flver.bones:
            # Just using actual bone names to avoid the need for parsing rules on export. However, duplicate names
            # need to be handled with suffixes.
            bl_bone_name = f"{bone.name} <DUPE>" if bone.name in self.bl_bone_names else bone.name
            self.bl_bone_names.append(bl_bone_name)

        if flver.gx_lists:
            self.warning(
                f"FLVER {self.name} has GX Lists, which are not yet supported by Soulstruct for Blender. "
                f"They will be lost."
            )

        png_cache_directory = GlobalSettings.get_scene_settings(self.context).png_cache_directory
        if settings.texture_manager or png_cache_directory:
            p = time.perf_counter()
            self.new_images = self.load_texture_images(settings.texture_manager)
            self.operator.info(f"Loaded {len(self.new_images)} textures in {time.perf_counter() - p:.3f} seconds.")
        else:
            self.warning("No TPF files or DDS dump folder given. No textures loaded for FLVER.")

        # Maps FLVER submeshes to their Blender material index to store per-face in the merged mesh.
        # Submeshes that originally indexed the same FLVER material may have different Blender 'variant' materials that
        # hold certain Submesh/FaceSet properties like `use_backface_culling`.
        # Conversely, Submeshes that only serve to handle per-submesh bone maximums (e.g. 38 in DS1) will use the same
        # Blender material and be split again automatically on export (but likely not in an indentical way!).
        submesh_bl_material_indices = []

        # Map FLVER material hashes to the indices of variant Blender materials sourced from them, which hold distinct
        # Submesh/FaceSet properties.
        flver_material_hash_variants = {}

        # Maps FLVER material hashes to their MTD info.
        flver_material_mtd_infos = {}
        for material in flver.materials:
            material_hash = hash(material)
            if material_hash in flver_material_mtd_infos:
                continue
            mtd_info = self.get_mtd_info(material.mtd_name, settings.mtd_manager)
            flver_material_mtd_infos[material_hash] = mtd_info

        self.new_materials = []
        for submesh in flver.submeshes:
            material = submesh.material
            material_hash = hash(material)  # NOTE: if there are duplicate FLVER materials, this will combine them
            if material_hash not in flver_material_hash_variants:
                # First time this FLVER material has been encountered. Create it in Blender now.
                # NOTE: Vanilla material names are unused and essentially worthless. They can also be the same for
                #  materials that actually use different lightmaps, EVEN INSIDE the same FLVER model. Names are changed
                #  here to just reflect the index. The original name is NOT kept to avoid stacking up formatting on
                #  export/import and because it is so useless anyway.
                flver_material_index = len(flver_material_hash_variants)
                bl_material_index = len(self.new_materials)
                bl_material = get_submesh_blender_material(
                    self.operator,
                    material,
                    material_name=f"{self.name} Material {flver_material_index}",  # no Variant suffix
                    mtd_info=flver_material_mtd_infos[material_hash],
                    submesh=submesh,
                    blend_mode=settings.material_blend_mode,
                )  # type: bpy.types.Material

                submesh_bl_material_indices.append(bl_material_index)
                flver_material_hash_variants[material_hash] = [bl_material_index]
                self.new_materials.append(bl_material)

                continue

            existing_variant_bl_indices = flver_material_hash_variants[material_hash]

            # Check if Blender material needs to be duplicated as a variant with different Mesh properties.
            found_existing_material = False
            for existing_bl_material_index in existing_variant_bl_indices:
                # NOTE: We do not care about enforcing any maximum submesh local bone count in Blender! The FLVER
                # exporter will create additional split submeshes as necessary for that.
                existing_bl_material = self.new_materials[existing_bl_material_index]
                if (
                    bool(existing_bl_material["Is Bind Pose"]) == submesh.is_bind_pose
                    and existing_bl_material["Default Bone Index"] == submesh.default_bone_index
                    and existing_bl_material["Face Set Count"] == len(submesh.face_sets)
                    and existing_bl_material.use_backface_culling == submesh.use_backface_culling
                ):
                    # Blender material already exists with the same Mesh properties. No new variant neeed.
                    submesh_bl_material_indices.append(existing_bl_material_index)
                    found_existing_material = True
                    break

            if found_existing_material:
                continue

            # No match found. New Blender material variant is needed to hold unique submesh data.
            variant_index = len(existing_variant_bl_indices)
            first_material = self.new_materials[existing_variant_bl_indices[0]]
            variant_name = first_material.name + f" <Variant {variant_index}>"
            bl_material = get_submesh_blender_material(
                self.operator,
                material,
                material_name=variant_name,
                mtd_info=flver_material_mtd_infos[material_hash],
                submesh=submesh,
                blend_mode=settings.material_blend_mode,
            )  # type: bpy.types.Material

            new_bl_material_index = len(self.new_materials)
            submesh_bl_material_indices.append(new_bl_material_index)
            flver_material_hash_variants[material_hash].append(new_bl_material_index)
            self.new_materials.append(bl_material)

        # UV layer names that each submesh should use (dependent on its FLVER material).
        submesh_uv_layer_names = []
        flver_material_uv_layer_names = {}
        for submesh in flver.submeshes:
            material_hash = hash(submesh.material)
            submesh_uv_layer_names.append(flver_material_uv_layer_names.setdefault(
                material_hash, flver_material_mtd_infos[material_hash].get_uv_layer_names()
            ))

        bl_flver_mesh = self.create_flver_mesh(
            flver, self.name, submesh_bl_material_indices, submesh_uv_layer_names
        )

        # Assign basic FLVER header information as custom props.
        # TODO: Configure a full-exporter dropdown/choice of game version that defaults as many of these as possible.
        bl_flver_mesh["Is Big Endian"] = flver.big_endian  # bool
        bl_flver_mesh["Version"] = flver.version.name  # str
        bl_flver_mesh["Unicode"] = flver.unicode  # bool
        bl_flver_mesh["Unk x4a"] = flver.unk_x4a  # bool
        bl_flver_mesh["Unk x4c"] = flver.unk_x4c  # int
        bl_flver_mesh["Unk x5c"] = flver.unk_x5c  # int
        bl_flver_mesh["Unk x5d"] = flver.unk_x5d  # int
        bl_flver_mesh["Unk x68"] = flver.unk_x68  # int

        if existing_armature:
            # Do not create an armature for this FLVER; use `existing_armature` instead.
            bl_armature_obj = existing_armature
            # Parts FLVERs sometimes have extra non-c0000 bones (e.g. multiple bones with their own name), which we will
            # delete here, to ensure that any attempt to use them in the new meshes raises an error.
            armature_bone_names = [bone.name for bone in bl_armature_obj.data.bones]
            for bone_name in tuple(self.bl_bone_names):
                if bone_name not in armature_bone_names:
                    self.bl_bone_names.remove(bone_name)
            dummy_prefix = self.name  # we generally don't expect any dummies, but will distinguish them with this
            # TODO: warn if `transform` is not None? invalid with existing armature?
        else:
            # Create a new armature for this FLVER.
            bl_armature_obj = self.create_armature(settings.base_edit_bone_length)
            dummy_prefix = ""
            self.new_objs.append(bl_armature_obj)

            if transform is not None:
                bl_armature_obj.location = transform.bl_translate
                bl_armature_obj.rotation_euler = transform.bl_rotate
                bl_armature_obj.scale = transform.bl_scale

        # Parent mesh to armature. This is critical for proper animation behavior (especially with root motion).
        bl_flver_mesh.parent = bl_armature_obj

        self.operator.set_active_obj(bl_flver_mesh)
        bpy.ops.object.modifier_add(type="ARMATURE")
        armature_mod = bl_flver_mesh.modifiers["Armature"]
        armature_mod.object = bl_armature_obj
        armature_mod.show_in_editmode = True
        armature_mod.show_on_cage = True

        for i, dummy in enumerate(flver.dummies):
            self.create_dummy(dummy, index=i, bl_armature=bl_armature_obj, dummy_prefix=dummy_prefix)

        self.operator.info(f"Created FLVER Blender mesh '{name}' in {time.perf_counter() - start_time:.3f} seconds.")

        return bl_armature_obj, bl_flver_mesh  # might be used by other importers

    def get_mtd_info(self, mtd_name: str, mtd_manager: MTDBinderManager = None) -> MTDInfo:
        """Get `MTDInfo` for a FLVER material, which is needed for both material creation and assignment of vertex UV
        data to the correct Blender UV data layer during mesh creation.
        """
        if not mtd_manager:
            return MTDInfo.from_mtd_name(mtd_name)

        # Use real MTD file (much less guesswork).
        try:
            mtd = mtd_manager[mtd_name]
        except KeyError:
            self.warning(f"Could not find MTD '{mtd_name}' in MTD dict. Guessing info from name.")
            return MTDInfo.from_mtd_name(mtd_name)
        return MTDInfo.from_mtd(mtd)

    def create_armature(self, base_edit_bone_length: float) -> bpy.types.Object:
        """Create a new Blender armature to serve as the parent object for the entire FLVER."""

        self.operator.to_object_mode()
        self.operator.deselect_all()

        bl_armature_data = bpy.data.armatures.new(f"{self.name} Armature")
        bl_armature_obj = self.create_obj(f"{self.name}", bl_armature_data)
        self.create_bones(bl_armature_obj, base_edit_bone_length)

        return bl_armature_obj

    def load_texture_images(self, texture_manager: TextureManager = None) -> list[bpy.types.Image]:
        """Load texture images from either `png_cache` folder or TPFs found with `texture_manager`.

        Will NEVER load an image that is already in Blender's data, regardless of image type (identified by stem only).
        """
        bl_image_stems = {Path(image.name).stem for image in bpy.data.images}
        new_loaded_images = []
        settings = self.settings
        png_cache_directory = GlobalSettings.get_scene_settings(self.context).png_cache_directory

        textures_to_load = {}  # type: dict[str, TPFTexture]
        for texture_path in self.flver.get_all_texture_paths():
            texture_stem = texture_path.stem
            if texture_stem in bl_image_stems:
                continue  # already loaded
            if texture_stem in textures_to_load:
                continue  # already queued to load below

            if settings.read_from_png_cache and png_cache_directory:
                png_path = Path(png_cache_directory, f"{texture_stem}.png")
                if png_path.is_file():
                    bl_image = bpy.data.images.load(str(png_path))
                    new_loaded_images.append(bl_image)
                    bl_image_stems.add(texture_stem)
                    continue

            if texture_manager:
                try:
                    texture = texture_manager.get_flver_texture(texture_stem)
                except KeyError as ex:
                    self.warning(str(ex))
                else:
                    textures_to_load[texture_stem] = texture
                    continue

            self.warning(f"Could not find TPF or cached PNG '{texture_path.stem}' for FLVER '{self.name}'.")

        if textures_to_load:
            for texture_stem in textures_to_load:
                self.operator.info(f"Loading texture into Blender: {texture_stem}")
            from time import perf_counter
            t = perf_counter()
            all_png_data = batch_get_tpf_texture_png_data(list(textures_to_load.values()))
            write_png_directory = (
                Path(png_cache_directory) if png_cache_directory and settings.write_to_png_cache else None
            )
            print(f"# INFO: Converted PNG images in {perf_counter() - t} s (cached = {settings.write_to_png_cache})")
            for texture_stem, png_data in zip(textures_to_load.keys(), all_png_data):
                bl_image = png_to_bl_image(texture_stem, png_data, write_png_directory)
                new_loaded_images.append(bl_image)

        return new_loaded_images

    def create_flver_mesh(
        self,
        flver: FLVER,
        name: str,
        submesh_bl_material_indices: list[int],
        submesh_uv_layer_names: list[list[str]],
    ) -> bpy.types.MeshObject:
        """Create a single Blender mesh that combines all FLVER submeshes, using multiple material slots.

        NOTE: FLVER (for DS1 at least) supports a maximum of 38 bones per sub-mesh. When this maximum is reached, a new
        FLVER submesh is created. All of these sub-meshes are unified in Blender under the same material slot, and will
        be split again on export as needed.

        Some FLVER submeshes also use the same material, but have different `Mesh` or `FaceSet` properties such as
        `use_backface_culling`. Backface culling is a material option in Blender, so these submeshes will use different
        Blender material 'variants' even though they use the same FLVER material. The FLVER exporter will start by
        creating a FLVER material for every Blender material slot, then unify any identical FLVER material instances and
        redirect any differences like `use_backface_culling` or `is_bind_pose` to the FLVER mesh.

        Breakdown:
            - Blender stores POSITION, BONE WEIGHTS, and BONE INDICES on vertices. Any differences here will require
            genuine vertex duplication in Blender. (Of course, vertices at the same position in the same sub-mesh should
            essentially ALWAYS have the same bone weights and indices.)
            - Blender stores MATERIAL SLOT INDEX on faces. This is how different FLVER submeshes are represented.
            - Blender stores UV COORDINATES, VERTEX COLORS, and NORMALS on face loops ('vertex instances'). This gels
            with what FLVER meshes want to do.
            - Blender does not import tangents or bitangents. These are calculated on export.
        """
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        # Armature parent object uses simply `name`. Mesh data/object has 'Mesh' suffix.
        bl_mesh = bpy.data.meshes.new(name=f"{name} Mesh")

        for material in self.new_materials:
            bl_mesh.materials.append(material)

        if any(mesh.invalid_layout for mesh in flver.submeshes):
            # Corrupted sub-meshes. Leave empty.
            # TODO: Should be able to handle known cases of this by redirecting to the correct vertex buffers.
            # noinspection PyTypeChecker
            return self.create_obj(f"{name} Mesh <INVALID>", bl_mesh)

        bl_vert_bone_weights, bl_vert_bone_indices = self.create_bm_mesh(
            bl_mesh,
            flver,
            submesh_bl_material_indices,
            submesh_uv_layer_names,
        )

        # noinspection PyTypeChecker
        bl_mesh_obj = self.create_obj(f"{name} Mesh", bl_mesh)  # type: bpy.types.MeshObject

        self.create_bone_vertex_groups(bl_mesh_obj, bl_vert_bone_weights, bl_vert_bone_indices)

        return bl_mesh_obj

    def create_bm_mesh(
        self,
        bl_mesh: bpy.types.Mesh,
        flver: FLVER,
        submesh_bl_material_indices: list[int],
        flver_material_uv_layer_names: list[list[str]],
    ) -> tuple[np.ndarray, np.ndarray]:
        """BMesh is more efficient for mesh construction and loop data layer assignment.

        Returns two arrays of bone indices and bone weights for the created Blender vertices.
        """

        p = time.perf_counter()
        # Create merged mesh. Degenerate/duplicate faces are left for Blender to handle.
        merged_mesh = MergedMesh.from_flver(
            flver,
            submesh_bl_material_indices,
            discard_degenerate_faces=False,
            discard_duplicate_faces=False,
            material_uv_layers=flver_material_uv_layer_names,
        )

        merged_mesh.swap_vertex_yz(tangents=False, bitangents=False)
        merged_mesh.invert_vertex_uv(invert_u=False, invert_v=True)
        merged_mesh.normalize_normals()
        self.operator.info(f"Merged FLVER submeshes in {time.perf_counter() - p} s")

        # Create UV and vertex color data layers.
        for uv_layer_name in merged_mesh.uv_layers:
            bl_mesh.uv_layers.new(name=uv_layer_name, do_init=False)
        # TODO: Support multiple colors.
        bl_mesh.vertex_colors.new(name="VertexColors")

        bm = bmesh.new()
        bm.from_mesh(bl_mesh)  # bring over UV and vertex color data layers

        # Get data layer accessors.
        loop_uv_layers = [bm.loops.layers.uv[uv_layer_name] for uv_layer_name in merged_mesh.uv_layers]
        loop_colors_layer = bm.loops.layers.color["VertexColors"]

        # Unfortunately, we have to assign UV and color data per loop object in BMesh, so there's no way to take
        # advantage of NumPy vectorization here. It's therefore faster to get our loop UV and color data now as lists
        # rather than repeatedly index the NumPy array.
        # TODO: Maybe worth a little performance test to see if it's better to assign all this data after all faces are
        #  created, rather than in loop triplets after each face.
        loop_uvs_list = [uv_array.tolist() for uv_array in merged_mesh.loop_uvs]
        loop_colors_list = merged_mesh.loop_vertex_colors[0].tolist()  # TODO: support multiple colors
        if len(merged_mesh.loop_vertex_colors) > 1:
            self.warning("More than one vertex color layer detected. Only the first will be imported into Blender!")

        # CREATE BLENDER VERTICES
        for position in merged_mesh.vertex_data["position"]:
            bm.verts.new(position)
        bm.verts.ensure_lookup_table()

        bl_loop_normal_indices = []  # need to filter out loops of degenerate faces

        # TODO: go back to reporting occurrences per-submesh (`faces[:, 3]`)?
        duplicate_face_count = 0
        degenerate_face_count = 0

        p = time.perf_counter()
        for face in merged_mesh.faces:

            loop_indices = face[:3]
            vertex_indices = merged_mesh.loop_vertex_indices[loop_indices]
            bm_verts = [bm.verts[v_i] for v_i in vertex_indices]

            try:
                bm_face = bm.faces.new(bm_verts)
            except ValueError as ex:
                if "face already exists" in str(ex):
                    # This is a duplicate face (happens rarely in vanilla FLVERs). We can ignore it.
                    # No lasting harm done as, by assertion, no new BMesh vertices were created above. We just need
                    # to remove the last three normals.
                    duplicate_face_count += 1
                    continue
                if "found the same (BMVert) used multiple times" in str(ex):
                    # Degenerate FLVER face (e.g. a line or point). These are not supported by Blender.
                    degenerate_face_count += 1
                    continue

                print(f"Unhandled error for BMFace. Vertices: {[v.co for v in bm_verts]}")
                raise ex

            bm_face.material_index = face[3]

            # TODO: Could potentially speed this up with `foreach_set` on `bm.loops` afterward, but would still need
            #  to record all FLVER loop indices that actually made it into BM faces (to filter out degenerate faces).
            #  Very minor optimization though (if at all).
            for bm_loop, loop_index in zip(bm_face.loops, loop_indices):
                for uv_i, (uv_list, uv_layer) in enumerate(zip(loop_uvs_list, loop_uv_layers)):
                    bm_loop[uv_layer].uv = uv_list[loop_index]
                bm_loop[loop_colors_layer] = loop_colors_list[loop_index]  # TODO: more colors
                bl_loop_normal_indices.append(loop_index)

        self.operator.info(f"Created Blender mesh faces in {time.perf_counter() - p} s")

        if degenerate_face_count or duplicate_face_count:
            self.warning(
                f"{degenerate_face_count} degenerate and {duplicate_face_count} duplicate faces were ignored during "
                f"FLVER import."
            )

        # TODO: Delete all unused vertices at this point?

        bm.to_mesh(bl_mesh)
        bm.free()

        # Enable custom split normals and assign them.
        bl_mesh.create_normals_split()
        bl_mesh.normals_split_custom_set(merged_mesh.loop_normals[bl_loop_normal_indices])  # one normal per loop
        bl_mesh.use_auto_smooth = True  # required for custom split normals to actually be used (rather than just face)
        bl_mesh.calc_normals_split()  # copy custom split normal data into API mesh loops

        bl_mesh.update()

        return merged_mesh.vertex_data["bone_weights"], merged_mesh.vertex_data["bone_indices"]

    def create_bone_vertex_groups(
        self,
        bl_mesh_obj: bpy.types.Object,
        bl_vert_bone_weights: np.ndarray,
        bl_vert_bone_indices: np.ndarray,
    ):
        # Naming a vertex group after a Blender bone will automatically link it in the Armature modifier below.
        bone_vertex_groups = [
            bl_mesh_obj.vertex_groups.new(name=bone_name)
            for bone_name in self.bl_bone_names
        ]  # type: list[bpy.types.VertexGroup]

        # Awkwardly, we need a separate call to `VertexGroups[bone_index].add(indices, weight)` for each combination
        # of `bone_index` and `weight`, so the dictionary keys constructed above are a tuple of those two to minimize
        # the number of Blender group `add()` calls needed at the end of this function.
        bone_vertex_group_indices = {}  # type: dict[tuple[int, float], list[int]]

        p = time.perf_counter()
        # TODO: Can probably be vectorized better with NumPy.
        for v_i, (bone_indices, bone_weights) in enumerate(zip(bl_vert_bone_indices, bl_vert_bone_weights)):
            if all(weight == 0.0 for weight in bone_weights) and len(set(bone_indices)) == 1:
                # Map Piece FLVERs use a single duplicated index and no weights.
                # TODO: May be able to assert that this is ALWAYS true for ALL vertices in map pieces.
                v_bone_index = bone_indices[0]
                bone_vertex_group_indices.setdefault((v_bone_index, 1.0), []).append(v_i)
            else:
                # Standard multi-bone weighting.
                for v_bone_index, v_bone_weight in zip(bone_indices, bone_weights):
                    if v_bone_weight == 0.0:
                        continue
                    bone_vertex_group_indices.setdefault((v_bone_index, v_bone_weight), []).append(v_i)

        for (bone_index, bone_weight), bone_vertices in bone_vertex_group_indices.items():
            bone_vertex_groups[bone_index].add(bone_vertices, bone_weight, "ADD")

        self.operator.info(f"Assigned Blender vertex groups to bones in {time.perf_counter() - p} s")

    def create_bones(self, bl_armature_obj: bpy.types.Object, base_edit_bone_length: float):
        """Create FLVER bones on given `bl_armature_obj` in Blender.

        Bones can be a little confusing in Blender. See:
            https://docs.blender.org/api/blender_python_api_2_71_release/info_gotcha.html#editbones-posebones-bone-bones

        The short story is that the "resting state" of each bone, including its head and tail position, is created in
        EDIT mode (as `EditBone` instances). This data defines the "zero deformation" state of the mesh with regard to
        bone weights, and will typically not be edited again when posing/animating a mesh that is rigged to this
        Armature. Instead, the bones are accessed as `PoseBone` instances in POSE mode, where they are treated like
        objects with transform data.

        If a FLVER bone has a parent bone, its FLVER transform is given relative to its parent's frame of reference.
        Determining the final position of any given bone in world space therefore requires all of its parents'
        transforms to be accumulated up to the root. (The same is true for HKX animation coordinates, which are local
        bone transformations in the same coordinate system.)

        Note that while bones are typically used for obvious animation cases in characters, objects, and parts (e.g.
        armor/weapons), they are also occasionally used in a fairly basic way by map pieces to position certain vertices
        in certain meshes. When this happens, so far, the bones have always been root bones, and basically function as
        shifted origins for the coordinates of certain vertices. I strongly suspect, but have not absolutely confirmed,
        that the `is_bind_pose` attribute of each mesh indicates whether FLVER bone data should be written to the
        EditBone (`is_bind_pose=True`) or PoseBone (`is_bind_pose=False`). Of course, we have to decide for each BONE,
        not each mesh, so currently I am enforcing that `is_bind_pose=False` for ALL meshes in order to write the bone
        transforms to PoseBone rather than EditBone. A warning will be logged if only some of them are `False`.

        The AABB of each bone is presumably generated to include all vertices that use that bone as a weight.
        """

        write_bone_type = ""
        warn_partial_bind_pose = False
        for mesh in self.flver.submeshes:
            if mesh.is_bind_pose:  # characters, objects, parts
                if not write_bone_type:
                    write_bone_type = "EDIT"  # write bone transforms to EditBones
                elif write_bone_type == "POSE":
                    warn_partial_bind_pose = True
                    write_bone_type = "EDIT"
                    break
            else:  # map pieces
                if not write_bone_type:
                    write_bone_type = "POSE"  # write bone transforms to PoseBones
                elif write_bone_type == "EDIT":
                    warn_partial_bind_pose = True
                    break  # keep EDIT default

        if not write_bone_type:
            # TODO: FLVER has no submeshes?
            self.warning(f"FLVER {self.name} has no submeshes. Bones written to EditBones.")
            write_bone_type = "EDIT"

        if warn_partial_bind_pose:
            self.warning(
                f"Some meshes in FLVER {self.name} use `is_bind_pose` (bone data written to EditBones) and some do not "
                f"(bone data written to PoseBones). Writing all bone data to EditBones."
            )

        # TODO: Theoretically, we could handled mixed bind pose/non-bind pose meshes IF AND ONLY IF they did not use the
        #  same bones. The bind pose bones could have their data written to EditBones, and the non-bind pose bones could
        #  have their data written to PoseBones. The 'is_bind_pose' custom property of each mesh can likewise be used on
        #  export, once it's confirmed that the same bone does not appear in both types of mesh.

        self.context.view_layer.objects.active = bl_armature_obj
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="EDIT", toggle=False)

        # noinspection PyTypeChecker
        armature_data = bl_armature_obj.data  # type: bpy.types.Armature
        # Create all edit bones. Head/tail are not set yet (depends on `write_bone_type` below).
        edit_bones = self.create_edit_bones(armature_data)

        # NOTE: Bones that have no vertices weighted to them are left as 'unused' root bones in the FLVER skeleton.
        # They may be animated by HKX animations (and will affect their children appropriately) but will not actually
        # affect any vertices in the mesh.

        if write_bone_type == "EDIT":
            self.write_data_to_edit_bones(edit_bones, base_edit_bone_length)
            del edit_bones  # clear references to edit bones as we exit EDIT mode
            if bpy.ops.object.mode_set.poll():
                bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        elif write_bone_type == "POSE":
            # This method will change back to OBJECT mode internally before setting pose bone data.
            self.write_data_to_pose_bones(bl_armature_obj, edit_bones)
        else:
            # Should not be possible to reach.
            raise ValueError(f"Invalid `write_bone_type`: {write_bone_type}")

    def create_edit_bones(self, bl_armature_data: bpy.types.Armature) -> list[bpy.types.EditBone]:
        """Create all edit bones from FLVER bones in `bl_armature`."""
        edit_bones = []  # all bones
        for game_bone, bl_bone_name in zip(self.flver.bones, self.bl_bone_names, strict=True):
            edit_bone = bl_armature_data.edit_bones.new(bl_bone_name)  # '<DUPE>' suffixes already added to names
            edit_bone: bpy.types.EditBone

            edit_bone["Unk x3c"] = game_bone.unk_x3c  # TODO: seems to be 1 for root bones?

            # If this is `False`, then a bone's rest pose rotation will NOT affect its relative pose basis translation.
            # That is, pose basis translation will be interpreted as being in parent space (or object for root bones)
            # rather than in the 'rest pose space' of this bone. We don't want such behavior, particularly for FLVER
            # root bones like 'Pelvis'.
            edit_bone.use_local_location = True

            # FLVER bones never inherit scale.
            edit_bone.inherit_scale = "NONE"

            if game_bone.child_index != -1:
                edit_bone["Child Name"] = self.bl_bone_names[game_bone.child_index]
            if game_bone.next_sibling_index != -1:
                edit_bone["Next Sibling Name"] = self.bl_bone_names[game_bone.next_sibling_index]
            if game_bone.previous_sibling_index != -1:
                edit_bone["Previous Sibling Name"] = self.bl_bone_names[game_bone.previous_sibling_index]
            edit_bones.append(edit_bone)
        return edit_bones

    def write_data_to_edit_bones(self, edit_bones: list[bpy.types.EditBone], base_edit_bone_length: float):

        game_arma_transforms = self.flver.get_bone_armature_space_transforms()

        for game_bone, edit_bone, game_arma_transform in zip(
            self.flver.bones, edit_bones, game_arma_transforms, strict=True
        ):
            game_translate, game_rotmat, game_scale = game_arma_transform

            if not is_uniform(game_scale, rel_tol=0.001):
                self.warning(f"Bone {game_bone.name} has non-uniform scale: {game_scale}. Left as identity.")
                bone_length = base_edit_bone_length
            elif any(c < 0.0 for c in game_scale):
                self.warning(f"Bone {game_bone.name} has negative scale: {game_scale}. Left as identity.")
                bone_length = base_edit_bone_length
            elif math.isclose(game_scale.x, 1.0, rel_tol=0.001):
                # Bone scale is ALMOST uniform and 1. Correct it.
                bone_length = base_edit_bone_length
            else:
                # Bone scale is uniform and not close to 1, which we can support (though it should be rare/never).
                bone_length = game_scale.x * base_edit_bone_length

            bl_translate = GAME_TO_BL_VECTOR(game_translate)
            # We need to set an initial head/tail position with non-zero length for the `matrix` setter to act upon.
            edit_bone.head = bl_translate
            edit_bone.tail = bl_translate + Vector((0.0, bone_length, 0.0))  # default tail position, rotated below

            bl_rot_mat3 = GAME_TO_BL_MAT3(game_rotmat)
            bl_lrs_mat = bl_rot_mat3.to_4x4()
            bl_lrs_mat.translation = bl_translate
            edit_bone.matrix = bl_lrs_mat
            edit_bone.length = bone_length  # does not interact with `matrix`

            if game_bone.parent_index != -1:
                parent_edit_bone = edit_bones[game_bone.parent_index]
                edit_bone.parent = parent_edit_bone
                # edit_bone.use_connect = True

    def write_data_to_pose_bones(self, bl_armature_obj: bpy.types.Object, edit_bones: list[bpy.types.EditBone]):

        for game_bone, edit_bone in zip(self.flver.bones, edit_bones, strict=True):
            # All edit bones are just Blender-Y-direction ("forward") stubs of base length.
            # This rigging makes map piece 'pose' bone data transform as expected for showing accurate vertex positions.
            edit_bone.head = Vector((0, 0, 0))
            edit_bone.tail = Vector((0, self.settings.base_edit_bone_length, 0))

        del edit_bones  # clear references to edit bones as we exit EDIT mode
        self.operator.to_object_mode()

        pose_bones = bl_armature_obj.pose.bones
        for game_bone, pose_bone in zip(self.flver.bones, pose_bones):
            # TODO: Pose bone transforms are relative to parent (in both FLVER and Blender).
            #  Confirm map pieces still behave as expected, though (they shouldn't even have child bones).
            pose_bone.rotation_mode = "QUATERNION"  # should already be default, but being explicit
            game_translate, game_bone_rotate = game_bone.translate, game_bone.rotate
            pose_bone.location = GAME_TO_BL_VECTOR(game_translate)
            pose_bone.rotation_quaternion = GAME_TO_BL_EULER(game_bone_rotate).to_quaternion()
            pose_bone.scale = GAME_TO_BL_VECTOR(game_bone.scale)

    def create_dummy(
        self, game_dummy: Dummy, index: int, bl_armature: bpy.types.ArmatureObject, dummy_prefix=""
    ) -> bpy.types.Object:
        """Create an empty object that represents a FLVER 'dummy' (a generic 3D point).

        The reference ID of the dummy (the value used to refer to it in other game files/code) is included in the name,
        so that it can be easily modified. The format of the dummy name should therefore not be changed. (Note that the
        order of dummies does not matter, and multiple dummies can have the same reference ID.)

        All dummies are children of the armature, and most are children of a specific bone given in 'attach_bone_name'.
        As much as I'd like to nest them under another empty object, to properly attach them to the armature, they have
        to be direct children.
        """
        if dummy_prefix:
            name = f"[{dummy_prefix}] {self.name} Dummy<{index}> [{game_dummy.reference_id}]"
        else:
            name = f"{self.name} Dummy<{index}> [{game_dummy.reference_id}]"
        bl_dummy = self.create_obj(name)  # no data (Empty)
        bl_dummy.parent = bl_armature
        bl_dummy.empty_display_type = "ARROWS"  # best display type/size I've found (single arrow not sufficient)
        bl_dummy.empty_display_size = 0.05

        if game_dummy.use_upward_vector:
            bl_rotation_euler = game_forward_up_vectors_to_bl_euler(game_dummy.forward, game_dummy.upward)
        else:  # TODO: I assume this is right (up-ignoring dummies only rotate around vertical axis)
            bl_rotation_euler = game_forward_up_vectors_to_bl_euler(game_dummy.forward, Vector3((0, 1, 0)))

        if game_dummy.parent_bone_index != -1:
            # Bone's FLVER translate is in the space of (i.e. relative to) this parent bone.
            # NOTE: This is NOT the same as the 'attach' bone, which is used as the actual Blender parent and
            # controls how the dummy moves during armature animations.
            bl_bone_name = self.bl_bone_names[game_dummy.parent_bone_index]
            bl_dummy["Parent Bone Name"] = bl_bone_name
            bl_parent_bone_matrix = bl_armature.data.bones[bl_bone_name].matrix_local
            bl_location = bl_parent_bone_matrix @ GAME_TO_BL_VECTOR(game_dummy.translate)
        else:
            # Bone's location is in armature space.
            bl_dummy["Parent Bone Name"] = ""
            bl_location = GAME_TO_BL_VECTOR(game_dummy.translate)

        # Dummy moves with this bone during animations.
        if game_dummy.attach_bone_index != -1:
            bl_dummy.parent_bone = self.bl_bone_names[game_dummy.attach_bone_index]
            bl_dummy.parent_type = "BONE"

        # We need to set the dummy's world matrix, rather than its local matrix, to bypass its possible bone
        # attachment above.
        bl_dummy.matrix_world = Matrix.LocRotScale(bl_location, bl_rotation_euler, Vector((1.0, 1.0, 1.0)))

        # NOTE: Reference ID not included as a property.
        # bl_dummy["reference_id"] = dummy.reference_id  # int
        bl_dummy["Color RGBA"] = game_dummy.color_rgba  # RGBA  # TODO: Use in actual display somehow?
        bl_dummy["Flag 1"] = game_dummy.flag_1  # bool
        bl_dummy["Use Upward Vector"] = game_dummy.use_upward_vector  # bool
        # NOTE: These two properties are only ever non-zero in Sekiro (and probably Elden Ring).
        bl_dummy["Unk x30"] = game_dummy.unk_x30  # int
        bl_dummy["Unk x34"] = game_dummy.unk_x34  # int

        return bl_dummy

    def create_obj(self, name: str, data=None):
        """Create a new Blender object with given `data` and link it to the scene's object collection."""
        obj = bpy.data.objects.new(name, data)
        self.context.scene.collection.objects.link(obj)
        self.new_objs.append(obj)
        return obj

    def warning(self, warning: str):
        self.operator.report({"WARNING"}, warning)

    @property
    def flver_root(self):
        """Always the first object created."""
        return self.new_objs[0]
