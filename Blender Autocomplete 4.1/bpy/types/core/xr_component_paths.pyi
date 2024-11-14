import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .xr_component_path import XrComponentPath
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class XrComponentPaths(bpy_prop_collection[XrComponentPath], bpy_struct):
    """Collection of OpenXR component paths"""

    def new(self, path: str | typing.Any) -> XrComponentPath:
        """new

        :param path: Path, OpenXR component path
        :type path: str | typing.Any
        :return: Component Path, Added component path
        :rtype: XrComponentPath
        """
        ...

    def remove(self, component_path: XrComponentPath):
        """remove

        :param component_path: Component Path
        :type component_path: XrComponentPath
        """
        ...

    def find(self, path: str | typing.Any) -> XrComponentPath:
        """find

        :param path: Path, OpenXR component path
        :type path: str | typing.Any
        :return: Component Path, The component path with the given path
        :rtype: XrComponentPath
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
