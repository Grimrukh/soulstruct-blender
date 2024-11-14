import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .g_pencil_stroke_point import GPencilStrokePoint

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class GPencilStrokePoints(bpy_prop_collection[GPencilStrokePoint], bpy_struct):
    """Collection of grease pencil stroke points"""

    def add(
        self,
        count: int | None,
        pressure: typing.Any | None = 1.0,
        strength: typing.Any | None = 1.0,
    ):
        """Add a new grease pencil stroke point

        :param count: Number, Number of points to add to the stroke
        :type count: int | None
        :param pressure: Pressure, Pressure for newly created points
        :type pressure: typing.Any | None
        :param strength: Strength, Color intensity (alpha factor) for newly created points
        :type strength: typing.Any | None
        """
        ...

    def pop(self, index: typing.Any | None = -1):
        """Remove a grease pencil stroke point

        :param index: Index, point index
        :type index: typing.Any | None
        """
        ...

    def update(self):
        """Recalculate internal triangulation data"""
        ...

    def weight_get(
        self,
        vertex_group_index: typing.Any | None = 0,
        point_index: typing.Any | None = 0,
    ) -> float:
        """Get vertex group point weight

        :param vertex_group_index: Vertex Group Index, Index of Vertex Group in the array of groups
        :type vertex_group_index: typing.Any | None
        :param point_index: Point Index, Index of the Point in the array
        :type point_index: typing.Any | None
        :return: Weight, Point Weight
        :rtype: float
        """
        ...

    def weight_set(
        self,
        vertex_group_index: typing.Any | None = 0,
        point_index: typing.Any | None = 0,
        weight: typing.Any | None = 0.0,
    ):
        """Set vertex group point weight

        :param vertex_group_index: Vertex Group Index, Index of Vertex Group in the array of groups
        :type vertex_group_index: typing.Any | None
        :param point_index: Point Index, Index of the Point in the array
        :type point_index: typing.Any | None
        :param weight: Weight, Point Weight
        :type weight: typing.Any | None
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
