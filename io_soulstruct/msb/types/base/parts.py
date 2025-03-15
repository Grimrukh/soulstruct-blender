from __future__ import annotations

__all__ = [
    "BaseBlenderMSBPart",
]

import abc
import typing as tp

import bpy
from mathutils import Vector, Euler

from soulstruct.base.maps.msb.utils import BitSet

from io_soulstruct.msb.properties import MSBPartSubtype, MSBPartArmatureMode, MSBPartProps
from io_soulstruct.msb.types.adapters import (
    SoulstructFieldAdapter, MSBPartGroupsAdapter, MSBPartModelAdapter, get_part_game_name
)
from io_soulstruct.msb.types.base import BaseBlenderMSBEntry, TYPE_PROPS_T, SUBTYPE_PROPS_T, MSB_T
from io_soulstruct.msb.types.base.msb_protocols import *
from io_soulstruct.utilities import *

from .part_armature_duplicator import PartArmatureDuplicator

PART_T = tp.TypeVar("PART_T", bound=MSBPartProtocol)
BIT_SET_T = tp.TypeVar("BIT_SET_T", bound=BitSet)


class BaseBlenderMSBPart(
    BaseBlenderMSBEntry[PART_T, MSBPartProps, SUBTYPE_PROPS_T, MSB_T],
    abc.ABC,
    tp.Generic[PART_T, TYPE_PROPS_T, SUBTYPE_PROPS_T, MSB_T, BIT_SET_T],
):
    """MSB Part instance of a FLVER, Collision (HKX), or Navmesh (NVM) model of the corresponding Part subtype, with
    an additional generic parameter for game-specific `BitSet` type.

    Shares its model data with the Blender model Mesh object (even if it's a placeholder).

    Note that FLVER-based parts do not duplicate the Dummies of their models, but can duplicate their Armatures
    depending on MSB import settings (e.g. to properly display the 'static poses' of Map Pieces and Objects).
    """

    TYPE = SoulstructType.MSB_PART
    BL_OBJ_TYPE = ObjectType.MESH  # true for all subtypes
    SOULSTRUCT_CLASS: tp.ClassVar[type[MSBPartProtocol]]
    MSB_ENTRY_SUBTYPE: tp.ClassVar[MSBPartSubtype]

    _MODEL_ADAPTER: tp.ClassVar[MSBPartModelAdapter]

    __slots__ = []
    obj: bpy.types.MeshObject

    # Only supported games currently are Demon's Souls and Dark Souls 1, which have identical MSB Part properties.
    # TODO: Probably need one more level of classes, for per-game supertype properties like these.

    TYPE_FIELDS = (
        # NOTE: `model`, `sib_path`, `translate`, `rotate`, and `scale` all handled 100% manually.
        SoulstructFieldAdapter("entity_id"),
        MSBPartGroupsAdapter("draw_groups"),
        MSBPartGroupsAdapter("display_groups"),
        SoulstructFieldAdapter("ambient_light_id"),
        SoulstructFieldAdapter("fog_id"),
        SoulstructFieldAdapter("scattered_light_id"),
        SoulstructFieldAdapter("lens_flare_id"),
        SoulstructFieldAdapter("shadow_id"),
        SoulstructFieldAdapter("dof_id"),
        SoulstructFieldAdapter("tone_map_id"),
        SoulstructFieldAdapter("point_light_id"),
        SoulstructFieldAdapter("tone_correction_id"),
        SoulstructFieldAdapter("lod_id"),
        SoulstructFieldAdapter("is_shadow_source"),
        SoulstructFieldAdapter("is_shadow_destination"),
        SoulstructFieldAdapter("is_shadow_only"),
        SoulstructFieldAdapter("draw_by_reflect_cam"),
        SoulstructFieldAdapter("draw_only_reflect_cam"),
        SoulstructFieldAdapter("use_depth_bias_float"),
        SoulstructFieldAdapter("disable_point_light_effect"),
    )

    entity_id: int
    draw_groups: BIT_SET_T
    display_groups: BIT_SET_T
    ambient_light_id: int
    fog_id: int
    scattered_light_id: int
    lens_flare_id: int
    shadow_id: int
    dof_id: int
    tone_map_id: int
    point_light_id: int
    tone_correction_id: int
    lod_id: int
    is_shadow_source: bool
    is_shadow_destination: bool
    is_shadow_only: bool
    draw_by_reflect_cam: bool
    draw_only_reflect_cam: bool
    use_depth_bias_float: bool
    disable_point_light_effect: bool

    @property
    def mesh(self) -> bpy.types.Mesh:
        return self.obj.data

    @property
    def armature(self) -> bpy.types.ArmatureObject | None:
        """Parts with FLVER models may have an Armature parent, which is useful for posing Map Pieces and for Cutscenes
        to animate individual characters, objects, etc."""
        if self._MODEL_ADAPTER.bl_model_type != SoulstructType.FLVER:
            # Blender object may still have a parent, but it is not a managed aspect of the Part.
            return None
        if self.obj.parent and self.obj.parent.type == "ARMATURE":
            # noinspection PyTypeChecker
            return self.obj.parent
        return None

    # region Manual MSB Part Properties

    @property
    def model(self) -> bpy.types.MeshObject | None:
        return self.type_properties.model

    @model.setter
    def model(self, value: bpy.types.MeshObject | None):
        self.type_properties.model = value

    def set_bl_obj_transform(self, part: PART_T):
        """Redirect transform to Part's Armature parent if present."""
        game_transform = Transform.from_msb_entry(part)
        obj = self.armature or self.obj
        obj.location = game_transform.bl_translate
        obj.rotation_euler = game_transform.bl_rotate
        obj.scale = game_transform.bl_scale

    def clear_bl_obj_transform(self):
        """Reset local transform to identity."""
        obj = self.armature or self.obj
        obj.location = Vector((0, 0, 0))
        obj.rotation_euler = Euler((0, 0, 0))
        obj.scale = Vector((1, 1, 1))

    def set_part_transform(self, part: PART_T, use_world_transform=False):
        """Get transform from Part's Armature parent if present."""
        obj = self.armature or self.obj
        bl_transform = BlenderTransform.from_bl_obj(obj, use_world_transform)
        part.translate = bl_transform.game_translate
        part.rotate = bl_transform.game_rotate_deg
        part.scale = bl_transform.game_scale

    # endregion

    @classmethod
    def new(
        cls,
        name: str,
        data: bpy.types.Mesh,
        collection: bpy.types.Collection = None,
    ) -> tp.Self:
        """Create a new instance of this MSB Part subtype with the given Mesh `data` as its model.

        `data` must be a Mesh for all MSB Part subtypes (enforced in parent method by `cls.BL_OBJ_TYPE`).
        """
        bl_part = super().new(name, data, collection)  # type: tp.Self
        bl_part.obj.MSB_PART.part_subtype = cls.MSB_ENTRY_SUBTYPE
        return bl_part

    @classmethod
    @tp.final
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: PART_T,
        name: str,
        collection: bpy.types.Collection = None,
        *,
        map_stem="",
        armature_mode=MSBPartArmatureMode.CUSTOM_ONLY,
    ) -> tp.Self:
        """Create a fully-represented MSB Part linked to a source model in Blender.

        Subclasses will override this to set additional Part-specific properties, or even a Part Armature if needed for
        those annoying old Map Pieces with "pre-posed vertices".
        """

        # MODEL and OBJECT CREATION
        if soulstruct_obj.model:
            # Blender model objects use the full file stem, not just the `MSBModel.name`.
            model_name = soulstruct_obj.model.get_model_file_stem(map_stem)
            model = cls._MODEL_ADAPTER.get_blender_model(context, model_name)  # will create placeholder if missing
        else:
            operator.warning(f"MSB Part '{name}' has no model set in the MSB.")
            model = None  # empty model reference (very unusual)
        model_mesh = model.data if model else bpy.data.meshes.new(name)
        bl_part = cls.new(name, model_mesh, collection)  # type: tp.Self
        bl_part.model = model  # NOTE: will redundantly set the Mesh data again but we can't avoid it

        # ENTRY PROPERTIES
        bl_part._read_props_from_msb_entry(operator, soulstruct_obj)

        if cls._MODEL_ADAPTER.bl_model_type == SoulstructType.FLVER:  # FLVER-based Parts only
            # Check if we should duplicate model's Armature to Part. We do this BEFORE setting the Part transform.
            PartArmatureDuplicator.maybe_duplicate_flver_model_armature(
                operator, context, armature_mode, bl_part, model
            )

        # Transform will be set to Part's Armature parent if created above.
        bl_part.set_bl_obj_transform(soulstruct_obj)

        # Any additional processing.
        bl_part._post_new_from_soulstruct_obj(operator, context, soulstruct_obj)

        return bl_part

    def duplicate_flver_model_armature(
        self, operator: LoggingOperator, context: bpy.types.Context, mode: MSBPartArmatureMode, exists_ok=True
    ):
        if self._MODEL_ADAPTER.bl_model_type != SoulstructType.FLVER:
            raise TypeError("Only FLVER-based Parts can have their model Armature duplicated.")
        if self.armature:
            if exists_ok:
                return  # fine
            raise ValueError("Part already has an Armature parent (and `exists_ok = False`).")
        if not self.model:
            raise ValueError("Part has no model to duplicate Armature from.")

        bl_transform = BlenderTransform.from_bl_obj(self.obj)
        self.clear_bl_obj_transform()

        try:
            PartArmatureDuplicator.maybe_duplicate_flver_model_armature(
                operator, context, mode, self, self.model
            )
        except Exception:
            # Un-clear transform.
            self.obj.location = bl_transform.bl_translate
            self.obj.rotation_euler = bl_transform.bl_rotate
            self.obj.scale = bl_transform.bl_scale
            raise

        # Set now-cleared Mesh object transform back to what it was.
        self.obj.location = bl_transform.bl_translate
        self.obj.rotation_euler = bl_transform.bl_rotate
        self.obj.scale = bl_transform.bl_scale

    def to_soulstruct_obj(self, operator: LoggingOperator, context: bpy.types.Context) -> PART_T:
        # Creation can be overridden (e.g. to make 'Dummy' versions of entry types).
        part = self._create_soulstruct_obj()  # type: PART_T

        # `MSBPart` `translate`, `rotate`, and `scale` are set all at once here.
        use_world_transform = context.scene.msb_export_settings.use_world_transforms
        self.set_part_transform(part, use_world_transform=use_world_transform)

        self._write_props_to_soulstruct_obj(operator, part)

        # Model is set during entry reference pass.

        return part

    def resolve_msb_entry_refs_and_map_stem(
        self, operator: LoggingOperator, msb_entry: PART_T, msb: MSB_T, map_stem: str
    ):
        """Can be overridden by Parts that require a deferred additional call after all MSB entries are created."""
        super().resolve_msb_entry_refs_and_map_stem(operator, msb_entry, msb, map_stem)
        self._MODEL_ADAPTER.set_msb_model(operator, self.model, msb_entry, msb, map_stem)
        msb_entry.set_auto_sib_path(map_stem)

    @property
    def game_name(self) -> str:
        """Part names only use text before first space OR first period."""
        return get_part_game_name(self.name)
