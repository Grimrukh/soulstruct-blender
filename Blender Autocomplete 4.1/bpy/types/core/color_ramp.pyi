import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .color_ramp_elements import ColorRampElements

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ColorRamp(bpy_struct):
    """Color ramp mapping a scalar value to a color"""

    color_mode: str
    """ Set color mode to use for interpolation

    :type: str
    """

    elements: ColorRampElements
    """ 

    :type: ColorRampElements
    """

    hue_interpolation: str
    """ Set color interpolation

    :type: str
    """

    interpolation: str
    """ Set interpolation between color stops

    :type: str
    """

    def evaluate(self, position: float | None) -> bpy_prop_array[float]:
        """Evaluate Color Ramp

        :param position: Position, Evaluate Color Ramp at position
        :type position: float | None
        :return: Color, Color at given position
        :rtype: bpy_prop_array[float]
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
