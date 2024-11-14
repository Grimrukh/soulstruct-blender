import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .curve_map_point import CurveMapPoint

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CurveMapPoints(bpy_prop_collection[CurveMapPoint], bpy_struct):
    """Collection of Curve Map Points"""

    def new(self, position: float | None, value: float | None) -> CurveMapPoint:
        """Add point to CurveMap

        :param position: Position, Position to add point
        :type position: float | None
        :param value: Value, Value of point
        :type value: float | None
        :return: New point
        :rtype: CurveMapPoint
        """
        ...

    def remove(self, point: CurveMapPoint):
        """Delete point from CurveMap

        :param point: PointElement to remove
        :type point: CurveMapPoint
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
