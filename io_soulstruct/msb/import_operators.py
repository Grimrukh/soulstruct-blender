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
from soulstruct.base.maps.msb import BaseMSBSubtype
from soulstruct.darksouls1ptde.maps import MSB as PTDE_MSB
from soulstruct.darksouls1r.maps import MSB as DSR_MSB
from soulstruct.demonssouls.maps import MSB as DES_MSB
from soulstruct.games import *

from io_soulstruct.msb.types import darksouls1ptde, darksouls1r, demonssouls
from io_soulstruct.general.cached import get_cached_file
from io_soulstruct.utilities import *
from io_soulstruct.utilities.operators import LoggingOperator, LoggingImportOperator
from .operator_config import *
from .properties import MSBRegionSubtype, MSBPartSubtype, MSBEventSubtype

if tp.TYPE_CHECKING:
    from io_soulstruct.type_checking import *
    from io_soulstruct.msb.types.base import *
    from .types.base.models import BaseBlenderMSBModelImporter


# Maps all games' `MSBModelSubtype` enum names to the MSB import settings bool name.
_IMPORT_MODEL_BOOLS = {
    "MapPieceModel": "import_map_piece_models",
    "ObjectModel": "import_object_models",
    "AssetModel":  "import_object_models",  # same
    "CharacterModel": "import_character_models",
    "PlayerModel": "import_character_models",  # same
    "CollisionModel": "import_collision_models",
    "NavmeshModel": "import_navmesh_models",
}


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

    # TODO: Not a fan of how these keys are Soulstruct enums, but the ones below are Blender enums.
    #  (It's because there is no `MSBModelSubtype` enum in Blender, as MSB Models aren't a `SoulstructType`.)
    msb_model_importers = blender_types_module.MSB_MODEL_IMPORTERS
    msb_model_importers: dict[BaseMSBSubtype, BaseBlenderMSBModelImporter]

    # NOTE: The keys of these are the *Blender* enums of the same name as the true MSB subtype enums.
    bl_region_classes = BLENDER_MSB_REGION_CLASSES[settings.game]
    bl_part_classes = BLENDER_MSB_PART_CLASSES[settings.game]
    bl_event_classes = BLENDER_MSB_EVENT_CLASSES[settings.game]

    # Two separate sub-collections for MSB entries: Parts, and Regions/Events combined.
    parts_collection = get_or_create_collection(context.scene.collection, f"{msb_stem} MSB", f"{msb_stem} Parts")
    regions_events_collection = get_or_create_collection(
        context.scene.collection, f"{msb_stem} MSB", f"{msb_stem} Regions/Events"
    )

    # TODO: Delete all created objects if/when an error is raised.

    # Batch-import all requested `MSBModel` file types (if not found in Blender).
    model_name_filter = msb_import_settings.get_model_name_match_filter()
    for model_subtype, model_list in msb.get_models_dict().items():
        subtype_bool = _IMPORT_MODEL_BOOLS[model_subtype.name]
        if not getattr(msb_import_settings, subtype_bool):
            continue  # import of this Model type is disabled

        model_importer = msb_model_importers[model_subtype]
        models = [model for model in model_list if model_name_filter(model.name)]
        if models:
            # Note that ALL Model types now support batch import. Models that already exist in Blender (of the expected
            # object type, Soulstruct type, and model name) will be skipped, regardless of their Collection.
            operator.info(f"Importing (up to) {len(models)} `{model_subtype.name}` model files in parallel.")
            model_map_stem = oldest_map_stem if model_importer.use_oldest_map_stem else msb_stem
            model_importer.batch_import_model_meshes(operator, context, models, map_stem=model_map_stem)

    # All MSB inter-entry reference fields are set later, so it doesn't matter what order we create the MSB entry
    # objects in Blender.
    msb_and_bl_regions = []
    msb_and_bl_events = []
    msb_and_bl_parts = []

    for region_subtype, msb_region_list in msb.get_regions_dict():
        bl_region_subtype = MSBRegionSubtype[region_subtype.name]
        bl_region_class = bl_region_classes[bl_region_subtype]  # type: type[BaseBlenderMSBRegion]
        for region in msb_region_list:
            try:
                # Don't need to get created object or provide a subcollection.
                bl_region = bl_region_class.new_from_soulstruct_obj(
                    operator, context, region, region.name, regions_events_collection
                )
            except Exception as ex:
                # Fatal error.
                traceback.print_exc()
                return operator.error(f"Failed to import {region.cls_name} '{region.name}': {ex}")
            msb_and_bl_regions.append((region, bl_region))

    for part_subtype, msb_part_list in msb.get_parts_dict():
        bl_part_subtype = MSBPartSubtype[part_subtype.name]
        bl_part_class = bl_part_classes[bl_part_subtype]  # type: type[BaseBlenderMSBPart]
        part_subtype_collection = get_or_create_collection(
            parts_collection,
            f"{msb_stem} {bl_part_subtype.get_nice_name()} Parts",
        )
        for part in msb_part_list:
            try:
                bl_part = bl_part_class.new_from_soulstruct_obj(
                    operator,
                    context,
                    part,
                    part.name,
                    collection=part_subtype_collection,
                    map_stem=msb_stem,
                    armature_mode=msb_import_settings.part_armature_mode,
                )
            except Exception as ex:
                # Fatal error.
                traceback.print_exc()
                return operator.error(f"Failed to import {part.cls_name} '{part.name}': {ex}")
            msb_and_bl_parts.append((part, bl_part))

    for event_subtype, msb_event_list in msb.get_events_dict():
        bl_event_type = MSBEventSubtype[event_subtype.name]
        bl_event_class = bl_event_classes[bl_event_type]  # type: type[BaseBlenderMSBEvent]
        for event in msb_event_list:
            try:
                bl_event = bl_event_class.new_from_soulstruct_obj(
                    operator, context, event, event.name, regions_events_collection
                )
            except Exception as ex:
                # Fatal error.
                traceback.print_exc()
                return operator.error(f"Failed to import {event.cls_name} '{event.name}': {ex}")

            msb_and_bl_events.append((event, bl_event))

    for msb_entry, bl_obj in msb_and_bl_parts + msb_and_bl_regions + msb_and_bl_events:
        bl_obj.resolve_bl_entry_refs(operator, msb_entry)

    for _, bl_event in msb_and_bl_events:
        if bl_event.PARENT_PROP_NAME:
            # Should exist in Blender among Parts or Regions imported above. If `None`, it's a harmless assignment.
            bl_event.parent = getattr(bl_event, bl_event.PARENT_PROP_NAME)

    part_count = len(msb_and_bl_parts)
    region_count = len(msb_and_bl_regions)
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
    def poll(cls, context) -> bool:
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
    def poll(cls, context) -> bool:
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
