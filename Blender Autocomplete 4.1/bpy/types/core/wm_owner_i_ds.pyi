import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .wm_owner_id import wmOwnerID
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class wmOwnerIDs(bpy_prop_collection[wmOwnerID], bpy_struct):
    def new(self, name: str | typing.Any) -> wmOwnerID:
        """Add ui tag

        :param name: New name for the tag
        :type name: str | typing.Any
        :return:
        :rtype: wmOwnerID
        """
        ...

    def remove(self, owner_id: wmOwnerID):
        """Remove ui tag

        :param owner_id: Tag to remove
        :type owner_id: wmOwnerID
        """
        ...

    def clear(self):
        """Remove all tags"""
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
