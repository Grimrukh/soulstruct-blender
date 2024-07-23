from __future__ import annotations

__all__ = [
    "BlenderMSBPart",
]

import abc
import typing as tp

import bpy
from io_soulstruct.exceptions import MissingPartModelError, MissingMSBEntryError, SoulstructTypeError
from io_soulstruct.general.core import SoulstructSettings
from io_soulstruct.msb.base import BlenderMSBEntry, ENTRY_TYPE
from io_soulstruct.msb.properties import MSBPartSubtype, MSBPartProps
from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities import *

if tp.TYPE_CHECKING:
    from soulstruct.base.maps.msb.utils import GroupBitSet
    from soulstruct.darksouls1ptde.maps.msb import MSB, MSBPart


class BlenderMSBPart(BlenderMSBEntry[MSBPart], abc.ABC):
    """Mesh-only 'instance' of a FLVER model of the corresponding MSB part subtype (Map Piece, Character, etc.).

    FLVER model Armatures and Dummies are NOT instantiated for FLVER parts -- only Meshes.
    """

    SOULSTRUCT_CLASS: tp.ClassVar[type[MSBPart]]
    EXPORT_TIGHT_NAME = True  # for MSB parts, we always use tight names
    PART_SUBTYPE: tp.ClassVar[MSBPartSubtype]
    MODEL_SUBTYPES: tp.ClassVar[list[str]]  # for `MSB` model search on export

    @property
    def part_props(self) -> MSBPartProps:
        return self.obj.msb_part_props

    @property
    def model(self) -> bpy.types.MeshObject | None:
        return self.obj.msb_part_props.model

    @model.setter
    def model(self, value: bpy.types.MeshObject | None):
        self.obj.msb_part_props.model = value

    def assert_obj_type(self):
        super().assert_obj_type()
        part_subtype = self.part_props.part_subtype
        if part_subtype != self.PART_SUBTYPE:
            raise SoulstructTypeError(
                f"Blender object '{self.name}' has MSB Part subtype '{part_subtype}', not '{self.PART_SUBTYPE}'."
            )

    def set_obj_transform(self, part: MSBPart):
        game_transform = Transform.from_msb_entry(part)
        self.obj.location = game_transform.bl_translate
        self.obj.rotation_euler = game_transform.bl_rotate
        self.obj.scale = game_transform.bl_scale

    def set_part_transform(self, part: MSBPart):
        bl_transform = BlenderTransform.from_bl_obj(self.obj)
        part.translate = bl_transform.game_translate
        part.rotate = bl_transform.game_rotate_deg
        part.scale = bl_transform.game_scale

    def set_obj_groups(self, part: MSBPart, groups_name: str, group_count=4, group_size=32):
        """Assign each enabled bit group in `part.{groups_name}` to the corresponding group in the Blender object."""
        part_groups = getattr(part, groups_name)  # type: GroupBitSet
        group_props = [getattr(self.obj.msb_part_props, f"{groups_name}_{j}") for j in range(group_count)]
        for i in part_groups.enabled_bits:
            for j in range(group_count):
                if i < group_size * (j + 1):
                    group_props[j][i - group_size * j] = True
                    break

    def set_part_groups(self, part: MSBPart, groups_name: str, group_count=4, group_size=32):
        """Assign each enabled bit group in the Blender object to the corresponding group in `part.{groups_name}`."""
        part_groups = getattr(part, groups_name)  # type: GroupBitSet
        group_props = [getattr(self.obj.msb_part_props, f"{groups_name}_{j}") for j in range(group_count)]
        for j in range(group_count):
            for i in range(group_size):
                if group_props[j][i]:
                    part_groups.add(group_size * j + i)

    @staticmethod
    def set_obj_entry_reference(
        operator: LoggingOperator,
        props: bpy.types.PropertyGroup,
        prop_name: str,
        part: MSBPart,
        soulstruct_type: SoulstructType,
    ):
        if msb_entry := getattr(part, prop_name):
            was_missing, pointer_obj = find_obj_or_create_empty(
                msb_entry.name,
                find_stem=True,
                soulstruct_type=soulstruct_type,
            )
            setattr(props, prop_name, pointer_obj)
            if was_missing:
                operator.warning(
                    f"Referenced MSB entry '{msb_entry.name}' in field '{prop_name}' of MSB part '{part.name}' not "
                    f"found in scene. Creating empty object with that name and Soulstruct type in Scene Collection to "
                    f"reference in Blender."
                )

    @staticmethod
    def set_part_entry_reference(
        pointer_obj: bpy.types.Object | None,
        part: MSBPart,
        prop_name: str,
        msb: MSB,
    ):
        if not pointer_obj:
            return  # leave part field as `None`
        try:
            if pointer_obj.soulstruct_type == SoulstructType.MSB_PART:
                msb_entry = msb.find_part_name(get_bl_obj_tight_name(pointer_obj))
            elif pointer_obj.soulstruct_type == SoulstructType.MSB_REGION:
                msb_entry = msb.find_region_name(get_bl_obj_tight_name(pointer_obj))
            else:
                raise SoulstructTypeError(f"Blender object '{pointer_obj.name}' is not an MSB Part or Region.")
            setattr(part, prop_name, msb_entry)
        except KeyError:
            raise MissingMSBEntryError(
                f"MSB entry '{pointer_obj.name}' referenced in field '{prop_name}' of part '{part.name}' "
                f"not found in MSB."
            )

    def set_obj_properties(self, operator: LoggingOperator, part: MSBPart):
        super().set_obj_properties(operator, part)
        props = self.obj.msb_part_props
        props.part_subtype = self.PART_SUBTYPE

        # NOTE: `model` already set.

        self.set_obj_groups(part, "draw_groups")
        self.set_obj_groups(part, "display_groups")

        self.set_obj_generic_props(
            part, props, skip_prefixes=("draw_groups_", "display_groups_"), skip_names=("part_subtype",)
        )

    def set_entry_properties(self, operator: LoggingOperator, entry: MSBPart, msb: MSB):
        """Set base `MSBPart` fields on `part` from Blender object properties.

        `msb` is required to resolve internal MSB entry references.
        """
        super().set_entry_properties(operator, entry, msb)

        props = self.part_props

        # Find MSB model.
        if not props.model:
            raise MissingPartModelError(f"Blender MSB Part '{self.name}' has no model set.")
        model_name = props.model.name
        try:
            entry.model = msb.find_model_name(model_name, subtypes=self.MODEL_SUBTYPES)
        except KeyError:
            raise MissingPartModelError(f"Model '{model_name}' not found in MSB model lists.")

        self.set_part_groups(entry, "draw_groups")
        self.set_part_groups(entry, "display_groups")

        self.set_entry_generic_props(
            props, entry, skip_prefixes=("draw_groups_", "display_groups_"), skip_names=("part_subtype",)
        )

    @classmethod
    def find_or_import_model(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        settings: SoulstructSettings,
        model_name: str,
        map_stem: str,  # not required by all subtypes
    ) -> bpy.types.MeshObject:
        """Find or create actual Blender collision model mesh."""
        try:
            return cls.find_model(model_name, map_stem)
        except MissingPartModelError:
            model = cls.import_model(operator, context, settings, map_stem, model_name)
            return model

    @classmethod
    @abc.abstractmethod
    def find_model(
        cls,
        model_name: str,
        map_stem: str,  # not required by all subtypes
    ):
        """Find the given model in the current scene. Should raise `MissingPartModelError` if not found."""

    @classmethod
    @abc.abstractmethod
    def import_model(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        settings: SoulstructSettings,
        model_name: str,
        map_stem: str,  # not required by all subtypes
    ):
        """Use other Soulstruct for Blender submodules to import model for this MSB Part."""

    @classmethod
    def new_from_entry(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        settings: SoulstructSettings,
        map_stem: str,
        entry: MSBPart,
        collection: bpy.types.Collection = None,
    ):
        """Create a fully-represented MSB Part linked to a source model in Blender.

        Works for all subclasses, thanks to abstract methods.
        """
        model_name = entry.model.get_model_file_stem(map_stem)
        model = cls.find_or_import_model(operator, context, settings, map_stem, model_name)
        bl_part = cls.new_from_model_mesh(model, entry.name, collection)
        bl_part.set_obj_transform(entry)
        bl_part.set_obj_properties(operator, entry)  # no subtype properties
        return bl_part

    @classmethod
    def new_from_model_mesh(
        cls,
        model_mesh_obj: bpy.types.MeshObject,
        part_name: str,
        collection: bpy.types.Collection = None,
    ) -> BlenderMSBPart:
        """Create a new Mesh MSB Part object that uses the given Mesh as its model (not necessarily `BlenderFLVER`)."""

        # noinspection PyTypeChecker
        part_obj = new_mesh_object(part_name, model_mesh_obj.data)
        part_obj.soulstruct_type = SoulstructType.MSB_PART
        (collection or bpy.context.scene.collection).objects.link(part_obj)

        part_obj.msb_part_props.model = model_mesh_obj
        # All other Part properties stay as default.

        return cls(part_obj)

    def to_entry(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        settings: SoulstructSettings,
        map_stem: str,
        msb: MSB,
    ) -> ENTRY_TYPE:
        entry = super().to_entry(operator, context, settings, map_stem, msb)
        entry.set_auto_sib_path(map_stem)
        self.set_part_transform(entry)
        return entry
