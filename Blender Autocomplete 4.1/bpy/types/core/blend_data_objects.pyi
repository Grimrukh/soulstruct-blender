import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .id import ID
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataObjects(bpy_prop_collection[Object], bpy_struct):
    """Collection of objects"""

    def new(self, name: str | typing.Any, object_data: ID | None) -> Object:
        """Add a new object to the main database

        :param name: New name for the data-block
        :type name: str | typing.Any
        :param object_data: Object data or None for an empty object
        :type object_data: ID | None
        :return: New object data-block
        :rtype: Object
        """
        ...

    def remove(
        self,
        object: Object,
        do_unlink: bool | typing.Any | None = True,
        do_id_user: bool | typing.Any | None = True,
        do_ui_user: bool | typing.Any | None = True,
    ):
        """Remove an object from the current blendfile

        :param object: Object to remove
        :type object: Object
        :param do_unlink: Unlink all usages of this object before deleting it
        :type do_unlink: bool | typing.Any | None
        :param do_id_user: Decrement user counter of all datablocks used by this object
        :type do_id_user: bool | typing.Any | None
        :param do_ui_user: Make sure interface does not reference this object
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
