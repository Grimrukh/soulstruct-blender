from __future__ import annotations

__all__ = [
    "BlenderMSBObject",
]

import traceback

import bpy
from io_soulstruct.exceptions import FLVERImportError
from io_soulstruct.flver.model_import.core import FLVERImporter
from io_soulstruct.flver.model_import.settings import FLVERImportSettings
from io_soulstruct.flver.textures.import_textures import TextureImportManager
from io_soulstruct.flver.utilities import get_flvers_from_binder
from io_soulstruct.general.core import SoulstructSettings
from io_soulstruct.utilities import LoggingOperator, get_collection, find_obj_or_create_empty
from soulstruct.containers import Binder
from soulstruct.darksouls1ptde.maps.parts import MSBObject, MSBDummyObject
from .base import BlenderMSBPart
from io_soulstruct.msb.properties import MSBPartSubtype, MSBObjectProps
from ..utilities import find_flver_model


class BlenderMSBObject(BlenderMSBPart):
    """Also used for 'Dummy' (Unused) MSB Objects."""

    PART_SUBTYPE = MSBPartSubtype.OBJECT

    @property
    def object_props(self) -> MSBObjectProps:
        return self.obj.msb_object_props

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

        flver_import_settings = context.scene.flver_import_settings  # type: FLVERImportSettings
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

    def set_properties(self, operator: LoggingOperator, part: MSBObject):
        super().set_properties(operator, part)
        if not isinstance(part, MSBObject):  # `MSBDummyObject` is a subclass of `MSBObject` in DS1
            return

        props = self.object_props

        if part.draw_parent:
            was_missing, props.draw_parent = find_obj_or_create_empty(part.draw_parent.name)
            if was_missing:
                operator.warning(
                    f"Draw parent '{part.draw_parent.name}' not found in scene. Creating empty object with that name "
                    f"in Scene Collection to use as draw parent for '{part.name}'."
                )

        for prop_name in props.__annotations__:
            if prop_name == "is_dummy":
                # Class-dependent.
                setattr(props, prop_name, isinstance(part, MSBDummyObject))
                continue
            if prop_name == "draw_parent":
                continue  # handled above
            # Primitive property.
            setattr(props, prop_name, getattr(part, prop_name))
