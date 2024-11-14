import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .retiming_key import RetimingKey

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class RetimingKeys(bpy_prop_collection[RetimingKey], bpy_struct):
    """Collection of RetimingKey"""

    def add(self, timeline_frame: typing.Any | None = 0) -> RetimingKey:
        """Add retiming key

        :param timeline_frame: Timeline Frame
        :type timeline_frame: typing.Any | None
        :return: New RetimingKey
        :rtype: RetimingKey
        """
        ...

    def reset(self):
        """Remove all retiming keys"""
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
