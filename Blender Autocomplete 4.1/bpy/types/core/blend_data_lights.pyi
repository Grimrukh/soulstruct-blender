import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .light import Light

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataLights(bpy_prop_collection[Light], bpy_struct):
    """Collection of lights"""

    def new(self, name: str | typing.Any, type: str | None) -> Light:
        """Add a new light to the main database

        :param name: New name for the data-block
        :type name: str | typing.Any
        :param type: Type, The type of light to add
        :type type: str | None
        :return: New light data-block
        :rtype: Light
        """
        ...

    def remove(
        self,
        light: Light,
        do_unlink: bool | typing.Any | None = True,
        do_id_user: bool | typing.Any | None = True,
        do_ui_user: bool | typing.Any | None = True,
    ):
        """Remove a light from the current blendfile

        :param light: Light to remove
        :type light: Light
        :param do_unlink: Unlink all usages of this light before deleting it (WARNING: will also delete objects instancing that light data)
        :type do_unlink: bool | typing.Any | None
        :param do_id_user: Decrement user counter of all datablocks used by this light data
        :type do_id_user: bool | typing.Any | None
        :param do_ui_user: Make sure interface does not reference this light data
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
