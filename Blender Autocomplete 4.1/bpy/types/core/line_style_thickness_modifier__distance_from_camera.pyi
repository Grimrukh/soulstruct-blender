import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .curve_mapping import CurveMapping
from .line_style_thickness_modifier import LineStyleThicknessModifier
from .line_style_modifier import LineStyleModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class LineStyleThicknessModifier_DistanceFromCamera(
    LineStyleThicknessModifier, LineStyleModifier, bpy_struct
):
    """Change line thickness based on the distance from the camera"""

    blend: str
    """ Specify how the modifier value is blended into the base value

    :type: str
    """

    curve: CurveMapping
    """ Curve used for the curve mapping

    :type: CurveMapping
    """

    expanded: bool
    """ True if the modifier tab is expanded

    :type: bool
    """

    influence: float
    """ Influence factor by which the modifier changes the property

    :type: float
    """

    invert: bool
    """ Invert the fade-out direction of the linear mapping

    :type: bool
    """

    mapping: str
    """ Select the mapping type

    :type: str
    """

    range_max: float
    """ Upper bound of the input range the mapping is applied

    :type: float
    """

    range_min: float
    """ Lower bound of the input range the mapping is applied

    :type: float
    """

    type: str
    """ Type of the modifier

    :type: str
    """

    use: bool
    """ Enable or disable this modifier during stroke rendering

    :type: bool
    """

    value_max: float
    """ Maximum output value of the mapping

    :type: float
    """

    value_min: float
    """ Minimum output value of the mapping

    :type: float
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
