"""Operators for importing entries from MSB files.

These operators will import entries from MSB files into the current scene. The imported objects will link to the
armature and mesh data of FLVER models found in the apppropriate Blender collection, e.g. "Character Models", and import
that model if it doesn't exist.
"""
from __future__ import annotations

__all__ = [
    "ImportMSBMapCollision",
    "ImportAllMSBMapCollisions",
]

import fnmatch
import re
import time
import traceback
import typing as tp
from pathlib import Path

import bpy
import bpy.ops

from soulstruct.containers import Binder, EntryNotFoundError

from soulstruct_havok.wrappers.hkx2015 import MapCollisionHKX

from io_soulstruct.general.cached import get_cached_file
from io_soulstruct.utilities import *
from io_soulstruct.havok.hkx_map_collision.model_import import *
from .core import *

if tp.TYPE_CHECKING:
    from io_soulstruct.general import SoulstructSettings, SoulstructGameEnums
    from io_soulstruct.type_checking import MSB_TYPING
    from .settings import MSBImportSettings


def find_map_collision_model(model_name: str) -> bpy.types.Object:
    """Find the model of the given type in the 'Map Collision Models' collection in the current scene.

    Returns the Empty parent of all 'h' and 'l' submeshes of the collision (`children`).
    """
    try:
        collection = bpy.data.collections["Map Collision Models"]
    except KeyError:
        raise MissingModelError("Collection 'Map Collision Models' not found in current scene.")
    for obj in collection.objects:
        if obj.name == model_name and obj.type == "EMPTY":
            if not [child for child in obj.children if child.type == "MESH"]:
                raise MissingModelError(f"Collision parent empty '{model_name}' has no child submesh objects.")
            return obj
    raise MissingModelError(f"Model '{model_name}' not found in 'Map Collision Models' collection.")


def import_collision_model(
    operator: LoggingOperator, context, settings: SoulstructSettings, model_name: str
) -> bpy.types.Object:
    """Import the Map Collison HKX model of the given name into a collection in the current scene."""
    if not settings.get_import_map_path():  # validation
        raise HKXMapCollisionImportError(
            "Game directory and map stem must be set in Blender's Soulstruct global settings."
        )

    # Get oldest version of map folder, if option enabled.
    map_stem = settings.get_oldest_map_stem_version()

    # BXF file never has DCX.
    hkxbhd_path = settings.get_import_map_path(f"h{map_stem[1:]}.hkxbhd")
    hkxbdt_path = settings.get_import_map_path(f"h{map_stem[1:]}.hkxbdt")
    if not hkxbhd_path.is_file():
        raise HKXMapCollisionImportError(f"Could not find HKXBHD header file for map '{map_stem}': {hkxbhd_path}")
    if not hkxbdt_path.is_file():
        raise HKXMapCollisionImportError(f"Could not find HKXBDT data file for map '{map_stem}': {hkxbdt_path}")

    entry_name = settings.game.process_dcx_path(f"{model_name}.hkx")

    hkxbxf = Binder.from_path(hkxbhd_path)
    try:
        hkx_entry = hkxbxf.find_entry_name(entry_name)
    except EntryNotFoundError:
        raise HKXMapCollisionImportError(
            f"Could not find HKX map collision entry '{entry_name}' in HKXBHD file '{hkxbhd_path.name}'."
        )

    import_info = HKXImportInfo(hkxbhd_path, hkx_entry.name, hkx_entry.to_binary_file(MapCollisionHKX))

    # If `load_other_resolutions = True`, this maps actual opened file paths to their other-res HKX files.
    # NOTE: Does NOT handle paths that need an entry to be chosen by the user (with queued Binder entries).
    # Those will be handled in the 'BinderChoice' operator.
    other_res_hkxs = {
        (import_info.path, import_info.hkx_name): load_other_res_hkx(
            operator=operator,
            file_path=import_info.path,
            import_info=import_info,
            is_binder=True,
        )
    }  # type: dict[tuple[Path, str], MapCollisionHKX]

    collection = get_collection("Map Collision Models", context.scene.collection)
    importer = HKXMapCollisionImporter(operator, context, collection=collection)

    hkx = import_info.hkx
    hkx_model_name = import_info.hkx_name.split(".")[0]
    other_res_hkx = other_res_hkxs.get((import_info.path, import_info.hkx_name), None)

    operator.info(f"Importing HKX '{hkx_model_name}'.")

    # Import single HKX.
    try:
        hkx_parent, _ = importer.import_hkx(hkx, bl_name=model_name, use_material=True)
    except Exception as ex:
        # Delete any objects created prior to exception.
        for obj in importer.all_bl_objs:
            bpy.data.objects.remove(obj)
        traceback.print_exc()  # for inspection in Blender console
        raise HKXMapCollisionImportError(f"Cannot import HKX: {import_info.path}. Error: {ex}")

    if other_res_hkx is not None:
        # Import other-res HKX.
        other_bl_name = "l" + model_name[1:]
        try:
            hkx_parent, _ = importer.import_hkx(
                other_res_hkx,
                bl_name=other_bl_name,
                use_material=True,
                existing_parent=hkx_parent,
            )
        except Exception as ex:
            # Delete any objects created prior to exception.
            for obj in importer.all_bl_objs:
                bpy.data.objects.remove(obj)
            traceback.print_exc()  # for inspection in Blender console
            raise HKXMapCollisionImportError(f"Cannot import other-res HKX for {import_info.path}. Error: {ex}")

    return hkx_parent

def get_collision_model(
    operator: LoggingOperator, context, settings: SoulstructSettings, model_name: str
) -> bpy.types.Object:
    """Find or create actual Blender collision model parent with submeshes."""
    try:
        return find_map_collision_model(model_name)
    except MissingModelError:
        t = time.perf_counter()
        hkx_parent = import_collision_model(operator, context, settings, model_name)
        operator.info(f"Imported Map Collision Model '{model_name}' in {time.perf_counter() - t:.3f} seconds.")
        return hkx_parent


def create_collision_model_instance(
    hkx_parent: bpy.types.Object,
    linked_name: str,
    collection: bpy.types.Collection,
) -> bpy.types.Object:
    """Create new Empty collision parent whose submesh children use linked meshes."""
    hkx_instance = bpy.data.objects.new(linked_name, None)  # empty parent
    hkx_instance["Model Name"] = hkx_parent.name  # used by exporter to find HKX submesh materials
    for submesh in [child for child in hkx_parent.children if child.type == "MESH"]:
        submesh_instance = bpy.data.objects.new(f"{linked_name} Submesh {submesh.name}", submesh.data)
        submesh_instance.parent = hkx_instance
        collection.objects.link(submesh_instance)
    return hkx_instance


class ImportMSBMapCollision(LoggingOperator):
    bl_idname = "import_scene.msb_map_collision_part"
    bl_label = "Import MSB Collision Part"
    bl_description = "Import selected MSB Collision entry from selected game MSB"

    # TODO: No way to change these properties.

    load_other_resolution: bpy.props.BoolProperty(
        name="Load Other Resolution",
        description="Try to load the other resolution (Hi/Lo) of the selected HKX (possibly in another Binder) and "
                    "parent them under the same empty object with optional MSB transform",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        game_enums = context.scene.soulstruct_game_enums  # type: SoulstructGameEnums
        return game_enums.hkx_map_collision_part not in {"", "0"}

    def execute(self, context):
        settings = self.settings(context)
        settings.save_settings()

        part_name = context.scene.soulstruct_game_enums.hkx_map_collision_part
        if not part_name:
            raise HKXMapCollisionImportError("No MSB map collision part selected.")

        # Get oldest version of map folder, if option enabled.
        map_stem = settings.get_oldest_map_stem_version()
        msb_path = settings.get_import_msb_path()
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING

        # Get MSB part transform.
        collision_part = msb.collisions.find_entry_name(part_name)
        model_name = collision_part.model.get_model_file_stem(map_stem)

        try:
            hkx_model = get_collision_model(self, context, settings, model_name)
        except Exception as ex:
            return self.error(f"Cannot find or import model for MSB collision part '{part_name}': {ex}")

        collection = get_collection(f"{map_stem} Map Collisions", context.scene.collection)
        hkx_instance = create_collision_model_instance(hkx_model, part_name, collection)
        msb_entry_to_obj_transform(collision_part, hkx_instance)

        return {"FINISHED"}


class ImportAllMSBMapCollisions(LoggingOperator):
    bl_idname = "import_scene.all_msb_map_collision_parts"
    bl_label = "Import All MSB Collision Parts"
    bl_description = "Import HKX meshes and MSB transform of every MSB Collision part"

    # TODO: No way to change these properties.

    load_other_resolution: bpy.props.BoolProperty(
        name="Load Other Resolution",
        description="Try to load the other resolution (Hi/Lo) of the selected HKX (possibly in another Binder) and "
                    "parent them under the same empty object with optional MSB transform",
        default=True,
    )

    use_material: bpy.props.BoolProperty(
        name="Use Material",
        description="If enabled, 'HKX Hi' or 'HKX Lo' material will be assigned or created for all collision meshes",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        settings = cls.settings(context)
        msb_path = settings.get_import_msb_path()
        if not is_path_and_file(msb_path):
            return False
        return True  # MSB exists

    def execute(self, context):

        start_time = time.perf_counter()

        settings = self.settings(context)
        settings.save_settings()

        msb_import_settings = context.scene.msb_import_settings  # type: MSBImportSettings

        part_name_match = msb_import_settings.part_name_match
        match msb_import_settings.part_name_match_mode:
            case "GLOB":
                def is_name_match(name: str):
                    return part_name_match in {"", "*"} or fnmatch.fnmatch(name, part_name_match)
            case "REGEX":
                pattern = re.compile(part_name_match)
                def is_name_match(name: str):
                    return part_name_match == "" or re.match(pattern, name)
            case _:  # should never happen
                return self.error(f"Invalid MSB part name match mode: {msb_import_settings.part_name_match_mode}")

        if not settings.get_import_map_path():  # validation
            return self.error("Game directory and map stem must be set in Blender's Soulstruct global settings.")

        map_stem = settings.get_oldest_map_stem_version()  # for FLVERs
        msb_path = settings.get_import_msb_path()  # will automatically use latest MSB version if known and enabled
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING

        part_count = 0
        hkx_instance = None  # for getting final mesh to select

        if msb_import_settings.include_pattern_in_parent_name:
            collection_name = f"{map_stem} Collisions ({part_name_match})"
        else:
            collection_name = f"{map_stem} Collisions"
        collection = get_collection(collection_name, context.scene.collection)

        for collision_part in msb.collisions:

            part_name = collision_part.name
            if not is_name_match(part_name):
                # Part name (NOT model) does not match glob/regex.
                continue

            model_name = collision_part.model.get_model_file_stem(map_stem)
            try:
                hkx_model = get_collision_model(self, context, settings, model_name)
            except Exception as ex:
                self.error(f"Cannot find or import model for MSB collision part '{collision_part.name}': {ex}")
                continue

            hkx_instance = create_collision_model_instance(hkx_model, part_name, collection)
            msb_entry_to_obj_transform(collision_part, hkx_instance)
            part_count += 1

        if part_count == 0:
            self.warning(
                f"No Collision MSB parts found with {msb_import_settings.part_name_match_mode} filter: "
                f"'{part_name_match}'"
            )
            return {"CANCELLED"}

        self.info(
            f"Imported {part_count} / {len(msb.map_pieces)} MSB Collision parts in "
            f"{time.perf_counter() - start_time:.3f} seconds (filter: '{part_name_match}')."
        )

        # Select and frame view on first submesh of (final) collision instance.
        if hkx_instance and hkx_instance.children:
            self.set_active_obj(hkx_instance.children[0])
            bpy.ops.view3d.view_selected(use_all_regions=False)

        return {"FINISHED"}
