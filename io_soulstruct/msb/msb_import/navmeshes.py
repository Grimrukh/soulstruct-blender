"""Operators for importing entries from MSB files.

These operators will import entries from MSB files into the current scene. The imported objects will link to the
armature and mesh data of FLVER models found in the apppropriate Blender collection, e.g. "Character Models", and import
that model if it doesn't exist.
"""
from __future__ import annotations

__all__ = [
    "ImportMSBNavmesh",
    "ImportAllMSBNavmeshes",
]

import fnmatch
import re
import time
import traceback
import typing as tp

import bpy
import bpy.ops

from soulstruct.containers import Binder, EntryNotFoundError
from soulstruct.darksouls1r.maps.navmesh import NVM

from io_soulstruct.general.cached import get_cached_file
from io_soulstruct.utilities import *
from io_soulstruct.navmesh.nvm.model_import import *
from .core import *

if tp.TYPE_CHECKING:
    from io_soulstruct.general import SoulstructSettings
    from io_soulstruct.type_checking import MSB_TYPING
    from .settings import MSBImportSettings


def find_navmesh_model(model_name: str) -> bpy.types.MeshObject:
    """Find the given navmesh model in the 'Navmesh Models' collection in the current scene."""
    try:
        collection = bpy.data.collections["Navmesh Models"]
    except KeyError:
        raise MissingModelError("Collection 'Navmesh Models' not found in current scene.")
    for obj in collection.objects:
        if obj.name == model_name and obj.type == "MESH":
            return obj
    raise MissingModelError(f"Model '{model_name}' not found in 'Navmesh Models' collection.")


def import_navmesh_model(
    operator: LoggingOperator, context, settings: SoulstructSettings, model_name: str
) -> bpy.types.MeshObject:
    if not settings.get_import_map_path():  # validation
        raise NVMImportError(
            "Game directory and map stem must be set in Blender's Soulstruct global settings."
        )

    # Get latest version of map folder, if option enabled.
    map_stem = settings.get_latest_map_stem_version()
    nvmbnd_path = settings.get_import_map_path(f"{map_stem}.nvmbnd")
    if not nvmbnd_path or not nvmbnd_path.is_file():
        raise NVMImportError(f"Could not find NVMBND file for map '{map_stem}': {nvmbnd_path}")

    nvm_entry_name = model_name + ".nvm"  # no DCX in DSR
    nvmbnd = Binder.from_path(nvmbnd_path)
    try:
        nvm_entry = nvmbnd.find_entry_name(nvm_entry_name)
    except EntryNotFoundError:
        raise NVMImportError(f"Could not find NVM entry '{nvm_entry_name}' in NVMBND file '{nvmbnd_path.name}'.")

    import_info = NVMImportInfo(
        nvmbnd_path, nvm_entry.minimal_stem, model_name, nvm_entry.to_binary_file(NVM)
    )

    collection = get_collection("Navmesh Models", context.scene.collection)
    importer = NVMImporter(operator, context, collection=collection)
    operator.info(f"Importing NVM model {import_info.model_file_stem} as '{import_info.bl_name}'.")

    try:
        nvm_model = importer.import_nvm(
            import_info,
            use_material=True,
            create_quadtree_boxes=False,
        )
    except Exception as ex:
        # Delete any objects created prior to exception.
        for obj in importer.all_bl_objs:
            bpy.data.objects.remove(obj)
        traceback.print_exc()  # for inspection in Blender console
        raise NVMImportError(f"Cannot import NVM: {import_info.path}. Error: {ex}")


    return nvm_model


def get_navmesh_model(
    operator: LoggingOperator, context, settings: SoulstructSettings, model_name: str
) -> bpy.types.MeshObject:
    """Find or create actual Blender navmesh."""
    try:
        return find_navmesh_model(model_name)
    except MissingModelError:
        t = time.perf_counter()
        nvm_model = import_navmesh_model(operator, context, settings, model_name)
        operator.info(f"Imported Navmesh Model '{model_name}' in {time.perf_counter() - t:.3f} seconds.")
        return nvm_model


def create_navmesh_model_instance(
    nvm_model: bpy.types.MeshObject,
    linked_name: str,
    collection: bpy.types.Collection,
) -> bpy.types.MeshObject:
    """Create new Mesh linked to model mesh."""
    nvm_instance = bpy.data.objects.new(linked_name, nvm_model.data)
    nvm_instance["Model Name"] = nvm_model.name
    collection.objects.link(nvm_instance)
    # noinspection PyTypeChecker
    return nvm_instance


class ImportMSBNavmesh(LoggingOperator):
    """Import a NVM from the current selected value of listed game MSB navmesh entries."""
    bl_idname = "import_scene.msb_navmesh_part"
    bl_label = "Import Navmesh Part"
    bl_description = "Import transform and model of selected Navmesh MSB part from selected game map"

    # TODO: Currently no way to change these property defaults in GUI.

    use_material: bpy.props.BoolProperty(
        name="Use Material",
        description="If enabled, 'NVM' material will be assigned or created for all imported navmeshes",
        default=True,
    )

    create_quadtree_boxes: bpy.props.BoolProperty(
        name="Create Quadtree Boxes",
        description="If enabled, create quadtree boxes for all imported navmeshes",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        if cls.settings(context).game_variable_name != "DARK_SOULS_DSR":
            return False
        navmesh_part = context.scene.soulstruct_game_enums.navmesh_part
        return navmesh_part not in {"", "0"}

    def execute(self, context):
        settings = self.settings(context)
        settings.save_settings()
        if settings.game_variable_name != "DARK_SOULS_DSR":
            return self.error("MSB Navmesh import from game is only available for Dark Souls Remastered.")

        map_stem = settings.get_latest_map_stem_version()  # NVMBNDs come from latest map version

        part_name = context.scene.soulstruct_game_enums.navmesh_part
        if not part_name:
            return self.error("No MSB navmesh part selected.")
        msb_path = settings.get_import_msb_path()  # will use newest MSB version
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING

        navmesh_part = msb.navmeshes.find_entry_name(part_name)
        nvm_model = get_navmesh_model(self, context, settings, navmesh_part.model.get_model_file_stem(map_stem))
        collection = get_collection(f"{map_stem} Navmeshes", context.scene.collection)
        nvm_instance = create_navmesh_model_instance(nvm_model, part_name, collection)
        msb_entry_to_obj_transform(navmesh_part, nvm_instance)

        self.info(f"Imported MSB navmesh part '{nvm_instance.name}'.")

        return {"FINISHED"}


class ImportAllMSBNavmeshes(LoggingOperator):
    """Import a NVM from the current selected value of listed game MSB navmesh entries."""
    bl_idname = "import_scene.all_msb_navmesh_parts"
    bl_label = "Import All Navmesh Parts"
    bl_description = "Import NVM mesh and MSB transform of every MSB Navmesh part"

    # TODO: Currently no way to change these property defaults in GUI.

    use_material: bpy.props.BoolProperty(
        name="Use Material",
        description="If enabled, 'NVM' material will be assigned or created for all imported navmeshes",
        default=True,
    )

    create_quadtree_boxes: bpy.props.BoolProperty(
        name="Create Quadtree Boxes",
        description="If enabled, create quadtree boxes for all imported navmeshes",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        settings = cls.settings(context)
        if settings.game_variable_name != "DARK_SOULS_DSR":
            return False
        msb_path = settings.get_import_msb_path()
        if not is_path_and_file(msb_path):
            return False
        return True  # MSB exists

    def execute(self, context):

        start_time = time.perf_counter()

        settings = self.settings(context)
        settings.save_settings()
        if settings.game_variable_name != "DARK_SOULS_DSR":
            return self.error("MSB Navmesh import from game is only available for Dark Souls Remastered.")

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
                return self.error(
                    f"Invalid MSB part name match mode: {msb_import_settings.part_name_match}"
                )

        map_stem = settings.get_latest_map_stem_version()  # NVMBNDs come from latest map version
        msb_path = settings.get_import_msb_path()  # will use newest MSB version
        msb = get_cached_file(msb_path, settings.get_game_msb_class())  # type: MSB_TYPING

        used_model_names = {}
        part_count = 0
        nvm_instance = None  # found/created by first part

        if msb_import_settings.include_pattern_in_parent_name:
            collection_name = f"{map_stem} Navmeshes ({part_name_match})"
        else:
            collection_name = f"{map_stem} Navmeshes"
        collection = get_collection(collection_name, context.scene.collection)

        for navmesh_part in msb.navmeshes:

            if not is_name_match(navmesh_part.name):
                # MSB navmesh name (part, not model) does not match glob/regex.
                continue
            part_name = navmesh_part.name

            if navmesh_part.model.name in used_model_names:
                first_part = used_model_names[navmesh_part.model.name]
                self.warning(
                    f"MSB navmesh part '{navmesh_part.name}' uses model '{navmesh_part.model.name}', which has "
                    f"already been loaded from MSB part '{first_part}'. No two MSB Navmesh parts should use the same "
                    f"NVM asset; try duplicating the NVM and and change the MSB model name first."
                )
                continue
            else:
                used_model_names[navmesh_part.model.name] = part_name

            nvm_model = get_navmesh_model(self, context, settings, navmesh_part.model.get_model_file_stem(map_stem))
            nvm_instance = create_navmesh_model_instance(nvm_model, part_name, collection)
            msb_entry_to_obj_transform(navmesh_part, nvm_instance)
            part_count += 1

            # Record model usage.
            used_model_names[navmesh_part.model.name] = navmesh_part.name

        if part_count == 0:
            self.warning(f"No MSB Navmesh parts found (filter: '{part_name_match}').")
            return {"CANCELLED"}

        self.info(
            f"Imported {part_count} / {len(msb.navmeshes)} MSB Navmesh parts in "
            f"{time.perf_counter() - start_time:.3f} seconds (filter: '{part_name_match}')."
        )

        # Select and frame view on (final) newly imported Mesh.
        if nvm_instance:
            self.set_active_obj(nvm_instance)
            bpy.ops.view3d.view_selected(use_all_regions=False)

        return {"FINISHED"}
