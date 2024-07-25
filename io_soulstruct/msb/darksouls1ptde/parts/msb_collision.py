from __future__ import annotations

__all__ = [
    "BlenderMSBCollision",
]

import traceback
import typing as tp

import bpy
from io_soulstruct.exceptions import MissingPartModelError
from io_soulstruct.collision.model_import import *
from io_soulstruct.msb.properties import MSBPartSubtype, MSBCollisionProps
from io_soulstruct.types import *
from io_soulstruct.utilities import *
from soulstruct.base.maps.msb.utils import GroupBitSet128
from soulstruct.darksouls1ptde.maps.enums import CollisionHitFilter
from soulstruct.darksouls1ptde.maps.parts import MSBCollision
from soulstruct_havok.wrappers.hkx2015.hkx_binder import BothResHKXBHD
from .msb_part import BlenderMSBPart

if tp.TYPE_CHECKING:
    from soulstruct.darksouls1ptde.maps.msb import MSB

class BlenderMSBCollision(BlenderMSBPart[MSBCollision, MSBCollisionProps]):
    """Not FLVER-based."""

    OBJ_DATA_TYPE = SoulstructDataType.MESH
    SOULSTRUCT_CLASS = MSBCollision
    PART_SUBTYPE = MSBPartSubtype.COLLISION
    MODEL_SUBTYPES = ["collision_models"]

    data: bpy.types.Mesh  # type override

    AUTO_COLLISION_PROPS = [
        "sound_space_type",
        "place_name_banner_id",
        "force_place_name_banner",
        "play_region_id",
        "stable_footing_flag",
        "camera_1_id",
        "camera_2_id",
        "unk_x27_x28",
        "attached_bonfire",
        "reflect_plane_height",
    ]

    sound_space_type: int
    place_name_banner_id: int
    force_place_name_banner: bool
    play_region_id: int
    stable_footing_flag: int
    camera_1_id: int
    camera_2_id: int
    unk_x27_x28: int
    attached_bonfire: int
    environment_event: bpy.types.Object | None
    reflect_plane_height: float

    @property
    def navmesh_groups(self):
        return self._get_groups_bit_set(self.subtype_properties.get_navmesh_groups_props_128())

    @navmesh_groups.setter
    def navmesh_groups(self, value: set[int] | GroupBitSet128):
        if isinstance(value, GroupBitSet128):
            value = value.enabled_bits
        self._set_groups_bit_set(self.type_properties.get_draw_groups_props_128(), value)

    @property
    def hit_filter(self) -> CollisionHitFilter:
        return CollisionHitFilter(self.subtype_properties.hit_filter)

    @hit_filter.setter
    def hit_filter(self, value: CollisionHitFilter):
        self.subtype_properties.hit_filter = value.name

    @property
    def vagrant_entity_ids(self) -> list[int]:
        return self.subtype_properties.get_vagrant_entity_ids()

    @vagrant_entity_ids.setter
    def vagrant_entity_ids(self, value: list[int]):
        if len(value) != 3:
            raise ValueError("Vagrant entity IDs should have exactly 3 elements.")
        for i in range(3):
            setattr(self.subtype_properties, f"vagrant_entity_ids_{i}", value[i])

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MSBCollision,
        name: str,
        collection: bpy.types.Collection = None,
        map_stem="",
    ) -> tp.Self:

        bl_collision = super().new_from_soulstruct_obj(
            operator, context, soulstruct_obj, name, collection, map_stem
        )  # type: tp.Self

        bl_collision.navmesh_groups = soulstruct_obj.navmesh_groups
        bl_collision.environment_event = cls.entry_ref_to_bl_obj(
            operator, soulstruct_obj, "environment_event", soulstruct_obj.environment_event, SoulstructType.MSB_EVENT
        )
        bl_collision.vagrant_entity_ids = soulstruct_obj.vagrant_entity_ids

        try:
            bl_collision.hit_filter = CollisionHitFilter(soulstruct_obj.hit_filter_id)
        except ValueError:
            operator.warning(
                f"Unknown MSB Collision hit filter ID: {soulstruct_obj.hit_filter_id}. Setting to `Normal`. You can "
                f"extend the enum for this property yourself by editing `MSBCollisionProps.hit_filter.items` "
                f"in add-on module `io_soulstruct/msb/properties.py`, or ask Grimrukh to add it later."
            )

        for name in cls.AUTO_COLLISION_PROPS:
            setattr(bl_collision, name, getattr(soulstruct_obj, name))

        return bl_collision

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        map_stem="",
        msb: MSB = None,
    ) -> MSBCollision:

        msb_collision = super().to_soulstruct_obj(operator, context, map_stem, msb)  # type: MSBCollision

        msb_collision.navmesh_groups = self.navmesh_groups
        msb_collision.environment_event = self.bl_obj_to_entry_ref(
            msb, "environment_event", self.environment_event, msb_collision
        )
        msb_collision.vagrant_entity_ids = self.vagrant_entity_ids

        for name in self.AUTO_COLLISION_PROPS:
            setattr(msb_collision, name, getattr(self, name))

        return msb_collision

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
        model_name: str,
        map_stem: str,
    ) -> bpy.types.MeshObject:
        """Import the Map Collison HKX model of the given name into a collection in the current scene.

        NOTE: `map_stem` should already be set to oldest version if option is enabled. This function is agnostic.
        """
        settings = operator.settings(context)

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


BlenderMSBCollision.add_auto_subtype_props(*BlenderMSBCollision.AUTO_COLLISION_PROPS)
