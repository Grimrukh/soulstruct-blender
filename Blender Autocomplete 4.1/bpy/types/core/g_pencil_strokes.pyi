import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .g_pencil_stroke import GPencilStroke

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class GPencilStrokes(bpy_prop_collection[GPencilStroke], bpy_struct):
    """Collection of grease pencil stroke"""

    def new(self) -> GPencilStroke:
        """Add a new grease pencil stroke

        :return: The newly created stroke
        :rtype: GPencilStroke
        """
        ...

    def remove(self, stroke: GPencilStroke):
        """Remove a grease pencil stroke

        :param stroke: Stroke, The stroke to remove
        :type stroke: GPencilStroke
        """
        ...

    def close(self, stroke: GPencilStroke):
        """Close a grease pencil stroke adding geometry

        :param stroke: Stroke, The stroke to close
        :type stroke: GPencilStroke
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
