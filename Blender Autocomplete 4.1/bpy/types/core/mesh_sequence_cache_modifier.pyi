import typing
import collections.abc
import mathutils
from .struct import Struct
from .cache_file import CacheFile
from .bpy_struct import bpy_struct
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MeshSequenceCacheModifier(Modifier, bpy_struct):
    """Cache Mesh"""

    cache_file: CacheFile
    """ 

    :type: CacheFile
    """

    object_path: str
    """ Path to the object in the Alembic archive used to lookup geometric data

    :type: str
    """

    read_data: set[str]
    """ Data to read from the cache

    :type: set[str]
    """

    use_vertex_interpolation: bool
    """ Allow interpolation of vertex positions

    :type: bool
    """

    velocity_scale: float
    """ Multiplier used to control the magnitude of the velocity vectors for time effects

    :type: float
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
