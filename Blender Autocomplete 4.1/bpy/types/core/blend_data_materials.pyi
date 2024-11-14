import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .material import Material

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataMaterials(bpy_prop_collection[Material], bpy_struct):
    """Collection of materials"""

    def new(self, name: str | typing.Any) -> Material:
        """Add a new material to the main database

        :param name: New name for the data-block
        :type name: str | typing.Any
        :return: New material data-block
        :rtype: Material
        """
        ...

    def create_gpencil_data(self, material: Material):
        """Add grease pencil material settings

        :param material: Material
        :type material: Material
        """
        ...

    def remove_gpencil_data(self, material: Material):
        """Remove grease pencil material settings

        :param material: Material
        :type material: Material
        """
        ...

    def remove(
        self,
        material: Material,
        do_unlink: bool | typing.Any | None = True,
        do_id_user: bool | typing.Any | None = True,
        do_ui_user: bool | typing.Any | None = True,
    ):
        """Remove a material from the current blendfile

        :param material: Material to remove
        :type material: Material
        :param do_unlink: Unlink all usages of this material before deleting it
        :type do_unlink: bool | typing.Any | None
        :param do_id_user: Decrement user counter of all datablocks used by this material
        :type do_id_user: bool | typing.Any | None
        :param do_ui_user: Make sure interface does not reference this material
        :type do_ui_user: bool | typing.Any | None
        """
        ...

    def tag(self, value: bool | None):
        """tag

        :param value: Value
        :type value: bool | None
        """
        ...

    @classmethod
    def bl_rna_get_subclass(cls, id: str | None, default=None) -> Struct:
        """

        :param id: The RNA type identifier.
        :type id: str | None
        :param default:
        :return: The RNA type or default when not found.
        :rtype: Struct
        """
        ...

    @classmethod
    def bl_rna_get_subclass_py(cls, id: str | None, default=None) -> typing.Any:
        """

        :param id: The RNA type identifier.
        :type id: str | None
        :param default:
        :return: The class or default when not found.
        :rtype: typing.Any
        """
        ...
