import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .mask_spline_points import MaskSplinePoints

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MaskSpline(bpy_struct):
    """Single spline used for defining mask shape"""

    offset_mode: str
    """ The method used for calculating the feather offset

    :type: str
    """

    points: MaskSplinePoints
    """ Collection of points

    :type: MaskSplinePoints
    """

    use_cyclic: bool
    """ Make this spline a closed loop

    :type: bool
    """

    use_fill: bool
    """ Make this spline filled

    :type: bool
    """

    use_self_intersection_check: bool
    """ Prevent feather from self-intersections

    :type: bool
    """

    weight_interpolation: str
    """ The type of weight interpolation for spline

    :type: str
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
