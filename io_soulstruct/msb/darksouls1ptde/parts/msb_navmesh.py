from __future__ import annotations

__all__ = [
    "BlenderMSBNavmesh",
]

import re
import traceback
import typing as tp

import bpy
from io_soulstruct.exceptions import NVMImportError, MissingPartModelError
from io_soulstruct.msb.properties import MSBPartSubtype, MSBNavmeshProps
from io_soulstruct.navmesh.nvm.types import *
from io_soulstruct.types import *
from io_soulstruct.utilities import *
from soulstruct.base.maps.msb.utils import GroupBitSet128
from soulstruct.containers import Binder, EntryNotFoundError
from soulstruct.darksouls1r.maps.navmesh.nvm import NVM
from soulstruct.darksouls1ptde.maps.models import MSBNavmeshModel
from soulstruct.darksouls1r.maps.parts import MSBNavmesh
from .msb_part import BlenderMSBPart

if tp.TYPE_CHECKING:
    from soulstruct.darksouls1r.maps.msb import MSB


class BlenderMSBNavmesh(BlenderMSBPart[MSBNavmesh, MSBNavmeshProps]):
    """Not FLVER-based."""

    OBJ_DATA_TYPE = SoulstructDataType.MESH
    SOULSTRUCT_CLASS = MSBNavmesh
    SOULSTRUCT_MODEL_CLASS = MSBNavmeshModel
    PART_SUBTYPE = MSBPartSubtype.Navmesh
    MODEL_SUBTYPES = ["navmesh_models"]
    MODEL_USES_LATEST_MAP = True  # only DS1 map asset to use latest map version for model import

    __slots__ = []
    data: bpy.types.Mesh

    @property
    def navmesh_groups(self):
        return self._get_groups_bit_set(self.subtype_properties.get_navmesh_groups_props_128())

    @navmesh_groups.setter
    def navmesh_groups(self, value: set[int] | GroupBitSet128):
        if isinstance(value, GroupBitSet128):
            value = value.enabled_bits
        self._set_groups_bit_set(self.subtype_properties.get_navmesh_groups_props_128(), value)

    def get_nvm_model(self) -> BlenderNVM:
        if not self.model:
            raise MissingPartModelError("Navmesh does not have a model.")
        return BlenderNVM(self.model)

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: MSBNavmesh,
        name: str,
        collection: bpy.types.Collection = None,
        map_stem="",
        try_import_model=True,
        model_collection: bpy.types.Collection = None,
    ) -> tp.Self:
        bl_navmesh = super().new_from_soulstruct_obj(
            operator, context, soulstruct_obj, name, collection, map_stem, try_import_model, model_collection
        )

        bl_navmesh.navmesh_groups = soulstruct_obj.navmesh_groups

        # Show wireframe by default.
        bl_navmesh.obj.show_wire = True

        return bl_navmesh

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        map_stem="",
        msb: MSB = None,
    ) -> MSBNavmesh:
        navmesh = super().to_soulstruct_obj(operator, context, map_stem=map_stem, msb=msb)
        navmesh.navmesh_groups = self.navmesh_groups
        return navmesh

    @classmethod
    def find_model_mesh(cls, model_name: str, map_stem: str) -> bpy.types.MeshObject:
        """Find the given Navmesh model in Blender data."""
        obj = find_obj(name=model_name, find_stem=True, soulstruct_type=SoulstructType.NAVMESH)
        if obj is None:
            raise MissingPartModelError(f"Navmesh model mesh '{model_name}' not found in Blender data.")
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
        """Import the Navmesh NVM model of the given name into a collection in the current scene.

        NOTE: `map_stem` should already be set to latest version if option is enabled. This function is agnostic.
        """
        settings = operator.settings(context)

        try:
            nvmbnd_path = settings.get_import_map_file_path(f"{map_stem}.nvmbnd")
        except FileNotFoundError:
            raise NVMImportError(f"Could not find NVMBND file for map {map_stem}.")

        nvm_entry_name = model_name + ".nvm"  # no DCX in DSR
        nvmbnd = Binder.from_path(nvmbnd_path)
        try:
            nvm_entry = nvmbnd.find_entry_matching_name(nvm_entry_name, flags=re.IGNORECASE, escape=True)
        except EntryNotFoundError:
            raise NVMImportError(f"Could not find NVM entry '{nvm_entry_name}' in NVMBND file '{nvmbnd_path.name}'.")

        nvm = nvm_entry.to_binary_file(NVM)

        if not model_collection:
            model_collection = get_or_create_collection(
                context.scene.collection,
                f"{map_stem} Models",
                f"{map_stem} Navmesh Models",
                hide_viewport=context.scene.msb_import_settings.hide_model_collections,
            )

        try:
            bl_nvm = BlenderNVM.new_from_soulstruct_obj(
                operator,
                context,
                nvm,
                model_name,
                collection=model_collection,
            )
        except Exception as ex:
            traceback.print_exc()  # for inspection in Blender console
            raise NVMImportError(f"Cannot import NVM: {model_name}. Error: {ex}")

        bl_nvm.set_face_materials(nvm)
        # Don't create quadtree boxes.

        # TODO: NVM import is so fast that this just slows the console down when importing all navmeshes.
        # operator.info(f"Imported NVM model {import_info.model_file_stem} as '{import_info.bl_name}'.")

        return bl_nvm.obj
