from __future__ import annotations

__all__ = [
    "BlenderMSBObject",
]

import traceback
import typing as tp

import bpy
from io_soulstruct.exceptions import MSBPartExportError, FLVERImportError
from io_soulstruct.flver.model_import.core import FLVERImporter
from io_soulstruct.flver.textures.import_textures import TextureImportManager
from io_soulstruct.flver.utilities import get_flvers_from_binder
from io_soulstruct.general.core import SoulstructSettings
from io_soulstruct.msb.properties import MSBPartSubtype, MSBObjectProps
from io_soulstruct.msb.utilities import find_flver_model
from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities import *
from soulstruct.containers import Binder
from soulstruct.darksouls1ptde.maps.parts import MSBObject, MSBDummyObject
from .base import BlenderMSBPart

if tp.TYPE_CHECKING:
    from soulstruct.darksouls1ptde.maps.msb import MSB


class BlenderMSBObject(BlenderMSBPart):
    """Also used for 'Dummy' (Unused) MSB Objects."""

    PART_SUBTYPE = MSBPartSubtype.OBJECT
    MODEL_SUBTYPES = ["object_models"]

    @property
    def object_props(self) -> MSBObjectProps:
        return self.obj.msb_object_props

    def set_obj_properties(self, operator: LoggingOperator, entry: MSBObject | MSBDummyObject):
        super().set_obj_properties(operator, entry)
        props = self.object_props

        self.set_obj_entry_reference(operator, props, "draw_parent", entry, SoulstructType.MSB_PART)

        if isinstance(entry, MSBDummyObject):
            props.is_dummy = True

        self.set_obj_generic_props(entry, props, skip_names={"draw_parent", "is_dummy"})

    def set_entry_properties(self, operator: LoggingOperator, entry: MSBObject | MSBDummyObject, msb: MSB):
        super().set_entry_properties(operator, entry, msb)
        props = self.object_props

        if props.is_dummy and not isinstance(entry, MSBDummyObject):
            raise MSBPartExportError(
                f"Object '{entry.name}' is marked as a dummy object, but is being exported as a non-dummy MSB Object."
            )
        elif not props.is_dummy and isinstance(entry, MSBDummyObject):
            raise MSBPartExportError(
                f"Object '{entry.name}' is not marked as a dummy object, but is being exported as an MSB Dummy Object."
            )

        self.set_part_entry_reference(props.draw_parent, entry, "draw_parent", msb)

        self.set_entry_generic_props(props, entry, skip_names={"draw_parent", "is_dummy"})

    @classmethod
    def find_model(
        cls,
        model_name: str,
        map_stem: str,  # not required by all subtypes
    ):
        return find_flver_model(cls.PART_SUBTYPE, model_name)

    @classmethod
    def import_model(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        settings: SoulstructSettings,
        model_name: str,
        map_stem="",  # not used
    ) -> bpy.types.MeshObject:
        """Import the model of the given name into a collection in the current scene."""

        flver_import_settings = context.scene.flver_import_settings
        chrbnd_path = settings.get_import_file_path(f"obj/{model_name}.objbnd")

        operator.info(f"Importing object FLVER from: {chrbnd_path.name}")

        texture_manager = TextureImportManager(settings) if flver_import_settings.import_textures else None

        objbnd = Binder.from_path(chrbnd_path)
        binder_flvers = get_flvers_from_binder(objbnd, chrbnd_path, allow_multiple=False)
        if texture_manager:
            texture_manager.find_flver_textures(chrbnd_path, objbnd)
        flver = binder_flvers[0]

        importer = FLVERImporter(
            operator,
            context,
            settings,
            texture_import_manager=texture_manager,
            collection=get_collection("Object Models", context.scene.collection),
        )

        try:
            bl_flver = importer.import_flver(flver, name=model_name)
        except Exception as ex:
            # Delete any objects created prior to exception.
            importer.abort_import()
            traceback.print_exc()  # for inspection in Blender console
            raise FLVERImportError(f"Cannot import FLVER from OBJBND: {chrbnd_path.name}. Error: {ex}")

        # Only need to return the Mesh.
        return bl_flver.mesh
