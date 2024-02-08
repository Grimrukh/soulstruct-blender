from __future__ import annotations

__all__ = [
    "MissingModelError",
    "find_flver_model",
    "create_flver_model_instance",
    "msb_entry_to_obj_transform",
    "BaseImportMSBPart",
]

import time
import traceback
import typing as tp

import bpy

from io_soulstruct.general.cached import get_cached_file
from io_soulstruct.general.core import SoulstructSettings
from io_soulstruct.utilities import *
from io_soulstruct.utilities.operators import LoggingOperator
from io_soulstruct.utilities.misc import *
from .settings import MSBImportSettings

if tp.TYPE_CHECKING:
    from soulstruct.base.maps.msb.parts import BaseMSBPart
    from soulstruct.base.maps.msb.regions import BaseMSBRegion
    from io_soulstruct.type_checking import MSB_TYPING


class MissingModelError(Exception):
    """Raised when a model file cannot be found in a Blender collection."""


def find_flver_model(model_type: str, model_name: str) -> tuple[bpy.types.ArmatureObject | None, bpy.types.MeshObject]:
    """Find the model of the given type in a 'Models' collection in the current scene."""
    try:
        collection = bpy.data.collections[f"{model_type} Models"]
    except KeyError:
        raise MissingModelError(f"Collection '{model_type} Models' not found in current scene.")
    for obj in collection.objects:
        if obj.name == model_name:
            if obj.type == "ARMATURE":
                mesh_obj = next((child for child in obj.children if child.type == "MESH"), None)
                if not mesh_obj:
                    raise MissingModelError(f"Armature '{model_name}' has no child mesh object.")
                return obj, mesh_obj
            elif obj.type == "MESH":  # Map Piece with no armature (acceptable)
                return None, obj
    raise MissingModelError(f"Model '{model_name}' not found in '{model_type} Models' collection.")


def create_flver_model_instance(
    context,
    armature: bpy.types.ArmatureObject | None,
    mesh: bpy.types.MeshObject,
    linked_name: str,
    collection: bpy.types.Collection,
) -> tuple[bpy.types.ArmatureObject | None, bpy.types.MeshObject]:
    """Create armature (optional) and mesh objects that link to the given armature and mesh data.

    NOTE: Does NOT copy dummy children from the source model. These aren't needed for linked MSB part instances, and
    will be found in the source model when exported (using 'Model Name') if needed. (Of course, Map Pieces in early
    games don't have dummies anyway.)
    """

    linked_mesh_obj = bpy.data.objects.new(f"{linked_name} Mesh" if armature else linked_name, mesh.data)
    collection.objects.link(linked_mesh_obj)

    if armature:
        linked_armature_obj = bpy.data.objects.new(linked_name, armature.data)
        collection.objects.link(linked_armature_obj)
        # Parent mesh to armature. This is critical for proper animation behavior (especially with root motion).
        linked_mesh_obj.parent = linked_armature_obj
        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action="DESELECT")
        linked_mesh_obj.select_set(True)
        context.view_layer.objects.active = linked_mesh_obj
        bpy.ops.object.modifier_add(type="ARMATURE")
        armature_mod = linked_mesh_obj.modifiers["Armature"]
        armature_mod.object = linked_armature_obj
        armature_mod.show_in_editmode = True
        armature_mod.show_on_cage = True
        linked_armature_obj["Model Name"] = armature.name  # used by exporter to find FLVER properties
        # noinspection PyTypeChecker
        return linked_armature_obj, linked_mesh_obj

    # No armature: link Mesh instead.
    linked_mesh_obj["Model Name"] = mesh.name  # used by exporter to find FLVER properties

    # noinspection PyTypeChecker
    return None, linked_mesh_obj


def msb_entry_to_obj_transform(msb_entry: BaseMSBPart | BaseMSBRegion, obj: bpy.types.Object):
    game_transform = Transform.from_msb_entry(msb_entry)
    obj.location = game_transform.bl_translate
    obj.rotation_euler = game_transform.bl_rotate
    obj.scale = game_transform.bl_scale


class BaseImportMSBPart(LoggingOperator):

    PART_TYPE_NAME: str  # e.g. 'Character'
    PART_TYPE_NAME_PLURAL: str  # e.g. 'Characters'
    MSB_LIST_NAME: str  # e.g. 'characters'
    GAME_ENUM_NAME: str | None  # e.g. 'character_part' or `None` for all-part importers

    @classmethod
    def poll(cls, context):
        settings = cls.settings(context)
        msb_path = settings.get_import_msb_path()
        if not is_path_and_file(msb_path):
            return False
        if cls.GAME_ENUM_NAME is not None:
            part = getattr(context.scene.soulstruct_game_enums, cls.GAME_ENUM_NAME)
            if part in {"", "0"}:
                return False  # no enum option selected
        return True  # MSB exists and a Character part name is selected from enum

    def import_enum_part(self, context):

        part_name = getattr(context.scene.soulstruct_game_enums, self.GAME_ENUM_NAME)
        if part_name in {"", "0"}:
            return self.error(f"Invalid MSB {self.PART_TYPE_NAME} selection: {part_name}")

        settings = self.settings(context)
        settings.save_settings()
        msb_import_settings = context.scene.msb_import_settings  # type: MSBImportSettings

        if not settings.get_import_map_path():  # validation
            return self.error("Game directory and map stem must be set in Blender's Soulstruct global settings.")

        # We always use the latest MSB, if the setting is enabled.
        msb_stem = settings.get_latest_map_stem_version()
        msb_path = settings.get_import_msb_path()  # will automatically use latest MSB version if known and enabled
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING
        collection_name = msb_import_settings.get_collection_name(msb_stem, self.PART_TYPE_NAME_PLURAL)
        part_collection = get_collection(collection_name, context.scene.collection)

        # Get MSB part.
        part_list = getattr(msb, self.MSB_LIST_NAME)
        try:
            part = part_list.find_entry_name(part_name)
        except KeyError:
            return self.error(f"MSB {self.PART_TYPE_NAME} '{part_name}' not found in MSB.")

        try:
            # NOTE: Instance creator may not always use `map_stem` (e.g. characters).
            instance = self._create_part_instance(context, settings, msb_stem, part, part_collection)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Failed to import MSB {self.PART_TYPE_NAME} part '{part.name}': {ex}")

        # Select and frame view on new instance.
        self.set_active_obj(instance)
        bpy.ops.view3d.view_selected(use_all_regions=False)

        return {"FINISHED"}

    def import_all_parts(self, context):

        start_time = time.perf_counter()

        settings = self.settings(context)
        settings.save_settings()

        if not settings.get_import_map_path():  # validation
            return self.error("Game directory and map stem must be set in Blender's Soulstruct global settings.")

        msb_import_settings = context.scene.msb_import_settings  # type: MSBImportSettings
        is_name_match = msb_import_settings.get_name_match_filter()
        msb_stem = settings.get_latest_map_stem_version()
        msb_path = settings.get_import_msb_path()  # will automatically use latest MSB version if known and enabled
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING
        collection_name = msb_import_settings.get_collection_name(msb_stem, self.PART_TYPE_NAME_PLURAL)
        part_collection = get_collection(collection_name, context.scene.collection)

        part_list = getattr(msb, self.MSB_LIST_NAME)
        part_count = 0

        for part in [part for part in part_list if is_name_match(part.name)]:
            try:
                self._create_part_instance(context, settings, msb_stem, part, part_collection)
            except Exception as ex:
                traceback.print_exc()
                self.error(f"Failed to import MSB {self.PART_TYPE_NAME} part '{part.name}': {ex}")
                continue

            part_count += 1

        if part_count == 0:
            self.warning(
                f"No MSB {self.PART_TYPE_NAME} parts found with {msb_import_settings.part_name_match_mode} filter: "
                f"'{msb_import_settings.part_name_match}'"
            )
            return {"CANCELLED"}

        self.info(
            f"Imported {part_count} / {len(part_list)} MSB {self.PART_TYPE_NAME} parts in "
            f"{time.perf_counter() - start_time:.3f} seconds (filter: '{msb_import_settings.part_name_match}')."
        )

        # No change in view after importing all parts.

        return {"FINISHED"}

    def _create_part_instance(
        self, context, settings: SoulstructSettings, map_stem: str, part: BaseMSBPart, collection: bpy.types.Collection
    ) -> bpy.types.Object:
        """Get or create model and create a linked instance with relevant MSB part data (transform, etc.)."""
        raise NotImplementedError
