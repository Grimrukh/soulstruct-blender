from __future__ import annotations

__all__ = [
    "BaseBlenderMSBPart",
]

import abc
import typing as tp

import bpy

from soulstruct.base.maps.msb.parts import BaseMSBPart
from soulstruct.base.maps.msb.utils import BitSet

from io_soulstruct.exceptions import SoulstructTypeError
from io_soulstruct.flver.models.types import BlenderFLVER
from io_soulstruct.msb.properties import BlenderMSBPartSubtype, MSBPartArmatureMode, MSBPartProps
from io_soulstruct.msb.types.adapters import *
from io_soulstruct.utilities import *

from .entry import BaseBlenderMSBEntry, SUBTYPE_PROPS_T, MSB_T
from .part_armature_duplicator import PartArmatureDuplicator

PART_T = tp.TypeVar("PART_T", bound=BaseMSBPart)
BIT_SET_T = tp.TypeVar("BIT_SET_T", bound=BitSet)


class BaseBlenderMSBPart(
    BaseBlenderMSBEntry[PART_T, MSBPartProps, SUBTYPE_PROPS_T, MSB_T],
    abc.ABC,
    tp.Generic[PART_T, SUBTYPE_PROPS_T, MSB_T, BIT_SET_T],  # added `BitSet` generic
):
    """MSB Part instance of a FLVER, Collision (HKX), or Navmesh (NVM) model of the corresponding Part subtype, with
    an additional generic parameter for game-specific `BitSet` type.

    Shares its model data with the Blender model Mesh object (even if it's a placeholder).

    Note that FLVER-based parts do not duplicate the Dummies of their models, but can duplicate their Armatures
    depending on MSB import settings (e.g. to properly display the 'static poses' of Map Pieces and Objects).
    """

    TYPE = SoulstructType.MSB_PART
    BL_OBJ_TYPE = ObjectType.MESH  # true for all subtypes
    SOULSTRUCT_CLASS: tp.ClassVar[type[BaseMSBPart]]
    MSB_ENTRY_SUBTYPE: tp.ClassVar[BlenderMSBPartSubtype]

    _MODEL_ADAPTER: tp.ClassVar[MSBPartModelAdapter]

    __slots__ = []
    obj: bpy.types.MeshObject

    TYPE_FIELDS = (
        # NOTE: `model` and `sib_path` are handled 100% manually.
        MSBTransformFieldAdapter("translate|rotate|scale"),  # may export world transform
        FieldAdapter("entity_id"),
        # NOTE: `draw_groups` and `display_groups` are used by all Parts, but the type of `BitSet` is game-specific.
    )

    entity_id: int
    draw_groups: BIT_SET_T
    display_groups: BIT_SET_T

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

    @property
    def transform_obj(self):
        """Part transform is stored on parent Armature if present."""
        return self.armature or self.obj

    # region Manual MSB Part Properties

    @property
    def model(self) -> bpy.types.MeshObject | None:
        return self.type_properties.model

    @model.setter
    def model(self, value: bpy.types.MeshObject | None):
        self.type_properties.model = value

    @property
    def location(self):
        return

    @location.setter
    def location(self, value):
        pass

    # endregion

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
        copy_pose=False,
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

        if cls._MODEL_ADAPTER.bl_model_type == SoulstructType.FLVER:  # FLVER-based Parts only
            # Check if we should duplicate model's Armature to Part. We do this BEFORE setting the Part transform.
            PartArmatureDuplicator.maybe_duplicate_flver_model_armature(
                operator, context, armature_mode, bl_part, model
            )

        # Transform will be set to Part's Armature parent if created above.
        bl_part._read_props_from_soulstruct_obj(operator, context, soulstruct_obj)

        # Any additional processing.
        bl_part._post_new_from_soulstruct_obj(operator, context, soulstruct_obj)

        return bl_part

    @classmethod
    def get_msb_subcollection(cls, msb_collection: bpy.types.Collection, msb_stem: str) -> bpy.types.Collection:
        return get_or_create_collection(
            msb_collection, f"{msb_stem} Parts", f"{msb_stem} {cls.MSB_ENTRY_SUBTYPE.get_nice_name()} Parts"
        )

    def duplicate_flver_model_armature(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        mode: MSBPartArmatureMode,
        exists_ok=True,
        copy_pose=True,  # default is that this isn't batched
    ):
        if self._MODEL_ADAPTER.bl_model_type != SoulstructType.FLVER:
            raise TypeError("Only FLVER-based Parts can have their model Armature duplicated.")
        if self.armature:
            if exists_ok:
                return  # fine
            raise ValueError("Part already has an Armature parent (and `exists_ok = False`).")
        if not self.model:
            raise ValueError("Part has no model to duplicate Armature from.")

        # If Armature is created, this will move the current local transform of the Mesh to the Armature.
        created = PartArmatureDuplicator.maybe_duplicate_flver_model_armature(operator, context, mode, self, self.model)

        if copy_pose and created:
            context.view_layer.update()  # SLOW
            self.copy_model_armature_pose()

    def copy_model_armature_pose(self):
        if self._MODEL_ADAPTER.bl_model_type != SoulstructType.FLVER:
            raise TypeError("Only FLVER-based Parts can have their model Armature pose copied.")
        if not self.armature:
            raise ValueError("Part does not have an Armature parent to copy pose from.")
        if not self.model:
            raise ValueError("Part has no model to copy Armature pose from.")
        bl_flver = BlenderFLVER(self.model)
        if not bl_flver.armature:
            return  # harmless case
        copy_armature_pose(bl_flver.armature, self.armature, ignore_bone_names={"<PART_ROOT>"})

    def resolve_msb_entry_refs_and_map_stem(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        msb_entry: PART_T,
        msb: MSB_T,
        map_stem: str,
    ):
        """Can be overridden by Parts that require a deferred additional call after all MSB entries are created."""
        super().resolve_msb_entry_refs_and_map_stem(operator, context, msb_entry, msb, map_stem)

        self._MODEL_ADAPTER.set_msb_model(operator, self.model, msb_entry, msb, map_stem)
        msb_entry.set_auto_sib_path(map_stem)

    @property
    def game_name(self) -> str:
        """Part names only use text before first space OR first period."""
        return get_part_game_name(self.name)

    @classmethod
    def from_armature_or_mesh(cls, obj: bpy.types.Object) -> tp.Self:
        """MSB Parts can be parsed from a Mesh obj or its optional Armature parent."""
        if not obj:
            raise SoulstructTypeError("No Object given.")
        _, mesh = cls.parse_msb_part_obj(obj)
        return cls(mesh)

    @classmethod
    def is_obj_type(cls, obj: bpy.types.Object) -> bool:
        """For MSB Part, Blender `obj` could be Mesh or Armature."""
        try:
            cls.from_armature_or_mesh(obj)
        except SoulstructTypeError:
            return False
        return True

    @staticmethod
    def parse_msb_part_obj(obj: bpy.types.Object) -> tuple[bpy.types.ArmatureObject | None, bpy.types.MeshObject]:
        """Parse a Blender object into an MSB Part Mesh and (optional) Armature object."""
        if obj.type == "MESH" and obj.soulstruct_type == SoulstructType.MSB_PART:
            mesh = obj
            armature = mesh.parent if mesh.parent is not None and mesh.parent.type == "ARMATURE" else None
        elif obj.type == "ARMATURE":
            armature = obj
            mesh_children = [child for child in armature.children if child.type == "MESH"]
            if not mesh_children or mesh_children[0].soulstruct_type != SoulstructType.MSB_PART:
                raise SoulstructTypeError(
                    f"Armature '{armature.name}' has no MSB Part Mesh child. Please create it, even if empty, and set "
                    f"its Soulstruct object type to MSB Part using the General Settings panel."
                )
            mesh = mesh_children[0]
        else:
            raise SoulstructTypeError(
                f"Given object '{obj.name}' is not an MSB Part Mesh or Armature parent of such. "
                f"Cannot parse as MSB Part."
            )

        # noinspection PyTypeChecker
        return armature, mesh
