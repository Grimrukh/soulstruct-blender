import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .curve_map import CurveMap
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CurveMapping(bpy_struct):
    """Curve mapping to map color, vector and scalar values to other values using a user defined curve"""

    black_level: mathutils.Color
    """ For RGB curves, the color that black is mapped to

    :type: mathutils.Color
    """

    clip_max_x: float
    """ 

    :type: float
    """

    clip_max_y: float
    """ 

    :type: float
    """

    clip_min_x: float
    """ 

    :type: float
    """

    clip_min_y: float
    """ 

    :type: float
    """

    curves: bpy_prop_collection[CurveMap]
    """ 

    :type: bpy_prop_collection[CurveMap]
    """

    extend: str
    """ Extrapolate the curve or extend it horizontally

    :type: str
    """

    tone: str
    """ Tone of the curve

    :type: str
    """

    use_clip: bool
    """ Force the curve view to fit a defined boundary

    :type: bool
    """

    white_level: mathutils.Color
    """ For RGB curves, the color that white is mapped to

    :type: mathutils.Color
    """

    def update(self):
        """Update curve mapping after making changes"""
        ...

    def reset_view(self):
        """Reset the curve mapping grid to its clipping size"""
        ...

    def initialize(self):
        """Initialize curve"""
        ...

    def evaluate(self, curve: CurveMap, position: float | None) -> float:
        """Evaluate curve at given location

        :param curve: curve, Curve to evaluate
        :type curve: CurveMap
        :param position: Position, Position to evaluate curve at
        :type position: float | None
        :return: Value, Value of curve at given location
        :rtype: float
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
