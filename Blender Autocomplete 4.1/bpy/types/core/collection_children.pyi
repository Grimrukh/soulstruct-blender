import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .collection import Collection
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CollectionChildren(bpy_prop_collection[Collection], bpy_struct):
    """Collection of child collections"""

    def link(self, child: Collection):
        """Add this collection as child of this collection

        :param child: Collection to add
        :type child: Collection
        """
        ...

    def unlink(self, child: Collection | None):
        """Remove this child collection from a collection

        :param child: Collection to remove
        :type child: Collection | None
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
