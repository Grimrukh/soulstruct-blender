from __future__ import annotations

__all__ = [
    "BlenderMSBObject",
]

import traceback
import typing as tp

import bpy
from io_soulstruct.exceptions import FLVERImportError, MissingPartModelError
from io_soulstruct.flver.image.image_import_manager import ImageImportManager
from io_soulstruct.flver.models import BlenderFLVER
from io_soulstruct.flver.utilities import get_flvers_from_binder
from io_soulstruct.msb.properties import MSBPartSubtype, MSBObjectProps
from io_soulstruct.msb.utilities import find_flver_model, batch_import_flver_models
from io_soulstruct.types import *
from io_soulstruct.utilities import *
from soulstruct.containers import Binder
from soulstruct.demonssouls.maps.parts import MSBObject, MSBDummyObject
from soulstruct.demonssouls.maps.models import MSBObjectModel
from .msb_part import BlenderMSBPart

if tp.TYPE_CHECKING:
    from soulstruct.demonssouls.maps.msb import MSB


class BlenderMSBObject(BlenderMSBPart[MSBObject, MSBObjectProps]):
    """Also used for 'Dummy' (Unused) MSB Objects."""

    OBJ_DATA_TYPE = SoulstructDataType.MESH
    SOULSTRUCT_CLASS = MSBObject
    SOULSTRUCT_MODEL_CLASS = MSBObjectModel
    PART_SUBTYPE = MSBPartSubtype.Object
    MODEL_SUBTYPES = ["object_models"]

    __slots__ = []

    AUTO_OBJECT_PROPS = [
        "break_term",
        "net_sync_type",
        "default_animation",
        "unk_x0e",
        "unk_x10",
    ]

    break_term: int
    net_sync_type: int
    default_animation: int
    unk_x0e: int
    unk_x10: int

    @property
    def armature(self) -> bpy.types.ArmatureObject | None:
        """Detect parent Armature of wrapped Mesh object. Rarely present for Parts."""
        if self.obj.parent and self.obj.parent.type == "ARMATURE":
            # noinspection PyTypeChecker
            return self.obj.parent
        return None

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MSBObject,
        name: str,
        collection: bpy.types.Collection = None,
        map_stem="",
        try_import_model=True,
        model_collection: bpy.types.Collection = None,
    ) -> tp.Self:
        bl_obj = super().new_from_soulstruct_obj(
            operator, context, soulstruct_obj, name, collection, map_stem, try_import_model, model_collection
        )  # type: tp.Self

        for name in cls.AUTO_OBJECT_PROPS:
            setattr(bl_obj, name, getattr(soulstruct_obj, name))

        bl_obj.subtype_properties.is_dummy = isinstance(soulstruct_obj, MSBDummyObject)
        # if bl_obj.subtype_properties.is_dummy and context.scene.msb_import_settings.hide_dummy_entries:
        #     bl_obj.obj.hide_viewport = True

        return bl_obj

    def _create_soulstruct_obj(self):
        if self.subtype_properties.is_dummy:
            return MSBDummyObject(name=self.export_name)
        return MSBObject(name=self.export_name)

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        map_stem="",
        msb: MSB = None,
    ) -> MSBObject:
        msb_object = super().to_soulstruct_obj(operator, context, map_stem, msb)  # type: MSBObject

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
        model_collection: bpy.types.Collection = None,
    ) -> bpy.types.MeshObject:
        """Import the model of the given name into a collection in the current scene."""
        settings = operator.settings(context)

        import_settings = context.scene.flver_import_settings
        objbnd_path = settings.get_import_file_path(f"obj/{model_name}.objbnd")

        operator.info(f"Importing object FLVER from: {objbnd_path.name}")

        image_import_manager = ImageImportManager(operator, context) if import_settings.import_textures else None

        objbnd = Binder.from_path(objbnd_path)
        binder_flvers = get_flvers_from_binder(objbnd, objbnd_path, allow_multiple=True)
        if image_import_manager:
            image_import_manager.find_flver_textures(objbnd_path, objbnd)
        flver = binder_flvers[0]  # TODO: ignoring secondary Object FLVERs for now

        if not model_collection:
            model_collection = get_or_create_collection(
                context.scene.collection,
                "Object Models",
                hide_viewport=context.scene.msb_import_settings.hide_model_collections,
            )

        try:
            bl_flver = BlenderFLVER.new_from_soulstruct_obj(
                operator,
                context,
                flver,
                model_name,
                image_import_manager=image_import_manager,
                collection=model_collection,
                force_bone_data_type=BlenderFLVER.BoneDataType.EDIT,
            )
        except Exception as ex:
            traceback.print_exc()  # for inspection in Blender console
            raise FLVERImportError(f"Cannot import FLVER from OBJBND: {objbnd_path.name}. Error: {ex}")

        # Only need to return the Mesh.
        return bl_flver.mesh

    @classmethod
    def batch_import_models(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        parts: list[MSBObject],
        map_stem: str,
    ):
        """Import all models for a batch of MSB Parts, as needed, in parallel as much as possible."""
        settings = operator.settings(context)

        model_datas = {}
        model_objbnds = {}
        for part in parts:
            if not part.model:
                continue  # ignore (warning will appear when `bl_part.model` assignes None)
            model_name = part.model.get_model_file_stem(map_stem)
            if model_name in model_datas:
                continue  # already queued for import
            try:
                cls.find_model_mesh(model_name, map_stem)
            except MissingPartModelError:
                # Queue up path for batch import.
                objbnd_path = settings.get_import_file_path(f"obj/{model_name}.objbnd")
                operator.info(f"Importing object FLVER from: {objbnd_path.name}")
                objbnd = Binder.from_path(objbnd_path)
                flver_entries = objbnd.find_entries_matching_name(r".*\.flver(\.dcx)?")
                if not flver_entries:
                    raise FLVERImportError(f"Cannot find a FLVER file in OBJBND {objbnd_path}.")
                # TODO: Ignoring secondary object FLVERs for now.
                model_datas[model_name] = flver_entries[0]
                model_objbnds[model_name] = objbnd

        if not model_datas:
            operator.info("No Object FLVER models to import.")
            return  # nothing to import

        batch_import_flver_models(
            operator,
            context,
            model_datas,
            map_stem,
            cls.PART_SUBTYPE.get_nice_name(),
            flver_source_binders=model_objbnds,
        )


BlenderMSBObject.add_auto_subtype_props(*BlenderMSBObject.AUTO_OBJECT_PROPS)
