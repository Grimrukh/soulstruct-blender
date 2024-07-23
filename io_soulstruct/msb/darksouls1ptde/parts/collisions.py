from __future__ import annotations

__all__ = [
    "BlenderMSBCollision",
]

import traceback
import typing as tp

import bpy
from io_soulstruct.exceptions import MissingPartModelError, MSBPartExportError
from io_soulstruct.general.core import SoulstructSettings
from io_soulstruct.havok.hkx_map_collision.model_import import *
from io_soulstruct.msb.properties import MSBPartSubtype, MSBCollisionProps
from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities import *
from soulstruct.darksouls1ptde.maps.enums import CollisionHitFilter
from soulstruct.darksouls1ptde.maps.parts import MSBCollision
from soulstruct_havok.wrappers.hkx2015.hkx_binder import BothResHKXBHD
from .base import BlenderMSBPart

if tp.TYPE_CHECKING:
    from soulstruct.darksouls1ptde.maps.msb import MSB

class BlenderMSBCollision(BlenderMSBPart):
    """Not FLVER-based."""

    SOULSTRUCT_CLASS = MSBCollision
    PART_SUBTYPE = MSBPartSubtype.COLLISION
    MODEL_SUBTYPES = ["collision_models"]

    @property
    def collision_props(self) -> MSBCollisionProps:
        return self.obj.msb_collision_props

    def set_obj_properties(self, operator: LoggingOperator, entry: MSBCollision):
        super().set_obj_properties(operator, entry)
        props = self.obj.msb_collision_props

        self.set_obj_groups(entry, "navmesh_groups", group_count=4, group_size=32)

        for i in range(3):
            setattr(props, f"vagrant_entity_ids_{i}", entry.vagrant_entity_ids[i])

        try:
            props.hit_filter = CollisionHitFilter(entry.hit_filter_id).name
        except ValueError:
            operator.warning(
                f"Unknown MSB Collision hit filter ID: {entry.hit_filter_id}. Setting to `Normal`. You can "
                f"extend the enum for this property yourself by editing `MSBCollisionProps.hit_filter.items` "
                f"in add-on module `io_soulstruct/msb/properties.py`, or ask Grimrukh to add it later."
            )
            props.hit_filter = "Normal"

        # TODO: Could potentially automate, or store event position + unknown data on Collision object itself.
        self.set_obj_entry_reference(operator, props, "environment_event", entry, SoulstructType.MSB_EVENT)

        self.set_obj_generic_props(
            entry,
            props,
            skip_prefixes=("navmesh_groups_", "vagrant_entity_ids_"),
            skip_names={"hit_filter", "environment_event"},
        )

    def set_entry_properties(self, operator: LoggingOperator, entry: MSBCollision, msb: MSB):
        super().set_entry_properties(operator, entry, msb)
        props = self.collision_props

        self.set_part_groups(entry, "navmesh_groups", group_count=4, group_size=32)

        for i in range(3):
            entry.vagrant_entity_ids[i] = getattr(props, f"vagrant_entity_ids_{i}")

        self.set_part_entry_reference(props.environment_event, entry, "environment_event", msb)

        try:
            entry.hit_filter_id = CollisionHitFilter[props.hit_filter].value
        except KeyError:
            # Not a case that can be handled, unlike import (but much rarer).
            raise MSBPartExportError(
                f"MSB Collision hit filter name '{props.hit_filter}' is not recognized as a value enum name in "
                f"Soulstruct. This is strange and suggests the Blender add-on is out of sync with the `soulstruct` "
                f"package. You can modify the enum for this property yourself by editing `CollisionHitFilter` in "
                f"add-on module `io_soulstruct/darksouls1ptde/maps/enums.py`."
            )

        self.set_entry_generic_props(
            props,
            entry,
            skip_prefixes=("navmesh_groups_", "vagrant_entity_ids_"),
            skip_names={"hit_filter", "environment_event"},
        )

    @classmethod
    def find_model(cls, model_name: str, map_stem: str) -> bpy.types.MeshObject:
        """Find the model of the given type in the 'Map Collision Models' collection in the current scene.

        Returns the Empty parent of all 'h' and 'l' submeshes of the collision (`children`).
        """
        collection_name = f"{map_stem} Collision Models"
        try:
            collection = bpy.data.collections[collection_name]
        except KeyError:
            raise MissingPartModelError(f"Collection '{collection_name}' not found in current scene.")
        for obj in collection.objects:
            if obj.name == model_name and obj.type == "MESH":
                return obj
        raise MissingPartModelError(f"Collision model mesh '{model_name}' not found in '{collection_name}' collection.")

    @classmethod
    def import_model(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        settings: SoulstructSettings,
        model_name: str,
        map_stem: str,
    ) -> bpy.types.MeshObject:
        """Import the Map Collison HKX model of the given name into a collection in the current scene.

        NOTE: `map_stem` should already be set to oldest version if option is enabled. This function is agnostic.
        """

        # NOTE: Hi and lo-res binders could come from different import folders (project vs. game).
        hi_res_hkxbhd_path = settings.get_import_map_path(f"h{map_stem[1:]}.hkxbhd")
        lo_res_hkxbhd_path = settings.get_import_map_path(f"l{map_stem[1:]}.hkxbhd")
        both_res_hkxbhd = BothResHKXBHD.from_both_paths(hi_res_hkxbhd_path, lo_res_hkxbhd_path)
        hi_hkx, lo_hkx = both_res_hkxbhd.get_both_hkx(model_name)
        collection = get_collection(f"{map_stem} Collision Models", context.scene.collection)

        # Import single HKX.
        try:
            hkx_model = import_hkx_model_merged(hi_hkx, model_name=model_name, lo_hkx=lo_hkx)
        except Exception as ex:
            traceback.print_exc()  # for inspection in Blender console
            raise HKXMapCollisionImportError(
                f"Cannot import HKX '{model_name}' from HKXBHDs in map {map_stem}. Error: {ex}"
            )
        collection.objects.link(hkx_model)
        for child in hkx_model.children:
            collection.objects.link(child)

        # TODO: HKX import is so fast that this just slows the console down when importing all collisions.
        # operator.info(f"Imported HKX '{hkx_model.name}' from model '{model_name}' in map {map_stem}.")

        return hkx_model
