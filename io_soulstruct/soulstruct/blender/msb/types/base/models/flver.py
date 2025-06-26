from __future__ import annotations

__all__ = [
    "BaseBlenderMSBFLVERModelImporter",
    "BlenderMSBMapPieceModelImporter",
    "BlenderMSBObjectModelImporter",
    "BlenderMSBCharacterModelImporter",
]

import abc
import time
import traceback
import typing as tp
from dataclasses import dataclass
from pathlib import Path

import bpy

from soulstruct.containers import Binder, BinderEntry
from soulstruct.flver import FLVER, MergedMesh

from soulstruct.blender.exceptions import FLVERImportError
from soulstruct.blender.flver.image.image_import_manager import ImageImportManager
from soulstruct.blender.flver.models.types import BlenderFLVER
from soulstruct.blender.flver.utilities import get_flvers_from_binder
from soulstruct.blender.types import ObjectType, SoulstructType
from soulstruct.blender.utilities import find_or_create_collection, LoggingOperator, get_model_name, find_obj

from .base import BaseBlenderMSBModelImporter, MODEL_T


@dataclass(slots=True)
class BaseBlenderMSBFLVERModelImporter(BaseBlenderMSBModelImporter, abc.ABC):
    """Still abstract; overridden by specific Model types (Map Pieces, Characters, Objects, etc.)."""

    MODEL_SUBTYPE_TITLE: tp.ClassVar[str]
    USE_MAP_COLLECTION: tp.ClassVar[bool] = False

    model_name_dict: dict[int, str] = None  # for adding character descriptions to model names

    def _import_flver_model_mesh(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        flver: FLVER,
        model_name: str,
        model_collection: bpy.types.Collection,
        image_import_manager: ImageImportManager = None,
    ) -> bpy.types.MeshObject:
        try:
            bl_flver = BlenderFLVER.new_from_soulstruct_obj(
                operator,
                context,
                flver,
                name=model_name,
                image_import_manager=image_import_manager,
                collection=model_collection,
            )  # returns Blender object
        except Exception as ex:
            traceback.print_exc()  # for inspection in Blender console
            raise FLVERImportError(f"Cannot import {self.MODEL_SUBTYPE_TITLE} FLVER: {model_name}. Error: {ex}")

        self.post_process_flver(context, bl_flver)
        return bl_flver.mesh

    @classmethod
    def _batch_import_flver_models(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        flver_sources: dict[str, BinderEntry | Path],
        map_stem: str,
        flver_source_binders: dict[str, Binder] = None,
        image_import_callback: tp.Callable[[ImageImportManager, FLVER, BinderEntry | Path, Binder | None], None] = None,
    ):
        """Base method for batch-importing FLVER models, which have already been parsed into `flver_sources` and
        (if in Binders) `flver_source_binders`.

        A single `ImageImportManager` is created to handle the batch (if enabled in import settings). If
        `image_import_callback` is given, it will be called on each `FLVER` with its corresponding source entry/path and
        (if given) its source `Binder` instance. This is in addition (and after) to the standard texture import method
        `ImageImportManager.find_flver_textures()`. This callback will usually load 'lazy' map textures used by a FLVER.
        """
        flver_import_settings = context.scene.flver_import_settings
        flver_source_binders = flver_source_binders or {}

        operator.info(f"Importing {len(flver_sources)} {cls.MODEL_SUBTYPE_TITLE} FLVERs in parallel.")

        p = time.perf_counter()

        if all(isinstance(data, Path) for data in flver_sources.values()):
            flvers_list = FLVER.from_path_batch(list(flver_sources.values()))
        elif all(isinstance(data, BinderEntry) for data in flver_sources.values()):
            flvers_list = FLVER.from_binder_entry_batch(list(flver_sources.values()))
        else:
            raise ValueError(
                "FLVER model data for batch importing must be ALL either `BinderEntry` or `Path` objects (not a mix)."
            )
        # Drop failed FLVERs immediately.
        flvers = {
            model_name: flver
            for model_name, flver in zip(flver_sources.keys(), flvers_list)
            if flver is not None
        }

        operator.info(
            f"Imported {len(flvers)} {cls.MODEL_SUBTYPE_TITLE} FLVERs in {time.perf_counter() - p:.2f} seconds."
        )
        p = time.perf_counter()

        if flver_import_settings.import_textures:
            # Create a shared `ImageImportManager` used for complete batch.
            image_import_manager = ImageImportManager(operator, context)
            # Find textures for all loaded FLVERs.
            for model_name, flver in flvers.items():
                source_binder = flver_source_binders.get(model_name, None)
                image_import_manager.find_flver_textures(
                    source_binder.path if source_binder else flver.path,
                    source_binder,
                )
                if image_import_callback:
                    image_import_callback(
                        image_import_manager,
                        flver,
                        flver_sources[model_name],
                        flver_source_binders.get(model_name, None),
                    )
        else:
            image_import_manager = None

        # Brief non-parallel excursion: create Blender materials and `MergedMesh` arguments for each `FLVER`.
        flver_bl_materials = {}
        flver_names_to_merge = []
        flvers_to_merge = []
        flver_merged_mesh_args = []
        bl_materials_by_matdef_name = {}  # can re-use cache across all FLVERs!
        merge_mesh_vertices = flver_import_settings.merge_mesh_vertices
        for model_name, flver in tuple(flvers.items()):
            if not flver.meshes:
                # FLVER has no meshes. No materials or merging.
                continue

            try:
                bl_materials, mesh_bl_material_indices, bl_material_uv_layer_names = BlenderFLVER.create_materials(
                    operator,
                    context,
                    flver,
                    model_name,
                    material_blend_mode=flver_import_settings.material_blend_mode,
                    image_import_manager=image_import_manager,
                    bl_materials_by_matdef_name=bl_materials_by_matdef_name,
                )
            except Exception as ex:
                operator.error(f"(Batch) Cannot import FLVER: {flver.path_name}. Material creation error: {ex}")
                flvers.pop(model_name)  # drop failed FLVER
                continue
            flver_bl_materials[model_name] = bl_materials

            flver_names_to_merge.append(model_name)
            flvers_to_merge.append(flver)
            flver_merged_mesh_args.append(
                (mesh_bl_material_indices, bl_material_uv_layer_names, merge_mesh_vertices)
            )

        operator.info(
            f"Created materials for {len(flvers)} {cls.MODEL_SUBTYPE_TITLE} FLVERs in {time.perf_counter() - p:.2f} "
            f"seconds."
        )
        p = time.perf_counter()

        # Merge meshes in parallel. Empty meshes will be `None`.
        flver_merged_meshes_list = MergedMesh.from_flver_batch(flvers_to_merge, flver_merged_mesh_args)
        flver_merged_meshes = {  # nothing dropped
            model_name: merged_mesh
            for model_name, merged_mesh in zip(flver_names_to_merge, flver_merged_meshes_list)
        }

        operator.info(
            f"Merged {len(flvers)} {cls.MODEL_SUBTYPE_TITLE} FLVERs in {time.perf_counter() - p:.2f} seconds."
        )
        p = time.perf_counter()

        if cls.USE_MAP_COLLECTION:
            model_collection = find_or_create_collection(
                context.scene.collection,
                "Models",
                f"{map_stem} Models",
                f"{map_stem} {cls.MODEL_SUBTYPE_TITLE} Models",
            )
        else:
            # Not map-specific.
            model_collection = find_or_create_collection(
                context.scene.collection,
                "Models",
                "Game Models",
                f"{cls.MODEL_SUBTYPE_TITLE} Models",
            )

        for model_name, flver in flvers.items():

            if flver.meshes:
                # Check for errors in merging and/or material creation.
                if flver_merged_meshes[model_name] is None and flver_bl_materials[model_name] is not None:
                    operator.error(f"Cannot import FLVER '{model_name}' ({flver.path_name}) due to `MergedMesh` error.")
                    continue
                if flver_bl_materials[model_name] is None and flver_merged_meshes[model_name] is not None:
                    operator.error(f"Cannot import FLVER: '{model_name}' ({flver.path_name}) due to material error.")
                    continue
                merged_mesh = flver_merged_meshes[model_name]
                bl_materials = flver_bl_materials[model_name]
            else:
                merged_mesh = None
                bl_materials = None

            try:
                BlenderFLVER.new_from_soulstruct_obj(
                    operator,
                    context,
                    flver,
                    name=model_name,
                    image_import_manager=image_import_manager,
                    collection=model_collection,
                    existing_merged_mesh=merged_mesh,
                    existing_bl_materials=bl_materials,
                )
            except Exception as ex:
                traceback.print_exc()  # for inspection in Blender console
                operator.error(f"Cannot import FLVER: {flver.path_name}. Error: {ex}")

        operator.info(
            f"Imported {len(flvers)} {cls.MODEL_SUBTYPE_TITLE} FLVERs in {time.perf_counter() - p:.2f} seconds."
        )

    def post_process_flver(self, context: bpy.types.Context, bl_flver: BlenderFLVER):
        """Add model description to Blender name."""
        if self.model_name_dict and context.scene.flver_import_settings.add_name_suffix:
            try:
                model_id = int(bl_flver.name[1:5])
                model_desc = self.model_name_dict[model_id]
                # Don't trigger full rename.
                bl_flver.obj.name += f" <{model_desc}>"
                bl_flver.armature.name += f" <{model_desc}>"
            except (ValueError, KeyError):
                pass

    @staticmethod
    def does_model_exist(model_name: str) -> bool:
        """Check if FLVER model already exists in Blender."""
        return find_obj(model_name, ObjectType.MESH, SoulstructType.FLVER, bl_name_func=get_model_name) is not None


@dataclass(slots=True)
class BlenderMSBMapPieceModelImporter(BaseBlenderMSBFLVERModelImporter):

    MODEL_SUBTYPE_TITLE = "Map Piece"
    USE_MAP_COLLECTION = True

    def import_model_mesh(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        model_name: str,
        map_stem: str,  # required for Map Pieces
        model_collection: bpy.types.Collection = None,
    ) -> bpy.types.MeshObject:
        """Import the model of the given name into a collection in the current scene.

        TODO: Will need to check MAPBNDs for Elden Ring MSBs.
        """
        settings = operator.settings(context)
        flver_import_settings = context.scene.flver_import_settings
        try:
            flver_path = settings.get_import_map_file_path(f"{model_name}.flver", map_stem=map_stem)
        except FileNotFoundError:
            raise FLVERImportError(f"Cannot find FLVER model file for Map Piece: {model_name}.")

        operator.info(f"Importing map piece FLVER: {flver_path}")

        flver = FLVER.from_path(flver_path)

        if flver_import_settings.import_textures:
            image_import_manager = ImageImportManager(operator, context)
            image_import_manager.find_flver_textures(flver_path)
            self._register_lazy_map_textures(image_import_manager, flver, flver_path, None)
        else:
            image_import_manager = None

        if not model_collection:
            model_collection = find_or_create_collection(
                context.scene.collection,
                "Models",
                f"{map_stem} Models",
                f"{map_stem} Map Piece Models",
            )

        return self._import_flver_model_mesh(
            operator, context, flver, model_name, model_collection, image_import_manager
        )

    def batch_import_model_meshes(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        models: list[MODEL_T],
        map_stem: str,
    ):
        """Import all models for a batch of MSB Map Pieces, as needed, in parallel as much as possible.

        TODO: Will need to check MAPBNDs for Elden Ring MSBs.
        """
        settings = operator.settings(context)

        model_datas = {}  # type: dict[str, Path]
        for model in models:
            model_name = model.get_model_file_stem(map_stem)
            if model_name in model_datas:
                continue  # already queued for import
            if self.does_model_exist(model_name):
                continue
            # Queue up path for batch import.
            try:
                model_path = settings.get_import_map_file_path(f"{model_name}.flver", map_stem=map_stem)
            except FileNotFoundError:
                pass  # handled later with placeholder model
            else:
                model_datas[model_name] = model_path

        if not model_datas:
            operator.info("No Map Piece FLVER models to import.")
            return  # nothing to import

        self._batch_import_flver_models(
            operator,
            context,
            model_datas,
            map_stem,
            flver_source_binders=None,
            image_import_callback=self._register_lazy_map_textures,
        )

    @staticmethod
    def _register_lazy_map_textures(
        image_import_manager: ImageImportManager,
        flver: FLVER,
        flver_source: Path,
        _: None,  # no source Binder  # TODO: there will be for MAPBND
    ) -> None:
        map_dir = flver_source.parent.parent  # assume Map Piece FLVER is in 'map/{map_stem}' subdirectory
        image_import_manager.register_lazy_flver_map_textures(map_dir, flver)


@dataclass(slots=True)
class BlenderMSBObjectModelImporter(BaseBlenderMSBFLVERModelImporter):

    MODEL_SUBTYPE_TITLE = "Object"
    USE_MAP_COLLECTION = False
    # NOTE: OBJBND binders are never nested under subfolders hnin any game.

    def import_model_mesh(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        model_name: str,
        map_stem="",  # not used
        model_collection: bpy.types.Collection = None,
    ) -> bpy.types.MeshObject:
        """Import the model of the given name into a collection in the current scene."""
        settings = operator.settings(context)

        flver_import_settings = context.scene.flver_import_settings

        # No game-specific logic needed to find OBJBND path (always the same).
        objbnd_path = settings.get_import_file_path(f"obj/{model_name}.objbnd")

        operator.info(f"Importing object FLVER from OBJBND: {objbnd_path.name}")

        objbnd = Binder.from_path(objbnd_path)
        binder_flvers = get_flvers_from_binder(objbnd, objbnd_path, allow_multiple=True)
        flver = binder_flvers[0]  # TODO: ignoring secondary Object FLVERs for now

        if flver_import_settings.import_textures:
            image_import_manager = ImageImportManager(operator, context)
            image_import_manager.find_flver_textures(objbnd_path, flver_binder=objbnd)
            self._register_lazy_map_textures(image_import_manager, flver, None, objbnd)
            map_dir = objbnd_path.parent.parent / "map"  # assume OBJBND is in 'obj' subdirectory next to 'map'
            image_import_manager.register_lazy_flver_map_textures(map_dir, flver)
        else:
            image_import_manager = None

        if not model_collection:
            model_collection = find_or_create_collection(context.scene.collection, "Models", "Object Models")

        return self._import_flver_model_mesh(
            operator, context, flver, model_name, model_collection, image_import_manager
        )

    def batch_import_model_meshes(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        models: list[MODEL_T],
        map_stem: str,
    ):
        """Import all models for a batch of MSB Parts, as needed, in parallel as much as possible."""
        settings = operator.settings(context)

        model_datas = {}
        model_objbnds = {}
        for model in models:
            model_name = model.get_model_file_stem(map_stem)
            if model_name in model_datas:
                continue  # already queued for import
            if self.does_model_exist(model_name):
                continue

            # Queue up path for batch import.
            objbnd_path = settings.get_import_file_path(f"obj/{model_name}.objbnd")
            objbnd = Binder.from_path(objbnd_path)
            flver_entries = objbnd.find_entries_matching_name(r".*\.flver(\.dcx)?")
            if not flver_entries:
                raise FLVERImportError(f"Cannot find a FLVER file in OBJBND {objbnd_path}.")
            # TODO: Ignoring secondary object FLVERs for now.
            model_datas[model_name] = flver_entries[0]
            model_objbnds[model_name] = objbnd

        if not model_datas:
            operator.info("No Object FLVER models to import.")
            return  # nothing to import

        self._batch_import_flver_models(
            operator,
            context,
            model_datas,
            map_stem,
            flver_source_binders=model_objbnds,
            image_import_callback=self._register_lazy_map_textures,
        )

    @staticmethod
    def _register_lazy_map_textures(
        image_import_manager: ImageImportManager,
        flver: FLVER,
        _: BinderEntry | None,  # Entry not needed
        source_objbnd: Binder,
    ) -> None:
        map_dir = source_objbnd.path.parent / "../map"  # assume OBJBND is in 'obj' subdirectory
        image_import_manager.register_lazy_flver_map_textures(map_dir, flver)


@dataclass(slots=True)
class BlenderMSBCharacterModelImporter(BaseBlenderMSBFLVERModelImporter):
    """Find and import a Character FLVER model from a CHRBND (or loose FLVER in Demon's Souls).

    Used for `MSBPlayerModel` entries as well (sometimes used for 'c0000').
    """

    MODEL_SUBTYPE_TITLE = "Character"
    USE_MAP_COLLECTION = False
    uses_nested_subfolders: bool = False  # CHRBNDs found in 'chr/cXXXX' folder rather than just 'chr'
    prefer_loose_flvers: bool = False  # prefer FLVERs in loose files over CHRBNDs (Demon's Souls only)

    def import_model_mesh(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        model_name: str,
        map_stem="",  # not used
        model_collection: bpy.types.Collection = None,
    ) -> bpy.types.MeshObject:
        """Import the model of the given name into a collection in the current scene."""
        settings = operator.settings(context)

        if not model_collection:
            model_collection = find_or_create_collection(context.scene.collection, "Models", "Character Models")

        import_settings = context.scene.flver_import_settings
        image_import_manager = ImageImportManager(operator, context) if import_settings.import_textures else None

        if self.uses_nested_subfolders:
            relative_chrbnd_path = Path(f"chr/{model_name}/{model_name}.chrbnd")
        else:
            relative_chrbnd_path = Path(f"chr/{model_name}.chrbnd")
        chrbnd_path = settings.get_import_file_path(relative_chrbnd_path)
        operator.info(f"Importing character FLVER from CHRBND: {chrbnd_path.name}")
        chrbnd = Binder.from_path(chrbnd_path)
        binder_flvers = get_flvers_from_binder(chrbnd, chrbnd_path, allow_multiple=False)
        if image_import_manager:
            image_import_manager.find_flver_textures(chrbnd_path, chrbnd)

        flver = binder_flvers[0]

        return self._import_flver_model_mesh(
            operator, context, flver, model_name, model_collection, image_import_manager
        )

    def batch_import_model_meshes(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        models: list[MODEL_T],
        map_stem: str,
    ):
        """Import all models for a batch of MSB Parts, as needed, in parallel as much as possible."""
        settings = operator.settings(context)
        model_datas = {}
        model_chrbnds = {}
        for model in models:
            model_name = model.get_model_file_stem(map_stem)
            if model_name in model_datas:
                continue  # already queued for import
            if self.does_model_exist(model_name):
                continue  # model already imported (Part will find it)

            if self.uses_nested_subfolders:
                relative_chrbnd_path = Path(f"chr/{model_name}/{model_name}.chrbnd")
            else:
                relative_chrbnd_path = Path(f"chr/{model_name}.chrbnd")

            if self.prefer_loose_flvers:
                flver_path = settings.get_import_file_path(relative_chrbnd_path.with_suffix(".flver"))
                if flver_path.exists():
                    model_datas[model_name] = flver_path
                    # No CHRBND stored.
                    continue

            chrbnd_path = settings.get_import_file_path(relative_chrbnd_path)
            chrbnd = Binder.from_path(chrbnd_path)
            flver_entries = chrbnd.find_entries_matching_name(r".*\.flver(\.dcx)?")
            if not flver_entries:
                raise FLVERImportError(f"Cannot find a FLVER file in CHRBND {chrbnd_path}.")
            model_datas[model_name] = flver_entries[0]
            model_chrbnds[model_name] = chrbnd

        if not model_datas:
            operator.info("No Character FLVER models to import.")
            return  # nothing to import

        self._batch_import_flver_models(
            operator,
            context,
            model_datas,
            map_stem,
            flver_source_binders=model_chrbnds,
        )
