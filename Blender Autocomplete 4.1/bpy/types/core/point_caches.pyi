import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .point_cache_item import PointCacheItem
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class PointCaches(bpy_prop_collection[PointCacheItem], bpy_struct):
    """Collection of point caches"""

    active_index: int | None
    """ 

    :type: int | None
    """

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
