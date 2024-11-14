import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .curve_profile_point import CurveProfilePoint
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CurveProfilePoints(bpy_prop_collection[CurveProfilePoint], bpy_struct):
    """Collection of Profile Points"""

    def add(self, x: float | None, y: float | None) -> CurveProfilePoint:
        """Add point to the profile

        :param x: X Position, X Position for new point
        :type x: float | None
        :param y: Y Position, Y Position for new point
        :type y: float | None
        :return: New point
        :rtype: CurveProfilePoint
        """
        ...

    def remove(self, point: CurveProfilePoint):
        """Delete point from the profile

        :param point: Point to remove
        :type point: CurveProfilePoint
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
