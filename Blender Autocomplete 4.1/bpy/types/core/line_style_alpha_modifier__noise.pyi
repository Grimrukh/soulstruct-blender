import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .curve_mapping import CurveMapping
from .line_style_modifier import LineStyleModifier
from .line_style_alpha_modifier import LineStyleAlphaModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class LineStyleAlphaModifier_Noise(
    LineStyleAlphaModifier, LineStyleModifier, bpy_struct
):
    """Alpha transparency based on random noise"""

    amplitude: float
    """ Amplitude of the noise

    :type: float
    """

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

    period: float
    """ Period of the noise

    :type: float
    """

    seed: int
    """ Seed for the noise generation

    :type: int
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
