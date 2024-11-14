import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .curve_point import CurvePoint

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CurveSlice(bpy_struct):
    """A single curve from a curves data-block"""

    first_point_index: int
    """ The index of this curve's first control point

    :type: int
    """

    index: int
    """ Index of this curve

    :type: int
    """

    points: bpy_prop_collection[CurvePoint]
    """ Control points of the curve

    :type: bpy_prop_collection[CurvePoint]
    """

    points_length: int
    """ Number of control points in the curve

    :type: int
    """

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
