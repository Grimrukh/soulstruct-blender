import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .collection import Collection
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataCollections(bpy_prop_collection[Collection], bpy_struct):
    """Collection of collections"""

    def new(self, name: str | typing.Any) -> Collection:
        """Add a new collection to the main database

        :param name: New name for the data-block
        :type name: str | typing.Any
        :return: New collection data-block
        :rtype: Collection
        """
        ...

    def remove(
        self,
        collection: Collection,
        do_unlink: bool | typing.Any | None = True,
        do_id_user: bool | typing.Any | None = True,
        do_ui_user: bool | typing.Any | None = True,
    ):
        """Remove a collection from the current blendfile

        :param collection: Collection to remove
        :type collection: Collection
        :param do_unlink: Unlink all usages of this collection before deleting it
        :type do_unlink: bool | typing.Any | None
        :param do_id_user: Decrement user counter of all datablocks used by this collection
        :type do_id_user: bool | typing.Any | None
        :param do_ui_user: Make sure interface does not reference this collection
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
