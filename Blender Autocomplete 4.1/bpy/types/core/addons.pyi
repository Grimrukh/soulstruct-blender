import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .addon import Addon
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Addons(bpy_prop_collection[Addon], bpy_struct):
    """Collection of add-ons"""

    @classmethod
    def new(cls) -> Addon:
        """Add a new add-on

        :return: Add-on data
        :rtype: Addon
        """
        ...

    @classmethod
    def remove(cls, addon: Addon):
        """Remove add-on

        :param addon: Add-on to remove
        :type addon: Addon
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
