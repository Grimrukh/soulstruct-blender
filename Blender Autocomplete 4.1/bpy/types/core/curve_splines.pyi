import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .spline import Spline
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CurveSplines(bpy_prop_collection[Spline], bpy_struct):
    """Collection of curve splines"""

    active: Spline | None
    """ Active curve spline

    :type: Spline | None
    """

    def new(self, type: str | None) -> Spline:
        """Add a new spline to the curve

        :param type: type for the new spline
        :type type: str | None
        :return: The newly created spline
        :rtype: Spline
        """
        ...

    def remove(self, spline: Spline):
        """Remove a spline from a curve

        :param spline: The spline to remove
        :type spline: Spline
        """
        ...

    def clear(self):
        """Remove all splines from a curve"""
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
