from __future__ import annotations

__all__ = [
    "BLENDER_MSB_PART_TYPES",
    "MSBPartOperatorConfig",
    "BaseImportSingleMSBPart",
    "BaseImportAllMSBParts",
]

import abc
import time
import traceback
import typing as tp
from dataclasses import dataclass

import bpy

from soulstruct.games import *

from io_soulstruct.general.cached import get_cached_file
from io_soulstruct.msb import darksouls1ptde, darksouls1r
from io_soulstruct.msb.properties import MSBPartSubtype
from io_soulstruct.utilities.operators import LoggingOperator
from io_soulstruct.utilities.misc import *
from ..settings import MSBImportSettings


if tp.TYPE_CHECKING:
    from io_soulstruct.type_checking import MSB_TYPING


BLENDER_MSB_PART_TYPES = {
    DARK_SOULS_PTDE: {
        MSBPartSubtype.MAP_PIECE: darksouls1ptde.BlenderMSBMapPiece,
        MSBPartSubtype.OBJECT: darksouls1ptde.BlenderMSBObject,
        MSBPartSubtype.CHARACTER: darksouls1ptde.BlenderMSBCharacter,
        MSBPartSubtype.PLAYER_START: darksouls1ptde.BlenderMSBPlayerStart,
        MSBPartSubtype.COLLISION: darksouls1ptde.BlenderMSBCollision,
        MSBPartSubtype.NAVMESH: darksouls1ptde.BlenderMSBNavmesh,
        MSBPartSubtype.CONNECT_COLLISION: darksouls1ptde.BlenderMSBConnectCollision,
    },
    DARK_SOULS_DSR: {
        MSBPartSubtype.MAP_PIECE: darksouls1r.BlenderMSBMapPiece,
        MSBPartSubtype.OBJECT: darksouls1r.BlenderMSBObject,
        MSBPartSubtype.CHARACTER: darksouls1r.BlenderMSBCharacter,
        MSBPartSubtype.PLAYER_START: darksouls1r.BlenderMSBPlayerStart,
        MSBPartSubtype.COLLISION: darksouls1r.BlenderMSBCollision,
        MSBPartSubtype.NAVMESH: darksouls1r.BlenderMSBNavmesh,
        MSBPartSubtype.CONNECT_COLLISION: darksouls1r.BlenderMSBConnectCollision,
    },
}


@dataclass(slots=True)
class MSBPartOperatorConfig:
    """Configuration for MSB Part import operators."""

    PART_SUBTYPE: MSBPartSubtype
    MSB_LIST_NAME: str
    GAME_ENUM_NAME: str | None
    USE_LATEST_MAP_FOLDER: bool = False

    def get_bl_part_type(self, game: Game) -> tp.Type[darksouls1ptde.BlenderMSBPart]:
        return BLENDER_MSB_PART_TYPES[game][self.PART_SUBTYPE]


class BaseImportSingleMSBPart(LoggingOperator, abc.ABC):

    config: tp.ClassVar[MSBPartOperatorConfig]

    @classmethod
    def poll(cls, context):
        settings = cls.settings(context)

        try:
            cls.config.get_bl_part_type(settings.game)
        except KeyError:
            return False

        msb_path = settings.get_import_msb_path()
        if not is_path_and_file(msb_path):
            return False
        part = getattr(context.scene.soulstruct_game_enums, cls.config.GAME_ENUM_NAME)
        if part in {"", "0"}:
            return False  # no enum option selected
        return True  # MSB exists and a Character part name is selected from enum

    def execute(self, context: bpy.types.Context):
        """Import MSB Part of this subclass's subtype from value of `config.GAME_ENUM_NAME` Blender enum property."""

        settings = self.settings(context)
        msb_import_settings = context.scene.msb_import_settings  # type: MSBImportSettings

        try:
            bl_part_type = self.config.get_bl_part_type(settings.game)
        except KeyError:
            return self.error(
                f"Cannot import MSB Part subtype `{self.config.PART_SUBTYPE}` for game {settings.game.name}."
            )

        part_name = getattr(context.scene.soulstruct_game_enums, self.config.GAME_ENUM_NAME)
        if part_name in {"", "0"}:
            return self.error(f"Invalid MSB {self.config.PART_SUBTYPE} selection: {part_name}")

        if not settings.get_import_map_path():  # validation
            return self.error("Game directory and map stem must be set in Blender's Soulstruct global settings.")

        # We always use the latest MSB, if the setting is enabled.
        msb_stem = settings.get_latest_map_stem_version()
        map_stem = settings.get_oldest_map_stem_version() if not self.config.USE_LATEST_MAP_FOLDER else msb_stem
        msb_path = settings.get_import_msb_path()  # will automatically use latest MSB version if known and enabled
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING
        collection_name = msb_import_settings.get_collection_name(msb_stem, self.config.PART_SUBTYPE)
        part_collection = get_collection(collection_name, context.scene.collection)

        # Get MSB part.
        part_list = getattr(msb, self.config.MSB_LIST_NAME)
        try:
            part = part_list.find_entry_name(part_name)
        except KeyError:
            return self.error(f"MSB {self.config.PART_SUBTYPE} '{part_name}' not found in MSB.")

        try:
            # NOTE: Instance creator may not always use `map_stem` (e.g. characters).
            bl_part = bl_part_type.new_from_part(self, context, settings, map_stem, part, part_collection)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Failed to import MSB {self.config.PART_SUBTYPE} part '{part.name}': {ex}")

        # Select and frame view on new instance.
        self.set_active_obj(bl_part)
        bpy.ops.view3d.view_selected(use_all_regions=False)

        return {"FINISHED"}


class BaseImportAllMSBParts(LoggingOperator, abc.ABC):

    config: tp.ClassVar[MSBPartOperatorConfig]

    @classmethod
    def poll(cls, context):
        settings = cls.settings(context)
        msb_path = settings.get_import_msb_path()

        try:
            cls.config.get_bl_part_type(settings.game)
        except KeyError:
            return False

        if not is_path_and_file(msb_path):
            return False
        return True  # MSB exists and a Character part name is selected from enum

    def invoke(self, context, event):
        """Ask user for confirmation before importing all parts, which can take a long time."""
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):

        start_time = time.perf_counter()

        settings = self.settings(context)
        try:
            bl_part_type = self.config.get_bl_part_type(settings.game)
        except KeyError:
            return self.error(
                f"Cannot import MSB Part subtype `{self.config.PART_SUBTYPE}` for game {settings.game.name}."
            )

        if not settings.get_import_map_path():  # validation
            return self.error("Game directory and map stem must be set in Blender's Soulstruct global settings.")

        msb_import_settings = context.scene.msb_import_settings  # type: MSBImportSettings
        is_name_match = msb_import_settings.get_name_match_filter()
        msb_stem = settings.get_latest_map_stem_version()
        map_stem = settings.get_oldest_map_stem_version() if not self.config.USE_LATEST_MAP_FOLDER else msb_stem
        msb_path = settings.get_import_msb_path()  # will automatically use latest MSB version if known and enabled
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING
        collection_name = msb_import_settings.get_collection_name(msb_stem, self.config.PART_SUBTYPE)
        part_collection = get_collection(collection_name, context.scene.collection)

        part_list = getattr(msb, self.config.MSB_LIST_NAME)
        part_count = 0

        for part in [part for part in part_list if is_name_match(part.name)]:
            try:
                # No need to return instance.
                bl_part_type.new_from_part(self, context, settings, map_stem, part, part_collection)
            except Exception as ex:
                traceback.print_exc()
                self.error(f"Failed to import MSB {self.config.PART_SUBTYPE} part '{part.name}': {ex}")
                continue

            part_count += 1

        if part_count == 0:
            self.warning(
                f"No MSB {self.config.PART_SUBTYPE} parts found with {msb_import_settings.entry_name_match_mode} filter: "
                f"'{msb_import_settings.entry_name_match}'"
            )
            return {"CANCELLED"}

        self.info(
            f"Imported {part_count} / {len(part_list)} MSB {self.config.PART_SUBTYPE} parts in "
            f"{time.perf_counter() - start_time:.3f} seconds (filter: '{msb_import_settings.entry_name_match}')."
        )

        # No change in view after importing all parts.

        return {"FINISHED"}
