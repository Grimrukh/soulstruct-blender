import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class UserAssetLibrary(bpy_struct):
    """Settings to define a reusable library for Asset Browsers to use"""

    import_method: str
    """ Determine how the asset will be imported, unless overridden by the Asset Browser

    :type: str
    """

    name: str
    """ Identifier (not necessarily unique) for the asset library

    :type: str
    """

    path: str
    """ Path to a directory with .blend files to use as an asset library

    :type: str
    """

    use_relative_path: bool
    """ Use relative path when linking assets from this asset library

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
