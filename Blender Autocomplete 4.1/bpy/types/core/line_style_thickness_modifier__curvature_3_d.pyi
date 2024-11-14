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


class LineStyleThicknessModifier_Curvature_3D(
    LineStyleThicknessModifier, LineStyleModifier, bpy_struct
):
    """Line thickness based on the radial curvature of 3D mesh surfaces"""

    blend: str
    """ Specify how the modifier value is blended into the base value

    :type: str
    """

    curvature_max: float
    """ Maximum Curvature

    :type: float
    """

    curvature_min: float
    """ Minimum Curvature

    :type: float
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

    thickness_max: float
    """ Maximum thickness

    :type: float
    """

    thickness_min: float
    """ Minimum thickness

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
