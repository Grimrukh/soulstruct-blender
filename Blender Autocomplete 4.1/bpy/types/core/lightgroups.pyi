import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .lightgroup import Lightgroup
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Lightgroups(bpy_prop_collection[Lightgroup], bpy_struct):
    """Collection of Lightgroups"""

    def add(self, name: str | typing.Any = "") -> Lightgroup:
        """add

        :param name: Name, Name of newly created lightgroup
        :type name: str | typing.Any
        :return: Newly created Lightgroup
        :rtype: Lightgroup
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
