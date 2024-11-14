import typing
import collections.abc
import mathutils
from .aov import AOV
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class AOVs(bpy_prop_collection[AOV], bpy_struct):
    """Collection of AOVs"""

    def add(self) -> AOV:
        """add

        :return: Newly created AOV
        :rtype: AOV
        """
        ...

    def remove(self, aov: AOV):
        """Remove an AOV

        :param aov: AOV to remove
        :type aov: AOV
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
