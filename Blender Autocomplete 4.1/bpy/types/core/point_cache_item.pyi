import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class PointCacheItem(bpy_struct):
    """Point cache for physics simulations"""

    compression: str
    """ Compression method to be used

    :type: str
    """

    filepath: str
    """ Cache file path

    :type: str
    """

    frame_end: int
    """ Frame on which the simulation stops

    :type: int
    """

    frame_start: int
    """ Frame on which the simulation starts

    :type: int
    """

    frame_step: int
    """ Number of frames between cached frames

    :type: int
    """

    index: int
    """ Index number of cache files

    :type: int
    """

    info: str
    """ Info on current cache status

    :type: str
    """

    is_baked: bool
    """ The cache is baked

    :type: bool
    """

    is_baking: bool
    """ The cache is being baked

    :type: bool
    """

    is_frame_skip: bool
    """ Some frames were skipped while baking/saving that cache

    :type: bool
    """

    is_outdated: bool
    """ 

    :type: bool
    """

    name: str
    """ Cache name

    :type: str
    """

    use_disk_cache: bool
    """ Save cache files to disk (.blend file must be saved first)

    :type: bool
    """

    use_external: bool
    """ Read cache from an external location

    :type: bool
    """

    use_library_path: bool
    """ Use this file's path for the disk cache when library linked into another file (for local bakes per scene file, disable this option)

    :type: bool
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
