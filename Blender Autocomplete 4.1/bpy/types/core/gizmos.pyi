import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .gizmo import Gizmo
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Gizmos(bpy_prop_collection[Gizmo], bpy_struct):
    """Collection of gizmos"""

    def new(self, type: str | typing.Any) -> Gizmo:
        """Add gizmo

        :param type: Gizmo identifier
        :type type: str | typing.Any
        :return: New gizmo
        :rtype: Gizmo
        """
        ...

    def remove(self, gizmo: Gizmo):
        """Delete gizmo

        :param gizmo: New gizmo
        :type gizmo: Gizmo
        """
        ...

    def clear(self):
        """Delete all gizmos"""
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
