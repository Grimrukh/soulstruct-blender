import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .curve_profile_point import CurveProfilePoint
from .bpy_struct import bpy_struct
from .curve_profile_points import CurveProfilePoints

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CurveProfile(bpy_struct):
    """Profile Path editor used to build a profile path"""

    points: CurveProfilePoints
    """ Profile control points

    :type: CurveProfilePoints
    """

    preset: str
    """ 

    :type: str
    """

    segments: bpy_prop_collection[CurveProfilePoint]
    """ Segments sampled from control points

    :type: bpy_prop_collection[CurveProfilePoint]
    """

    use_clip: bool
    """ Force the path view to fit a defined boundary

    :type: bool
    """

    use_sample_even_lengths: bool
    """ Sample edges with even lengths

    :type: bool
    """

    use_sample_straight_edges: bool
    """ Sample edges with vector handles

    :type: bool
    """

    def update(self):
        """Refresh internal data, remove doubles and clip points"""
        ...

    def reset_view(self):
        """Reset the curve profile grid to its clipping size"""
        ...

    def initialize(self, totsegments: typing.Any):
        """Set the number of display segments and fill tables

        :param totsegments: The number of segment values to initialize the segments table with
        :type totsegments: typing.Any
        """
        ...

    def evaluate(self, length_portion: float | None) -> mathutils.Vector:
        """Evaluate the at the given portion of the path length

        :param length_portion: Length Portion, Portion of the path length to travel before evaluation
        :type length_portion: float | None
        :return: Location, The location at the given portion of the profile
        :rtype: mathutils.Vector
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
