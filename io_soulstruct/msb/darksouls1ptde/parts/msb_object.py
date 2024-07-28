from __future__ import annotations

__all__ = [
    "BlenderMSBObject",
]

import traceback
import typing as tp

import bpy
from io_soulstruct.exceptions import FLVERImportError
from io_soulstruct.flver.models import BlenderFLVER
from io_soulstruct.flver.image.image_import_manager import ImageImportManager
from io_soulstruct.flver.utilities import get_flvers_from_binder
from io_soulstruct.msb.properties import MSBPartSubtype, MSBObjectProps
from io_soulstruct.msb.utilities import find_flver_model
from io_soulstruct.types import *
from io_soulstruct.utilities import *
from soulstruct.containers import Binder
from soulstruct.darksouls1ptde.maps.parts import MSBObject, MSBDummyObject
from .msb_part import BlenderMSBPart

if tp.TYPE_CHECKING:
    from soulstruct.darksouls1ptde.maps.msb import MSB


class BlenderMSBObject(BlenderMSBPart[MSBObject, MSBObjectProps]):
    """Also used for 'Dummy' (Unused) MSB Objects."""

    OBJ_DATA_TYPE = SoulstructDataType.MESH
    SOULSTRUCT_CLASS = MSBObject
    PART_SUBTYPE = MSBPartSubtype.OBJECT
    MODEL_SUBTYPES = ["object_models"]

    __slots__ = []

    AUTO_OBJECT_PROPS = [
        "break_term",
        "net_sync_type",
        "default_animation",
        "unk_x0e_x10",
        "unk_x10_x14",
    ]

    break_term: int
    net_sync_type: int
    default_animation: int
    unk_x0e_x10: int
    unk_x10_x14: int

    @property
    def armature(self) -> bpy.types.ArmatureObject | None:
        """Detect parent Armature of wrapped Mesh object. Rarely present for Parts."""
        if self.obj.parent and self.obj.parent.type == "ARMATURE":
            # noinspection PyTypeChecker
            return self.obj.parent
        return None

    @property
    def draw_parent(self) -> bpy.types.Object | None:
        return self.subtype_properties.draw_parent

    @draw_parent.setter
    def draw_parent(self, value: bpy.types.Object | None):
        self.subtype_properties.draw_parent = value

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MSBObject,
        name: str,
        collection: bpy.types.Collection = None,
        map_stem="",
    ) -> tp.Self:
        bl_obj = super().new_from_soulstruct_obj(
            operator, context, soulstruct_obj, name, collection, map_stem
        )  # type: tp.Self

        bl_obj.draw_parent = cls.entry_ref_to_bl_obj(
            operator,
            soulstruct_obj,
            "draw_parent",
            soulstruct_obj.draw_parent,
            SoulstructType.MSB_PART,
            missing_collection_name=f"{map_stem} Missing MSB References".lstrip(),
        )

        for name in cls.AUTO_OBJECT_PROPS:
            setattr(bl_obj, name, getattr(soulstruct_obj, name))

        bl_obj.subtype_properties.is_dummy = isinstance(soulstruct_obj, MSBDummyObject)

        return bl_obj

    def create_soulstruct_obj(self):
        if self.subtype_properties.is_dummy:
            return MSBDummyObject(name=self.tight_name)
        return MSBObject(name=self.tight_name)

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        map_stem="",
        msb: MSB = None,
    ) -> MSBObject:
        msb_object = super().to_soulstruct_obj(operator, context, map_stem, msb)  # type: MSBObject

        msb_object.draw_parent = self.bl_obj_to_entry_ref(msb, "draw_parent", self.draw_parent, msb_object)

        for name in self.AUTO_OBJECT_PROPS:
            setattr(msb_object, name, getattr(self, name))

        return msb_object

    @classmethod
    def find_model_mesh(cls, model_name: str, map_stem="") -> bpy.types.MeshObject:
        return find_flver_model(model_name).mesh

    @classmethod
    def import_model_mesh(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        model_name: str,
        map_stem="",  # not used
    ) -> bpy.types.MeshObject:
        """Import the model of the given name into a collection in the current scene."""
        settings = operator.settings(context)

        import_settings = context.scene.flver_import_settings
        objbnd_path = settings.get_import_file_path(f"obj/{model_name}.objbnd")

        operator.info(f"Importing object FLVER from: {objbnd_path.name}")

        texture_import_manager = ImageImportManager(operator, context) if import_settings.import_textures else None

        objbnd = Binder.from_path(objbnd_path)
        binder_flvers = get_flvers_from_binder(objbnd, objbnd_path, allow_multiple=True)
        if texture_import_manager:
            texture_import_manager.find_flver_textures(objbnd_path, objbnd)
        flver = binder_flvers[0]  # TODO: ignoring secondary Object FLVERs for now

        try:
            bl_flver = BlenderFLVER.new_from_soulstruct_obj(
                operator,
                context,
                flver,
                model_name,
                texture_import_manager=texture_import_manager,
                collection=get_collection("Object Models", context.scene.collection),
            )
        except Exception as ex:
            traceback.print_exc()  # for inspection in Blender console
            raise FLVERImportError(f"Cannot import FLVER from OBJBND: {objbnd_path.name}. Error: {ex}")

        # Only need to return the Mesh.
        return bl_flver.mesh


BlenderMSBObject.add_auto_subtype_props(*BlenderMSBObject.AUTO_OBJECT_PROPS)
