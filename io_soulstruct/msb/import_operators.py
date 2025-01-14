"""Import MSB Regions of any shape as Blender Empty objects, with custom shape properties and a custom draw tool.

Much simpler than MSB Part import, obviously, aside from the custom draw logic.
"""
from __future__ import annotations

__all__ = [
    "ImportMapMSB",
    "ImportAnyMSB",
]

import time
import traceback
import typing as tp
from pathlib import Path

import bpy
from soulstruct.darksouls1ptde.maps import MSB as PTDE_MSB
from soulstruct.darksouls1r.maps import MSB as DSR_MSB
from soulstruct.demonssouls.maps import MSB as DES_MSB
from soulstruct.games import *
from soulstruct.utilities.misc import IDList

from io_soulstruct.exceptions import BatchOperationUnsupportedError, UnsupportedGameTypeError, MissingPartModelError
from io_soulstruct.msb import darksouls1ptde, darksouls1r, demonssouls
from io_soulstruct.msb.properties import MSBPartSubtype
from io_soulstruct.general.cached import get_cached_file
from io_soulstruct.utilities import *
from io_soulstruct.utilities.operators import LoggingOperator, LoggingImportOperator

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
    "Protoboss": "import_character_models",  # same
    "Navmesh": "import_navmesh_models",
    "DummyObject": "import_object_models",
    "DummyCharacter": "import_character_models",
    "ConnectCollision": "import_collision_models",  # same
}


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
    "Protoboss",
    "DummyObject",
    # TODO: "DummyAsset",
    "DummyCharacter",
)


def _import_msb(
    operator: LoggingOperator, context: Context, msb: MSB_TYPING, msb_stem: str, oldest_map_stem: str
) -> set[str]:

    settings = operator.settings(context)
    msb_import_settings = context.scene.msb_import_settings
    p = time.perf_counter()

    if settings.is_game(DARK_SOULS_PTDE):
        blender_types_module = darksouls1ptde
    elif settings.is_game(DARK_SOULS_DSR):
        blender_types_module = darksouls1r
    elif settings.is_game(DEMONS_SOULS):
        blender_types_module = demonssouls
    else:
        return operator.error(f"Unsupported game for MSB import/export: {settings.game.name}")

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

    # Two separate sub-collections for MSB entries: Parts, and Regions/Events combined.
    parts_collection = get_or_create_collection(context.scene.collection, f"{msb_stem} MSB", f"{msb_stem} Parts")
    regions_events_collection = get_or_create_collection(
        context.scene.collection, f"{msb_stem} MSB", f"{msb_stem} Regions/Events"
    )

    # TODO: Delete all created objects if/when an error is raised.

    # 1. Find all Parts that will have their models imported.
    part_name_filter = msb_import_settings.get_name_match_filter()
    batched_parts_with_models = {}  # for batch import attempt
    all_parts_with_models = IDList()  # for backup single import attempt
    for part in msb.get_parts():

        if not part.model:
            continue
        subtype_bool = _IMPORT_MODEL_BOOLS[part.SUBTYPE_ENUM.name]
        if not getattr(msb_import_settings, subtype_bool):
            continue  # part subtype models disabled
        if not part_name_filter(part.name):
            continue  # manually excluded

        bl_part_type = get_bl_part_type(part)
        map_dir_stem = oldest_map_stem if bl_part_type.MODEL_USES_OLDEST_MAP_VERSION else msb_stem

        try:
            bl_part_type.find_model_mesh(part.model.name, map_dir_stem)
        except MissingPartModelError:
            pass  # queue up model to import below
        else:
            continue  # ignore Part with found model

        if part.SUBTYPE_ENUM in batched_parts_with_models:
            parts = batched_parts_with_models[part.SUBTYPE_ENUM][1]
        else:
            parts = IDList()
            batched_parts_with_models[part.SUBTYPE_ENUM] = (bl_part_type, parts)
        parts.append(part)

    # 2. Try to batch-import all queued Part models.
    for part_subtype, (bl_part_type, parts) in tuple(batched_parts_with_models.items()):
        map_dir_stem = oldest_map_stem if bl_part_type.MODEL_USES_OLDEST_MAP_VERSION else msb_stem

        try:
            # Import models for this Part subtype in parallel, as much as possible.
            operator.info(f"Importing {bl_part_type.PART_SUBTYPE.get_nice_name()} models in parallel.")
            bl_part_type.batch_import_models(operator, context, parts, map_stem=map_dir_stem)
        except BatchOperationUnsupportedError:
            # Import models for this Part subtype one by one below.
            all_parts_with_models.extend(parts)

    # 3. Import Regions first, as they contain no MSB references.
    region_count = 0
    for region in msb.get_regions():
        bl_region_type = get_bl_region_type(region)
        try:
            # Don't need to get created object or provide a subcollection.
            bl_region_type.new_from_soulstruct_obj(operator, context, region, region.name, regions_events_collection)
        except Exception as ex:
            # Fatal error.
            traceback.print_exc()
            return operator.error(f"Failed to import {region.cls_name} '{region.name}': {ex}")
        region_count += 1

    # 4. Import Parts in a particular order so references will exist. TODO: Currently DS1 subtypes only.
    # Note that Collision references to Environment Events are handled AFTER Event import below (only delayed case).
    msb_and_bl_parts = []
    for part_subtype in PART_SUBTYPE_ORDER:
        try:
            part_list_name = msb.resolve_subtype_name(part_subtype)
        except KeyError:
            continue  # not a subtype in this game
        parts = getattr(msb, part_list_name)
        for part in parts:
            bl_part_type = get_bl_part_type(part)
            part_subtype_collection = get_or_create_collection(
                parts_collection,
                f"{msb_stem} {bl_part_type.PART_SUBTYPE.get_nice_name()} Parts",
            )
            try:
                # We only import the model here if models were requested for this part subtype and batch import for
                # this subtype was unsupported above. Otherwise, an empty model will be created (with a warning).
                try_import_model = part in all_parts_with_models
                bl_part = bl_part_type.new_from_soulstruct_obj(
                    operator,
                    context,
                    part,
                    part.name,
                    collection=part_subtype_collection,
                    map_stem=msb_stem,
                    try_import_model=try_import_model,
                )
            except Exception as ex:
                # Fatal error.
                traceback.print_exc()
                return operator.error(f"Failed to import {part.cls_name} '{part.name}': {ex}")
            msb_and_bl_parts.append((part, bl_part))

    # 5. Import Events last, as they may reference Parts and Regions.
    msb_and_bl_events = []
    for event in msb.get_events():
        bl_event_type = get_bl_event_type(event)
        try:
            bl_event = bl_event_type.new_from_soulstruct_obj(
                operator, context, event, event.name, regions_events_collection, msb_stem
            )
        except Exception as ex:
            # Fatal error.
            traceback.print_exc()
            return operator.error(f"Failed to import {event.cls_name} '{event.name}': {ex}")

        if bl_event.PARENT_PROP_NAME:
            # Should exist in Blender among Parts or Regions imported above. If `None`, it's a harmless assignment.
            bl_event.parent = getattr(bl_event, bl_event.PARENT_PROP_NAME)

        msb_and_bl_events.append((event, bl_event))

    # 6. Set Collision references to Environment Events.
    collisions = [(msb_c, bl_c) for msb_c, bl_c in msb_and_bl_parts if bl_c.PART_SUBTYPE == MSBPartSubtype.Collision]
    for msb_collision, bl_collision in collisions:
        msb_collision: MSB_COLLISION_TYPING
        bl_collision: darksouls1ptde.BlenderMSBCollision
        if msb_collision.environment_event:
            # Find environment event by searching through the list of events created above, NOT by name (as it MUST
            # exist and MUST have been imported, and MSB event names may not be unique).
            for msb_event, bl_event in msb_and_bl_events:
                if msb_event is msb_collision.environment_event:  # by ID
                    bl_collision.environment_event = bl_event.obj
                    break
            else:
                operator.warning(
                    f"Collision '{msb_collision.name}' references Environment Event "
                    f"'{msb_collision.environment_event.name}', but the Environment Event was not found among imported "
                    f"MSB Events in Blender. Left Collision -> Environment reference empty."
                )

    part_count = len(msb_and_bl_parts)
    event_count = len(msb_and_bl_events)

    operator.info(
        f"Imported {part_count} Parts, {region_count} Regions, and {event_count} Events from MSB {msb_stem} "
        f"in {time.perf_counter() - p:.3f} seconds."
    )

    return {"FINISHED"}


class ImportMapMSB(LoggingOperator):
    """Import all Parts, Regions, and Events from active map's MSB.

    All entries must be imported and exported at once. However, Part models are optional, and may be empty.
    """

    bl_idname = "import_scene.map_msb"
    bl_label = "Import MSB"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Import all Parts, Regions, and Events from the active map's MSB, with selected Model meshes"

    @classmethod
    def poll(cls, context):
        settings = cls.settings(context)
        if not settings.game_config.msb_class:
            return False  # unsupported
        try:
            settings.get_import_msb_path()
        except FileNotFoundError:
            return False
        return True

    def execute(self, context):

        settings = self.settings(context)

        msb_stem = settings.get_latest_map_stem_version()
        msb_path = settings.get_import_msb_path()  # will automatically use latest MSB version if known and enabled
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING
        oldest_map_stem = settings.get_oldest_map_stem_version(msb_stem)

        return _import_msb(self, context, msb, msb_stem, oldest_map_stem)


class ImportAnyMSB(LoggingImportOperator):
    """Import all Parts, Regions, and Events from active map's MSB.

    All entries must be imported and exported at once. However, Part models are optional, and may be empty.
    """

    bl_idname = "import_scene.any_msb"
    bl_label = "Import MSB"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Import all Parts, Regions, and Events from selected MSB or JSON, with selected Model meshes"

    filter_glob: bpy.props.StringProperty(
        default="*.msb;*.msb.dcx;*.json",
        options={'HIDDEN'},
        maxlen=255,
    )

    directory: bpy.props.StringProperty(options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        settings = cls.settings(context)
        if not settings.game_config.msb_class:
            return False  # unsupported
        return True

    def execute(self, context):

        settings = self.settings(context)
        if settings.is_game("DARK_SOULS_PTDE"):
            msb_class = PTDE_MSB
        elif settings.is_game("DARK_SOULS_DSR"):
            msb_class = DSR_MSB
        elif settings.is_game("DEMONS_SOULS"):
            msb_class = DES_MSB
        else:
            return self.error(f"Unsupported game for MSB import/export: {settings.game.name}")

        msb_path = Path(self.filepath)
        msb_stem = msb_path.name.split(".")[0]
        oldest_map_stem = settings.get_oldest_map_stem_version(msb_stem)

        if msb_path.suffix == ".json":
            try:
                msb = msb_class.from_json(msb_path)
            except Exception as ex:
                return self.error(f"Failed to load MSB from JSON: {ex}")
        else:
            try:
                msb = msb_class.from_path(msb_path)
            except Exception as ex:
                return self.error(f"Failed to load MSB file: {ex}")

        return _import_msb(self, context, msb, msb_stem, oldest_map_stem)
