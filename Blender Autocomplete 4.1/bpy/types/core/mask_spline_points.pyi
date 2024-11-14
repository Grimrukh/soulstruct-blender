import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .mask_spline_point import MaskSplinePoint

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MaskSplinePoints(bpy_prop_collection[MaskSplinePoint], bpy_struct):
    """Collection of masking spline points"""

    def add(self, count: int | None):
        """Add a number of point to this spline

        :param count: Number, Number of points to add to the spline
        :type count: int | None
        """
        ...

    def remove(self, point: MaskSplinePoint):
        """Remove a point from a spline

        :param point: The point to remove
        :type point: MaskSplinePoint
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
