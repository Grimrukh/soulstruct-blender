from __future__ import annotations

__all__ = [
    "BlenderMSBPart",
]

import abc
import typing as tp

import bpy
from io_soulstruct.exceptions import *
from io_soulstruct.flver.models import BlenderFLVER
from io_soulstruct.msb.properties import MSBPartSubtype, MSBPartProps
from io_soulstruct.types import *
from io_soulstruct.utilities import *
from soulstruct.base.maps.msb.utils import GroupBitSet128
from soulstruct.darksouls1ptde.maps.msb import MSBPart, MSBModel

if tp.TYPE_CHECKING:
    from soulstruct.base.maps.msb import MSBEntry
    from soulstruct.darksouls1ptde.maps.msb import MSB


PART_T = tp.TypeVar("PART_T", bound=MSBPart)
SUBTYPE_PROPS_T = tp.TypeVar("SUBTYPE_PROPS_T", bound=bpy.types.PropertyGroup)


class BlenderMSBPart(SoulstructObject[MSBPart, MSBPartProps], tp.Generic[PART_T, SUBTYPE_PROPS_T]):
    """Mesh-only MSB Part instance of a FLVER model of the corresponding Part subtype (Map Piece, Character, etc.).

    FLVER model Armatures and Dummies are NOT instantiated for FLVER parts -- strictly Meshes (or Empties for Player
    Starts).
    """

    TYPE = SoulstructType.MSB_PART
    # OBJ_DATA_TYPE is subtype-dependent.
    SOULSTRUCT_CLASS: tp.ClassVar[type[MSBPart]]
    SOULSTRUCT_MODEL_CLASS: tp.ClassVar[type[MSBModel]]
    EXPORT_TIGHT_NAME = True  # for MSB parts, we always use tight names
    PART_SUBTYPE: tp.ClassVar[MSBPartSubtype]
    MODEL_SUBTYPES: tp.ClassVar[list[str]]  # for `MSB` model search on export

    __slots__ = []
    obj: bpy.types.MeshObject
    # All Parts are Meshes.
    data: bpy.types.Mesh

    AUTO_PART_PROPS: tp.ClassVar[list[str]] = [
        "entity_id",
        "ambient_light_id",
        "fog_id",
        "scattered_light_id",
        "lens_flare_id",
        "shadow_id",
        "dof_id",
        "tone_map_id",
        "point_light_id",
        "tone_correction_id",
        "lod_id",
        "is_shadow_source",
        "is_shadow_destination",
        "is_shadow_only",
        "draw_by_reflect_cam",
        "draw_only_reflect_cam",
        "use_depth_bias_float",
        "disable_point_light_effect",
    ]

    entity_id: int
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
    def armature(self) -> bpy.types.ArmatureObject | None:
        """Detect parent Armature of wrapped Mesh object. Rarely present for Parts. Must be overridden to enable."""
        raise TypeError(f"MSB {self.PART_SUBTYPE} parts cannot have Armatures.")

    @property
    def subtype_properties(self) -> SUBTYPE_PROPS_T:
        return getattr(self.obj, self.PART_SUBTYPE)

    @property
    def model(self) -> bpy.types.MeshObject | None:
        return self.type_properties.model

    @model.setter
    def model(self, value: bpy.types.MeshObject | None):
        self.type_properties.model = value

    @staticmethod
    def _get_groups_bit_set(props: list[bpy.props.BoolVectorProperty]):
        groups = GroupBitSet128.all_off()
        for i in range(4):
            for j in range(32):
                if props[i][j]:
                    groups.add(i * 32 + j)
        return groups

    @staticmethod
    def _set_groups_bit_set(props: list[bpy.props.BoolVectorProperty], enabled_bits: set[int]):
        for i in range(4):
            for j in range(32):
                props[i][j] = (i * 32 + j) in enabled_bits

    @property
    def draw_groups(self) -> GroupBitSet128:
        return self._get_groups_bit_set(self.type_properties.get_draw_groups_props_128())

    @draw_groups.setter
    def draw_groups(self, value: set[int] | GroupBitSet128):
        if isinstance(value, GroupBitSet128):
            value = value.enabled_bits
        self._set_groups_bit_set(self.type_properties.get_draw_groups_props_128(), value)

    @property
    def display_groups(self) -> GroupBitSet128:
        return self._get_groups_bit_set(self.type_properties.get_display_groups_props_128())

    @display_groups.setter
    def display_groups(self, value: set[int] | GroupBitSet128):
        if isinstance(value, GroupBitSet128):
            value = value.enabled_bits
        self._set_groups_bit_set(self.type_properties.get_display_groups_props_128(), value)

    def set_bl_obj_transform(self, part: MSBPart):
        game_transform = Transform.from_msb_entry(part)
        self.obj.location = game_transform.bl_translate
        self.obj.rotation_euler = game_transform.bl_rotate
        self.obj.scale = game_transform.bl_scale

    def set_part_transform(self, part: MSBPart):
        bl_transform = BlenderTransform.from_bl_obj(self.obj)
        part.translate = bl_transform.game_translate
        part.rotate = bl_transform.game_rotate_deg
        part.scale = bl_transform.game_scale

    @staticmethod
    def entry_ref_to_bl_obj(
        operator: LoggingOperator,
        part: MSBPart,
        prop_name: str,
        ref_entry: MSBEntry | None,
        ref_soulstruct_type: SoulstructType,
        missing_collection_name="Missing MSB References",
    ) -> bpy.types.Object | None:
        if not ref_entry:
            return None

        was_missing, pointer_obj = find_obj_or_create_empty(
            ref_entry.name,
            find_stem=True,
            soulstruct_type=ref_soulstruct_type,
            missing_collection_name=missing_collection_name,
        )
        if was_missing:
            operator.warning(
                f"Referenced MSB entry '{ref_entry.name}' in field '{prop_name}' of MSB part '{part.name}' not "
                f"found in Blender data. Creating empty reference."
            )
        return pointer_obj

    @staticmethod
    def bl_obj_to_entry_ref(
        msb: MSB,
        prop_name: str,
        bl_obj: bpy.types.Object | None,
        part: MSBPart,
        entry_subtype: str = None
    ) -> MSBEntry | None:

        if not bl_obj:
            return None  # leave part field as `None`
        if entry_subtype:
            subtypes = (entry_subtype,)
        else:
            subtypes = ()

        try:
            if bl_obj.soulstruct_type == SoulstructType.MSB_PART:
                msb_entry = msb.find_part_name(get_bl_obj_tight_name(bl_obj), subtypes=subtypes)
            elif bl_obj.soulstruct_type == SoulstructType.MSB_REGION:
                msb_entry = msb.find_region_name(bl_obj.name, subtypes=subtypes)  # full name
            elif bl_obj.soulstruct_type == SoulstructType.MSB_EVENT:
                msb_entry = msb.find_event_name(bl_obj.name, subtypes=subtypes)  # full name
            else:
                raise SoulstructTypeError(f"Blender object '{bl_obj.name}' is not an MSB Part or Region.")
            return msb_entry
        except KeyError:
            raise MissingMSBEntryError(
                f"MSB entry '{bl_obj.name}' referenced in field '{prop_name}' of part '{part.name}' "
                f"not found in MSB."
            )

    @classmethod
    def model_ref_to_bl_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        part: MSBPart,
        map_stem: str,
    ) -> bpy.types.MeshObject | None:
        """Unlike resolving entry refs as new empty objects if missing, we try to import models."""

        if not part.model:
            operator.warning(f"MSB Part '{part.name}' has no model set in the MSB.")
            return None

        model_name = part.model.get_model_file_stem(map_stem)
        return cls.find_or_import_model_mesh(operator, context, model_name, map_stem)

    def bl_obj_to_model_ref(
        self,
        operator: LoggingOperator,
        msb: MSB,
        part: MSBPart,
    ) -> MSBEntry | None:
        """Find model in MSB with matching name to this object's `model` reference."""

        if not self.model:
            operator.warning(f"MSB Part '{part.name}' has no model set in Blender.")
            return None  # leave part field as `None`

        # We use the `MSBModel` subclass to determine what name to look for.
        msb_model_name = self.SOULSTRUCT_MODEL_CLASS.model_file_stem_to_model_name(get_bl_obj_tight_name(self.model))
        try:
            return msb.find_model_name(msb_model_name, subtypes=self.MODEL_SUBTYPES)
        except KeyError:
            raise MissingPartModelError(
                f"Model '{msb_model_name}' (from Blender model '{self.model.name}') not found in MSB model lists."
            )

    @classmethod
    def batch_import_models(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        parts: list[PART_T],
        map_stem: str,
    ):
        """Import all models for a batch of MSB Parts, as needed, in parallel as much as possible.

        Not available by defailt.
        """
        raise BatchOperationUnsupportedError(f"Cannot batch import MSB Part subtype: {cls.PART_SUBTYPE}")

    @classmethod
    def new(
        cls,
        name: str,
        data: bpy.types.Mesh | None,
        collection: bpy.types.Collection = None,
    ) -> tp.Self:
        bl_part = super().new(name, data, collection)  # type: tp.Self
        bl_part.obj.MSB_PART.part_subtype = cls.PART_SUBTYPE
        return bl_part

    @classmethod
    def find_or_import_model_mesh(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        model_name: str,
        map_stem: str,  # not required by all subtypes
    ) -> bpy.types.MeshObject:
        """Find or create actual Blender model mesh. Not necessarily a FLVER mesh!"""
        try:
            return cls.find_model_mesh(model_name, map_stem)
        except MissingPartModelError:
            model = cls.import_model_mesh(operator, context, model_name, map_stem)
            return model

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: PART_T,
        name: str,
        collection: bpy.types.Collection = None,
        map_stem="",
    ) -> tp.Self:
        """Create a fully-represented MSB Part linked to a source model in Blender.

        Subclasses will override this to set additional Part-specific properties, or even a Part Armature if needed for
        those annoying old Map Pieces with "pre-posed vertices".
        """
        model = cls.model_ref_to_bl_obj(operator, context, soulstruct_obj, map_stem)
        model_mesh = model.data if model else bpy.data.meshes.new(name)
        bl_part = cls.new(name, model_mesh, collection)  # type: tp.Self
        bl_part.set_bl_obj_transform(soulstruct_obj)
        bl_part.model = model
        bl_part.draw_groups = soulstruct_obj.draw_groups
        bl_part.display_groups = soulstruct_obj.display_groups
        for name in cls.AUTO_PART_PROPS:
            setattr(bl_part, name, getattr(soulstruct_obj, name))

        return bl_part

    def duplicate_flver_model_armature(self, context: bpy.types.Context):
        """Duplicate FLVER model's Armature parent to being the parent of this part Mesh.

        Only works for FLVER-based Parts, obviously (Map Pieces, Objects, Assets, Characters). Those classes will also
        expose an `armature` property to retrieve the Mesh parent.

        If the model parent does not have an Armature, the implicit default one will be created for the Part, though
        this is unlikely to be useful for such models (i.e., static Map Pieces).
        """
        if not self.model:
            raise ValueError("Cannot duplicate model armature for MSB Part without a model.")
        if not self.model.soulstruct_type == SoulstructType.FLVER:
            raise TypeError(f"MSB {self.PART_SUBTYPE} parts do not have FLVER model armatures to duplicate.")
        bl_flver = BlenderFLVER(self.model)
        if not bl_flver.armature:
            # This FLVER model doesn't have an Armature, implying the FLVER has only one default bone. We create that
            # for this Part, without assigning it to the FLVER.
            BlenderFLVER.create_default_armature_parent(context, self.tight_name, self.obj)
        else:
            # Duplicate model's Armature. This handles parenting, rigging, etc. We only copy pose for Map Pieces.
            bl_flver.duplicate_armature(context, self.obj, copy_pose=self.PART_SUBTYPE == MSBPartSubtype.MAP_PIECE)
            # Rename new modifier for clarity.
            self.obj.modifiers["FLVER Armature"].name = "Part Armature"

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        map_stem="",
        msb: MSB = None,
    ) -> PART_T:
        if msb is None:
            raise ValueError("MSB must be provided to convert Blender MSB Part to `MSBPart`, to resolve references.")

        # Creation can be overridden (e.g. to make 'Dummy' versions of entry types).
        part = self.create_soulstruct_obj(name=self.tight_name if self.EXPORT_TIGHT_NAME else self.name)  # type: PART_T

        part.set_auto_sib_path(map_stem)
        self.set_part_transform(part)
        part.model = self.bl_obj_to_model_ref(operator, msb, part)
        part.draw_groups = self.draw_groups
        part.display_groups = self.display_groups
        for name in self.AUTO_PART_PROPS:
            setattr(part, name, getattr(self, name))

        return part

    @classmethod
    @abc.abstractmethod
    def find_model_mesh(
        cls,
        model_name: str,
        map_stem: str,  # not required by all subtypes
    ) -> bpy.types.MeshObject:
        """Find the given model in the current scene. Used on Blender Part creation to avoid re-importing models.

        Should raise `MissingPartModelError` if not found.
        """

    @classmethod
    @abc.abstractmethod
    def import_model_mesh(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        model_name: str,
        map_stem: str,  # not required by all subtypes
    ) -> bpy.types.MeshObject:
        """Use other Soulstruct for Blender submodules to import model for this MSB Part."""

    @classmethod
    def add_auto_subtype_props(cls, *names):
        for prop_name in names:
            # `prop_name` must be baked in to each closure!
            setattr(
                cls, prop_name, property(
                    lambda self, pn=prop_name: getattr(self.subtype_properties, pn),
                    lambda self, value, pn=prop_name: setattr(self.subtype_properties, pn, value),
                )
            )


BlenderMSBPart.add_auto_type_props(*BlenderMSBPart.AUTO_PART_PROPS)
# Subtype props added by subclasses.
