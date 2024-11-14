import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .curve_mapping import CurveMapping

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BrushCurvesSculptSettings(bpy_struct):
    add_amount: int
    """ Number of curves added by the Add brush

    :type: int
    """

    curve_length: float
    """ Length of newly added curves when it is not interpolated from other curves

    :type: float
    """

    curve_parameter_falloff: CurveMapping
    """ Falloff that is applied from the tip to the root of each curve

    :type: CurveMapping
    """

    density_add_attempts: int
    """ How many times the Density brush tries to add a new curve

    :type: int
    """

    density_mode: str
    """ Determines whether the brush adds or removes curves

    :type: str
    """

    interpolate_length: bool
    """ Use length of the curves in close proximity

    :type: bool
    """

    interpolate_point_count: bool
    """ Use the number of points from the curves in close proximity

    :type: bool
    """

    interpolate_shape: bool
    """ Use shape of the curves in close proximity

    :type: bool
    """

    minimum_distance: float
    """ Goal distance between curve roots for the Density brush

    :type: float
    """

    minimum_length: float
    """ Avoid shrinking curves shorter than this length

    :type: float
    """

    points_per_curve: int
    """ Number of control points in a newly added curve

    :type: int
    """

    scale_uniform: bool
    """ Grow or shrink curves by changing their size uniformly instead of using trimming or extrapolation

    :type: bool
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
