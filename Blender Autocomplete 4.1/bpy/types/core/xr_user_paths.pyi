import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .xr_user_path import XrUserPath
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class XrUserPaths(bpy_prop_collection[XrUserPath], bpy_struct):
    """Collection of OpenXR user paths"""

    def new(self, path: str | typing.Any) -> XrUserPath:
        """new

        :param path: Path, OpenXR user path
        :type path: str | typing.Any
        :return: User Path, Added user path
        :rtype: XrUserPath
        """
        ...

    def remove(self, user_path: XrUserPath):
        """remove

        :param user_path: User Path
        :type user_path: XrUserPath
        """
        ...

    def find(self, path: str | typing.Any) -> XrUserPath:
        """find

        :param path: Path, OpenXR user path
        :type path: str | typing.Any
        :return: User Path, The user path with the given path
        :rtype: XrUserPath
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
