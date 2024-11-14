import typing
import collections.abc
import mathutils
from .struct import Struct
from .cache_file import CacheFile
from .constraint import Constraint
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class TransformCacheConstraint(Constraint, bpy_struct):
    """Look up transformation from an external file"""

    cache_file: CacheFile
    """ 

    :type: CacheFile
    """

    object_path: str
    """ Path to the object in the Alembic archive used to lookup the transform matrix

    :type: str
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
