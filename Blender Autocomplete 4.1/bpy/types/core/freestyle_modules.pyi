import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .freestyle_module_settings import FreestyleModuleSettings
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FreestyleModules(bpy_prop_collection[FreestyleModuleSettings], bpy_struct):
    """A list of style modules (to be applied from top to bottom)"""

    def new(self) -> FreestyleModuleSettings:
        """Add a style module to scene render layer Freestyle settings

        :return: Newly created style module
        :rtype: FreestyleModuleSettings
        """
        ...

    def remove(self, module: FreestyleModuleSettings):
        """Remove a style module from scene render layer Freestyle settings

        :param module: Style module to remove
        :type module: FreestyleModuleSettings
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
