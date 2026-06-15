from __future__ import annotations

__all__ = [
    "BaseBlenderMSBFLVERModelImporter",
    "BlenderMSBMapPieceModelImporter",
    "BlenderMSBObjectModelImporter",
    "BlenderMSBCharacterModelImporter",
]

import abc
import traceback
import typing as tp
from dataclasses import dataclass
from pathlib import Path

import bpy

from soulstruct.base.maps.msb.models import BaseMSBModel
from soulstruct.flver import *

import pyrelink.core as pyre
from pyrelink.flver import FLVER as PyreFLVER, TextureFinder

from .....base.operators import *
from .....exceptions import FLVERImportError
from .....flver.models.types import BlenderFLVER
from .....flver.utilities import get_flvers_from_binder
from .....types import *
from .....utilities import find_or_create_collection, get_model_name, find_obj

from .base import BaseBlenderMSBModelImporter


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
        texture_finder: TextureFinder | None = None,
    ) -> MeshObject:
        try:
            bl_flver = BlenderFLVER.new_from_soulstruct_obj(
                operator,
                context,
                flver,
                name=model_name,
                texture_finder=texture_finder,
                collection=model_collection,
            )
        except Exception as ex:
            traceback.print_exc()  # for inspection in Blender console
            raise FLVERImportError(f"Cannot import {self.MODEL_SUBTYPE_TITLE} FLVER: {model_name}. Error: {ex}")

        self.post_process_bl_flver(context, bl_flver)
        return bl_flver.mesh

    @classmethod
    def _batch_import_flver_models(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        map_stem: str,
        flver_path_sources: dict[str, Path] | None = None,
        flver_binder_sources: dict[str, tuple[pyre.BinderEntry, pyre.Binder]] | None = None,
    ) -> None:
        """Base method for batch-importing FLVER models for an MSB Part subtype.

        Calls the `BlenderFLVER` batch importer, placing them in the appropriate model Collection.
        """

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

        # Returned BlenderFLVER dictionary is not needed. All logging is done internally.
        BlenderFLVER.new_batch_from_soulstruct_objs(
            operator,
            context,
            flver_path_sources=flver_path_sources,
            flver_binder_sources=flver_binder_sources,
            flver_model_category=cls.MODEL_SUBTYPE_TITLE,
            texture_finder_callback=None,
            collection=model_collection,
        )

    def post_process_bl_flver(self, context: bpy.types.Context, bl_flver: BlenderFLVER):
        """Add model description to Blender name."""
        if self.model_name_dict and context.scene.flver_import_settings.add_name_suffix:
            try:
                model_id = int(bl_flver.name[1:5])
                model_desc = self.model_name_dict[model_id]
                # Don't trigger full rename.
                bl_flver.obj.name += f" <{model_desc}>"
                if bl_flver.armature:
                    bl_flver.armature.name += f" <{model_desc}>"
            except (ValueError, KeyError):
                pass

    @staticmethod
    def is_model_in_blender(model_name: str) -> bool:
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
        model_collection: bpy.types.Collection | None = None,
    ) -> MeshObject:
        """Import the model of the given name into a collection in the current scene."""
        settings = operator.settings(context)
        flver_import_settings = context.scene.flver_import_settings

        if settings.is_game("ELDEN_RING"):
            # Map Piece FLVERs are in MAPBND Binders.
            mapbnd_name = f"map/{map_stem[:3]}/{map_stem}/{map_stem}_{model_name[1:]}.mapbnd.dcx"
            try:
                flver_source_path = settings.get_import_file_path(mapbnd_name)
            except FileNotFoundError:
                raise FLVERImportError(f"Cannot find MAPBND model binder file for Map Piece: {model_name}.")
            operator.info(f"Importing map piece FLVER from MAPBND: {flver_source_path}")

            mapbnd = pyre.Binder.from_path(flver_source_path)
            flver_entries = mapbnd.find_entries_by_name_regex(r".*\.flver(\.dcx)?")
            if not flver_entries:
                raise FLVERImportError(f"Cannot find a FLVER file in MAPBND {flver_source_path}.")
            flver_entry = flver_entries[0]

            if settings.use_pyrelink_flver:
                flver = PyreFLVER.from_bytes(flver_entry.get_uncompressed_data())
            else:
                flver = FLVER.from_bytes(flver_entry.get_uncompressed_data())
        else:
            # Loose FLVER files in older games.
            mapbnd = None
            try:
                flver_source_path = settings.get_import_map_file_path(f"{model_name}.flver", map_stem=map_stem)
            except FileNotFoundError:
                raise FLVERImportError(f"Cannot find FLVER model file for Map Piece: {model_name}.")
            operator.info(f"Importing map piece FLVER: {flver_source_path}")
            if settings.use_pyrelink_flver:
                flver = PyreFLVER.from_path(flver_source_path)
            else:
                flver = FLVER.from_path(flver_source_path)

        if flver_import_settings.import_textures:
            texture_finder = TextureFinder(
                settings.pyrelink_game_type,
                settings.get_first_existing_import_root() or "",
            )
            texture_finder.register_flver_sources(flver_source_path, mapbnd, prefer_hi_res=True)
        else:
            texture_finder = None

        if not model_collection:
            model_collection = find_or_create_collection(
                context.scene.collection,
                "Models",
                f"{map_stem} Models",
                f"{map_stem} Map Piece Models",
            )

        return self._import_flver_model_mesh(
            operator,
            context,
            flver,
            model_name,
            model_collection,
            texture_finder=texture_finder,
        )

    def batch_import_model_meshes(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        models: list[BaseMSBModel],
        map_stem: str,
    ):
        """Import all models for a batch of MSB Map Pieces, as needed, in parallel as much as possible."""
        settings = operator.settings(context)

        flver_path_sources = {}  # type: dict[str, Path]
        flver_binder_sources = {}  # type: dict[str, tuple[pyre.BinderEntry, pyre.Binder]]
        
        if settings.is_game("ELDEN_RING"):
            # Map Piece FLVERS are inside MAPBND Binders.
        
            for model in models:
                model_name = model.get_model_file_stem(map_stem)
                if model_name in flver_binder_sources:
                    continue  # already queued for import
                if self.is_model_in_blender(model_name):
                    continue
                # Queue up path for batch import.
                try:
                    mapbnd_path = settings.get_import_file_path(
                        f"map/{map_stem[:3]}/{map_stem}/{map_stem}_{model_name[1:]}.mapbnd.dcx"
                    )
                    mapbnd = pyre.Binder.from_path(mapbnd_path)
                    flver_entry = mapbnd.find_entry_by_id(200)
                    if flver_entry is None:
                        raise FileNotFoundError
                except FileNotFoundError:
                    pass  # handled later with placeholder model
                else:
                    flver_binder_sources[model_name] = (flver_entry, mapbnd)

            if not flver_binder_sources:
                operator.info("No Map Piece FLVER models (from MAPBNDs) to import.")
                return
            
        else:
        
            for model in models:
                model_name = model.get_model_file_stem(map_stem)
                if model_name in flver_path_sources:
                    continue  # already queued for import
                if self.is_model_in_blender(model_name):
                    continue
                # Queue up path for batch import.
                try:
                    model_path = settings.get_import_map_file_path(f"{model_name}.flver", map_stem=map_stem)
                except FileNotFoundError:
                    pass  # handled later with placeholder model
                else:
                    flver_path_sources[model_name] = model_path

            if not flver_path_sources:
                operator.info("No Map Piece FLVER models to import.")
                return

        self._batch_import_flver_models(
            operator,
            context,
            map_stem,
            flver_path_sources=flver_path_sources,
            flver_binder_sources=flver_binder_sources,
        )


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
        model_collection: bpy.types.Collection | None = None,
    ) -> MeshObject:
        """Import the model of the given name into a collection in the current scene."""
        settings = operator.settings(context)

        flver_import_settings = context.scene.flver_import_settings

        # No game-specific logic needed to find OBJBND path (always the same).
        objbnd_path = settings.get_import_file_path(f"obj/{model_name}.objbnd")

        operator.info(f"Importing object FLVER from OBJBND: {objbnd_path.name}")

        objbnd = pyre.Binder.from_path(objbnd_path)
        binder_flvers = get_flvers_from_binder(
            objbnd, objbnd_path, allow_multiple=True, use_pyrelink_flver=settings.use_pyrelink_flver
        )

        if flver_import_settings.import_textures:
            texture_finder = settings.create_texture_finder()
            texture_finder.register_flver_sources(objbnd_path, objbnd, prefer_hi_res=True)
        else:
            texture_finder = None

        if not model_collection:
            model_collection = find_or_create_collection(context.scene.collection, "Models", "Object Models")

        first_bl_obj = None
        for flver in binder_flvers:
            sub_model_name = flver.path_minimal_stem  # e.g. could be 'o1000_1'
            assert sub_model_name is not None  # set by Binder
            bl_obj = self._import_flver_model_mesh(
                operator, context, flver, sub_model_name, model_collection, texture_finder
            )
            if not first_bl_obj:
                first_bl_obj = bl_obj

        assert first_bl_obj is not None  # logically ensured
        return first_bl_obj

    def batch_import_model_meshes(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        models: list[BaseMSBModel],
        map_stem: str,
    ):
        """Import all models for a batch of MSB Parts, as needed, in parallel as much as possible."""
        settings = operator.settings(context)

        flver_binder_sources = {}  # type: dict[str, tuple[pyre.BinderEntry, pyre.Binder]]
        for model in models:
            model_name = model.get_model_file_stem(map_stem)
            if model_name in flver_binder_sources:
                continue  # already queued for import
            if self.is_model_in_blender(model_name):
                continue

            # Queue up path for batch import.
            objbnd_path = settings.get_import_file_path(f"obj/{model_name}.objbnd")
            objbnd = pyre.Binder.from_path(objbnd_path)
            # OBJBNDs can contain multiple FLVERs, e.g. 'o1000', 'o1000_1'.
            flver_entries = objbnd.find_entries_by_name_regex(r".*\.flver(\.dcx)?")
            if not flver_entries:
                raise FLVERImportError(f"Cannot find a FLVER file in OBJBND {objbnd_path}.")
            for entry in flver_entries:
                flver_binder_sources[entry.stem] = (entry, objbnd)

        if not flver_binder_sources:
            operator.info("No Object FLVER models to import.")
            return  # nothing to import

        self._batch_import_flver_models(
            operator,
            context,
            map_stem,
            flver_binder_sources=flver_binder_sources,
        )


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
        model_collection: bpy.types.Collection | None = None,
    ) -> MeshObject:
        """Import the model of the given name into a collection in the current scene."""
        settings = operator.settings(context)

        if not model_collection:
            model_collection = find_or_create_collection(context.scene.collection, "Models", "Character Models")

        import_settings = context.scene.flver_import_settings
        texture_finder = settings.create_texture_finder() if import_settings.import_textures else None
        # No extra global texture sources to pinpoint for Characters.

        if self.uses_nested_subfolders:
            relative_chrbnd_path = Path(f"chr/{model_name}/{model_name}.chrbnd")
        else:
            relative_chrbnd_path = Path(f"chr/{model_name}.chrbnd")
        chrbnd_path = settings.get_import_file_path(relative_chrbnd_path)
        operator.info(f"Importing character FLVER from CHRBND: {chrbnd_path.name}")
        chrbnd = pyre.Binder.from_path(chrbnd_path)
        # Only one Character FLVER permitted per CHRBND.
        binder_flvers = get_flvers_from_binder(chrbnd, chrbnd_path, allow_multiple=False)
        flver = binder_flvers[0]
        if texture_finder:
            texture_finder.register_flver_sources(chrbnd_path, chrbnd, prefer_hi_res=True)

        return self._import_flver_model_mesh(
            operator, context, flver, model_name, model_collection, texture_finder
        )

    def batch_import_model_meshes(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        models: list[BaseMSBModel],
        map_stem: str,
    ):
        """Import all models for a batch of MSB Parts, as needed, in parallel as much as possible."""
        settings = operator.settings(context)

        # If `prefer_loose_flvers = True`, sources may be Paths (Demon's Souls PS3 only).
        flver_path_sources = {}  # type: dict[str, Path]
        flver_binder_sources = {}  # type: dict[str, tuple[pyre.BinderEntry, pyre.Binder]]

        for model in models:
            model_name = model.get_model_file_stem(map_stem)
            if model_name in flver_path_sources or model_name in flver_binder_sources:
                continue  # already queued for import
            if self.is_model_in_blender(model_name):
                continue  # model already imported (Part will find it)

            if self.uses_nested_subfolders:
                relative_chrbnd_path = Path(f"chr/{model_name}/{model_name}.chrbnd")
            else:
                relative_chrbnd_path = Path(f"chr/{model_name}.chrbnd")

            if self.prefer_loose_flvers:
                flver_path = settings.get_import_file_path(relative_chrbnd_path.with_suffix(".flver"))
                if flver_path.exists():
                    flver_path_sources[model_name] = flver_path
                    # No CHRBND stored.
                    continue

            chrbnd_path = settings.get_import_file_path(relative_chrbnd_path)
            chrbnd = pyre.Binder.from_path(chrbnd_path)
            flver_entries = chrbnd.find_entries_by_name_regex(r".*\.flver(\.dcx)?")
            if not flver_entries:
                raise FLVERImportError(f"Cannot find a FLVER file in CHRBND {chrbnd_path}.")
            if len(flver_entries) > 1:
                raise FLVERImportError(f"Found multiple FLVER files in CHRBND {chrbnd_path}. Only one is expected.")
            flver_binder_sources[model_name] = (flver_entries[0], chrbnd)

        if not flver_path_sources and not flver_binder_sources:
            operator.info("No Character FLVER models to import.")
            return  # nothing to import

        self._batch_import_flver_models(
            operator,
            context,
            map_stem,
            flver_path_sources=flver_path_sources,
            flver_binder_sources=flver_binder_sources,
        )
