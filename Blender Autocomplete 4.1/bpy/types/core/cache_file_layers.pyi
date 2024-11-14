import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .cache_file_layer import CacheFileLayer
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CacheFileLayers(bpy_prop_collection[CacheFileLayer], bpy_struct):
    """Collection of cache layers"""

    active: CacheFileLayer | None
    """ Active layer of the CacheFile

    :type: CacheFileLayer | None
    """

    def new(self, filepath: str | typing.Any) -> CacheFileLayer:
        """Add a new layer

        :param filepath: File path to the archive used as a layer
        :type filepath: str | typing.Any
        :return: Newly created layer
        :rtype: CacheFileLayer
        """
        ...

    def remove(self, layer: CacheFileLayer):
        """Remove an existing layer from the cache file

        :param layer: Layer to remove
        :type layer: CacheFileLayer
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
