"""Import MSB Regions of any shape as Blender Empty objects, with custom shape properties and a custom draw tool.

Much simpler than MSB Part import, obviously, aside from the custom draw logic.
"""
from __future__ import annotations

__all__ = [
    "ImportMSB",
]

import time
import traceback
import typing as tp

from io_soulstruct.exceptions import BatchOperationUnsupportedError, UnsupportedGameTypeError, MissingPartModelError
from io_soulstruct.msb import darksouls1ptde, darksouls1r
from io_soulstruct.general.cached import get_cached_file
from io_soulstruct.utilities import *
from io_soulstruct.utilities.operators import LoggingOperator
from soulstruct.games import *

if tp.TYPE_CHECKING:
    from io_soulstruct.type_checking import *
    from io_soulstruct.msb.types import *


# Maps all games' `MSBPartSubtype` enum names to the MSB import settings bool name.
_IMPORT_MODEL_BOOLS = {
    "MapPiece": "import_map_piece_models",
    "Object": "import_object_models",
    "Asset":  "import_object_models",  # same
    "Character": "import_character_models",
    "PlayerStart": "import_character_models",  # same
    "Collision": "import_collision_models",
    "Navmesh": "import_navmesh_models",
    "DummyObject": "import_object_models",
    "DummyCharacter": "import_character_models",
    "ConnectCollision": "import_collision_models",  # same
}


class ImportMSB(LoggingOperator):
    """Import all Parts, Regions, and Events from active map's MSB.

    All entries must be imported and exported at once. However, Part models are optional, and may be empty.
    """

    bl_idname = "import_scene.msb"
    bl_label = "Import MSB"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Import all Parts, Regions, and Events from the active map's MSB, and selected Model meshes"

    # Note that we don't use the Blender `MSBPartSubtype` enum here, which doesn't include Dummy variants.
    PART_SUBTYPE_ORDER = (
        "MapPiece",
        "Collision",  # environment event references ignored
        "Navmesh",
        "ConnectCollision",  # references Collision

        # These may have Draw Parents from above.
        "Object",
        "Asset",
        "Character",
        "PlayerStart",
        "DummyObject",
        # TODO: "DummyAsset",
        "DummyCharacter",
    )

    @classmethod
    def poll(cls, context):
        settings = cls.settings(context)
        try:
            settings.get_import_msb_path()
        except FileNotFoundError:
            return False
        return True

    def execute(self, context):

        p = time.perf_counter()
        settings = self.settings(context)

        if settings.is_game(DARK_SOULS_PTDE):
            blender_types_module = darksouls1ptde
        elif settings.is_game(DARK_SOULS_DSR):
            blender_types_module = darksouls1r
        else:
            return self.error(f"Unsupported game for MSB import/export: {settings.game.name}")

        def get_bl_region_type(region_: MSB_REGION_TYPING) -> type[IBlenderMSBRegion]:
            try:
                return getattr(blender_types_module, f"Blender{region_.cls_name}")  # type: type[IBlenderMSBRegion]
            except AttributeError:
                raise UnsupportedGameTypeError(f"Unsupported MSB Region subtype: {region_.SUBTYPE_ENUM.name}")

        def get_bl_event_type(event_: MSB_EVENT_TYPING) -> type[IBlenderMSBEvent]:
            try:
                return getattr(blender_types_module, f"Blender{event_.cls_name}")  # type: type[IBlenderMSBEvent]
            except AttributeError:
                raise UnsupportedGameTypeError(f"Unsupported MSB Event subtype: {event_.SUBTYPE_ENUM.name}")

        def get_bl_part_type(part_: MSB_PART_TYPING) -> type[IBlenderMSBPart]:
            cls_name = part_.cls_name.replace("Dummy", "")
            try:
                return getattr(blender_types_module, f"Blender{cls_name}")  # type: type[IBlenderMSBPart]
            except AttributeError:
                raise UnsupportedGameTypeError(f"Unsupported MSB Part subtype: {part_.SUBTYPE_ENUM.name}")

        msb_import_settings = context.scene.msb_import_settings
        msb_stem = settings.get_latest_map_stem_version()
        msb_path = settings.get_import_msb_path()  # will automatically use latest MSB version if known and enabled
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING

        # Two separate sub-collections for MSB entries.
        parts_collection = get_or_create_collection(context.scene.collection, f"{msb_stem} MSB", f"{msb_stem} Parts")
        regions_events_collection = get_or_create_collection(
            context.scene.collection, f"{msb_stem} MSB", f"{msb_stem} Regions/Events"
        )

        # TODO: Delete all created objects if/when an error is raised.

        # 1. Find all Parts that will have their models imported.
        part_name_filter = msb_import_settings.get_name_match_filter()
        parts_with_models = {}
        for part in msb.get_parts():

            if not part.model:
                continue
            subtype_bool = _IMPORT_MODEL_BOOLS[part.SUBTYPE_ENUM.name]
            if not getattr(msb_import_settings, subtype_bool):
                continue  # part subtype models disabled
            if not part_name_filter(part.name):
                continue  # manually excluded

            bl_part_type = get_bl_part_type(part)

            if bl_part_type.MODEL_USES_LATEST_MAP:
                map_dir_stem = settings.get_latest_map_stem_version()
            else:
                map_dir_stem = settings.get_oldest_map_stem_version()

            try:
                bl_part_type.find_model_mesh(part.model.name, map_dir_stem)
            except MissingPartModelError:
                pass  # queue up model to import below
            else:
                continue  # ignore Part with found model

            parts = parts_with_models.setdefault(part.SUBTYPE_ENUM, [])
            parts.append(part)

        # 2. Import all queued Part models.
        for part_subtype, parts in parts_with_models.items():
            bl_part_type = get_bl_part_type(parts[0])
            if bl_part_type.MODEL_USES_LATEST_MAP:
                map_dir_stem = settings.get_latest_map_stem_version()
            else:
                map_dir_stem = settings.get_oldest_map_stem_version()

            try:
                # Import models for this Part subtype in parallel, as much as possible.
                bl_part_type.batch_import_models(self, context, parts, map_stem=map_dir_stem)
            except BatchOperationUnsupportedError:
                # Import models for this Part subtype one by one.
                for part in parts:
                    try:
                        bl_part_type.new_from_soulstruct_obj(
                            self, context, part, part.name, parts_collection, map_dir_stem
                        )
                    except Exception as ex:
                        # Fatal error.
                        traceback.print_exc()
                        return self.error(f"Failed to import {part.cls_name} '{part.name}': {ex}")

        # 3. Import Regions first, as they contain no MSB references.
        region_count = 0
        for region in msb.get_regions():
            bl_region_type = get_bl_region_type(region)
            try:
                # Don't need to get created object or provide a subcollection.
                bl_region_type.new_from_soulstruct_obj(self, context, region, region.name, regions_events_collection)
            except Exception as ex:
                # Fatal error.
                traceback.print_exc()
                return self.error(f"Failed to import {region.cls_name} '{region.name}': {ex}")
            region_count += 1

        # 4. Import Parts in a particular order so references will exist. TODO: Currently DS1 subtypes only.
        part_count = 0
        for part_subtype in self.PART_SUBTYPE_ORDER:
            try:
                part_list_name = msb.resolve_subtype_name(part_subtype)
            except KeyError:
                continue  # not a subtype in this game
            parts = getattr(msb, part_list_name)
            for part in parts:
                bl_part_type = get_bl_part_type(part)
                part_subtype_collection = get_or_create_collection(
                    parts_collection, f"{msb_stem} {bl_part_type.PART_SUBTYPE.get_nice_name()} Parts"
                )
                try:
                    # If model isn't found, an empty one will be created.
                    bl_part_type.new_from_soulstruct_obj(
                        self, context, part, part.name, part_subtype_collection, msb_stem, try_import_model=False
                    )
                except Exception as ex:
                    # Fatal error.
                    traceback.print_exc()
                    return self.error(f"Failed to import {part.cls_name} '{part.name}': {ex}")
                part_count += 1

        # 5. Import Events last, as they may reference Parts and Regions.
        event_count = 0
        for event in msb.get_events():
            bl_event_type = get_bl_event_type(event)
            try:
                bl_event = bl_event_type.new_from_soulstruct_obj(
                    self, context, event, event.name, regions_events_collection, msb_stem
                )
            except Exception as ex:
                # Fatal error.
                traceback.print_exc()
                return self.error(f"Failed to import {event.cls_name} '{event.name}': {ex}")

            if bl_event.PARENT_PROP_NAME:
                # Should exist in Blender among Parts or Regions imported above. If `None`, it's a harmless assignment.
                bl_event.parent = getattr(bl_event, bl_event.PARENT_PROP_NAME)

            event_count += 1

        self.info(
            f"Imported {part_count} Parts, {region_count} Regions, and {event_count} Events from MSB {msb_stem} "
            f"in {time.perf_counter() - p:.3f} seconds."
        )

        return {"FINISHED"}
