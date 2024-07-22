from __future__ import annotations

__all__ = [
    "BlenderMSBPart",
    "BlenderMSBRegion",
]

import abc
import typing as tp

import bpy
from io_soulstruct.exceptions import MissingPartModelError
from io_soulstruct.general.core import SoulstructSettings
from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities import new_mesh_object, Transform, LoggingOperator
from io_soulstruct.msb.base import BlenderMSBEntry
from io_soulstruct.msb.properties import MSBPartProps

if tp.TYPE_CHECKING:
    from soulstruct.base.maps.msb.parts import BaseMSBPart
    from soulstruct.base.maps.msb.regions import BaseMSBRegion
    from io_soulstruct.msb.properties import MSBPartSubtype


class BlenderMSBPart(BlenderMSBEntry, abc.ABC):
    """Mesh-only 'instance' of a FLVER model of the corresponding MSB part subtype (Map Piece, Character, etc.).

    FLVER model Armatures and Dummies are NOT instantiated for FLVER parts -- only Meshes.
    """

    PART_SUBTYPE: tp.ClassVar[MSBPartSubtype]

    def set_properties(self, operator: LoggingOperator, part: BaseMSBPart):
        self.obj.soulstruct_type = SoulstructType.MSB_PART

        props = self.obj.msb_part_props
        props.part_subtype = self.PART_SUBTYPE

        for groups in ("draw_groups", "display_groups"):
            group_props = [getattr(props, f"{groups}_{i}") for i in range(4)]
            for i in getattr(part, groups):
                if 0 <= i < 32:
                    group_props[0][i] = True
                elif 32 <= i < 64:
                    group_props[1][i - 32] = True
                elif 64 <= i < 96:
                    group_props[2][i - 64] = True
                elif 96 <= i < 128:
                    group_props[3][i - 96] = True

        for prop_name in MSBPartProps.__annotations__:
            if (
                prop_name.startswith("draw_groups_")
                or prop_name.startswith("display_groups_")
                or prop_name == "part_subtype"
            ):
                continue  # handled above

            # Property names match real `MSBPart` fields.
            setattr(props, prop_name, getattr(part, prop_name))

    @property
    def part_props(self) -> MSBPartProps:
        return self.obj.msb_part_props

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
    def new_from_part(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        settings: SoulstructSettings,
        map_stem: str,
        part: BaseMSBPart,
        collection: bpy.types.Collection = None,
    ):
        """Create a fully-represented MSB Part linked to a source model in Blender.

        Works for all subclasses, thanks to abstract methods.
        """
        model_name = part.model.get_model_file_stem(map_stem)
        model = cls.find_or_import_model(operator, context, settings, map_stem, model_name)
        bl_part = cls.new_from_model_mesh(model, part.name, collection)
        bl_part.set_transform(part)
        bl_part.set_properties(operator, part)  # no subtype properties
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


class BlenderMSBRegion(BlenderMSBEntry):
    """Not abstract in DS1."""

    def set_transform(self, region: BaseMSBRegion):
        game_transform = Transform.from_msb_entry(region)
        self.obj.location = game_transform.bl_translate
        self.obj.rotation_euler = game_transform.bl_rotate
        self.obj.scale = game_transform.bl_scale
