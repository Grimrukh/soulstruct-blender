from __future__ import annotations

__all__ = [
    "BlenderMSBCollision",
]

import traceback
import typing as tp

import bpy
from io_soulstruct.exceptions import MissingPartModelError, MapCollisionImportError
from io_soulstruct.collision.types import BlenderMapCollision
from io_soulstruct.msb.properties import MSBPartSubtype, MSBCollisionProps
from io_soulstruct.types import *
from io_soulstruct.utilities import *
from soulstruct.base.maps.msb.utils import GroupBitSet128
from soulstruct.darksouls1ptde.maps.enums import CollisionHitFilter
from soulstruct.darksouls1ptde.maps.models import MSBCollisionModel
from soulstruct.darksouls1ptde.maps.parts import MSBCollision
from soulstruct_havok.wrappers.shared import MapCollisionModel, BothResHKXBHD
from .msb_part import BlenderMSBPart

if tp.TYPE_CHECKING:
    from soulstruct.darksouls1ptde.maps.msb import MSB


class BlenderMSBCollision(BlenderMSBPart[MSBCollision, MSBCollisionProps]):
    """Not FLVER-based.

    NOTE: `environment_event` circular reference is not represented in Blender. It is found on MSB export.
    """

    OBJ_DATA_TYPE = SoulstructDataType.MESH
    SOULSTRUCT_CLASS = MSBCollision
    SOULSTRUCT_MODEL_CLASS = MSBCollisionModel
    BLENDER_MODEL_TYPE = SoulstructType.COLLISION
    PART_SUBTYPE = MSBPartSubtype.Collision
    MODEL_SUBTYPES = ["collision_models"]

    __slots__ = []

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
    reflect_plane_height: float

    @property
    def navmesh_groups(self):
        return self._get_groups_bit_set(self.subtype_properties.get_navmesh_groups_props_128())

    @navmesh_groups.setter
    def navmesh_groups(self, value: set[int] | GroupBitSet128):
        if isinstance(value, GroupBitSet128):
            value = value.enabled_bits
        self._set_groups_bit_set(self.subtype_properties.get_navmesh_groups_props_128(), value)

    @property
    def hit_filter(self) -> CollisionHitFilter:
        """Blender property is the name of the enum, not the integer value from the MSB."""
        return CollisionHitFilter[self.subtype_properties.hit_filter]

    @hit_filter.setter
    def hit_filter(self, value: CollisionHitFilter):
        """Blender property is the name of the enum, not the integer value from the MSB."""
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
        try_import_model=True,
        model_collection: bpy.types.Collection = None,
    ) -> tp.Self:

        bl_collision = super().new_from_soulstruct_obj(
            operator, context, soulstruct_obj, name, collection, map_stem, try_import_model, model_collection
        )  # type: tp.Self

        bl_collision.navmesh_groups = soulstruct_obj.navmesh_groups
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
        msb_collision.hit_filter_id = self.hit_filter.value
        msb_collision.vagrant_entity_ids = self.vagrant_entity_ids

        for name in self.AUTO_COLLISION_PROPS:
            setattr(msb_collision, name, getattr(self, name))

        return msb_collision

    @classmethod
    def find_model_mesh(cls, model_name: str, map_stem: str) -> bpy.types.MeshObject:
        """Find the given Collision model in Blender data."""
        obj = find_obj(name=model_name, find_stem=True, soulstruct_type=SoulstructType.COLLISION)
        if obj is None:
            raise MissingPartModelError(f"Collision model mesh '{model_name}' not found in Blender data.")
        # noinspection PyTypeChecker
        return obj

    @classmethod
    def import_model_mesh(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        model_name: str,
        map_stem: str,
        model_collection: bpy.types.Collection = None,
    ) -> bpy.types.MeshObject:
        """Import the Map Collison HKX model of the given name into a collection in the current scene.

        NOTE: `map_stem` should already be set to oldest version if option is enabled. This function is agnostic.
        """
        settings = operator.settings(context)

        if not model_collection:
            model_collection = get_or_create_collection(
                context.scene.collection,
                f"{map_stem} Models",
                f"{map_stem} Collision Models",
                hide_viewport=context.scene.msb_import_settings.hide_model_collections,
            )

        if settings.is_game("DARK_SOULS_PTDE"):
            # No HKX binders; hi and lo-res models are loose HKX files in map directory.
            hi_res_hkx_name = f"h{model_name[1:]}.hkx"
            try:
                hi_res_hkx_path = settings.get_import_map_file_path(hi_res_hkx_name)
            except FileNotFoundError:
                raise FileNotFoundError(f"Cannot find hi-res HKX '{hi_res_hkx_name}' for map {map_stem}.")
            lo_res_hkx_name = f"l{model_name[1:]}.hkx"
            try:
                lo_res_hkx_path = settings.get_import_map_file_path(lo_res_hkx_name)
            except FileNotFoundError:
                raise FileNotFoundError(f"Cannot find lo-res HKX '{lo_res_hkx_name}' for map {map_stem}.")

            try:
                hi_collision = MapCollisionModel.from_path(hi_res_hkx_path)
            except Exception as ex:
                raise MapCollisionImportError(
                    f"Cannot load hi-res HKX '{hi_res_hkx_name}' from map {map_stem}. Error: {ex}"
                )
            try:
                lo_collision = MapCollisionModel.from_path(lo_res_hkx_path)
            except Exception as ex:
                raise MapCollisionImportError(
                    f"Cannot load lo-res HKX '{lo_res_hkx_name}' from map {map_stem}. Error: {ex}"
                )

            # Import single HKX.
            try:
                bl_map_collision = BlenderMapCollision.new_from_soulstruct_obj(
                    operator, context, hi_collision, model_name, collection=model_collection, lo_collision=lo_collision
                )
            except Exception as ex:
                traceback.print_exc()  # for inspection in Blender console
                raise MapCollisionImportError(
                    f"Cannot import HKX '{model_name}' from HKXBHDs in map {map_stem}. Error: {ex}"
                )

        elif settings.is_game("DARK_SOULS_DSR"):
            # NOTE: Hi and lo-res binders could end up being found in different import folders (project vs. game).
            try:
                hi_res_hkxbhd_path = settings.get_import_map_file_path(f"h{map_stem[1:]}.hkxbhd")
            except FileNotFoundError:
                raise FileNotFoundError(f"Cannot find hi-res HKXBHD for map {map_stem}.")
            try:
                lo_res_hkxbhd_path = settings.get_import_map_file_path(f"l{map_stem[1:]}.hkxbhd")
            except FileNotFoundError:
                raise FileNotFoundError(f"Cannot find lo-res HKXBHD for map {map_stem}.")

            both_res_hkxbhd = BothResHKXBHD.from_both_paths(hi_res_hkxbhd_path, lo_res_hkxbhd_path)
            hi_collision, lo_collision = both_res_hkxbhd.get_both_hkx(model_name)

            # Import single HKX.
            try:
                bl_map_collision = BlenderMapCollision.new_from_soulstruct_obj(
                    operator, context, hi_collision, model_name, collection=model_collection, lo_collision=lo_collision
                )
            except Exception as ex:
                traceback.print_exc()  # for inspection in Blender console
                raise MapCollisionImportError(
                    f"Cannot import HKX '{model_name}' from HKXBHDs in map {map_stem}. Error: {ex}"
                )

        else:
            raise MapCollisionImportError(
                f"Cannot yet import HKX Collision models ('{model_name}') for game {settings.game.name} (only DS1)."
            )

        return bl_map_collision.obj


BlenderMSBCollision.add_auto_subtype_props(*BlenderMSBCollision.AUTO_COLLISION_PROPS)
