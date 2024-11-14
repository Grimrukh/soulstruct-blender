import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .line_style_thickness_modifier import LineStyleThicknessModifier
from .line_style_modifier import LineStyleModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class LineStyleThicknessModifier_Noise(
    LineStyleThicknessModifier, LineStyleModifier, bpy_struct
):
    """Line thickness based on random noise"""

    amplitude: float
    """ Amplitude of the noise

    :type: float
    """

    blend: str
    """ Specify how the modifier value is blended into the base value

    :type: str
    """

    expanded: bool
    """ True if the modifier tab is expanded

    :type: bool
    """

    influence: float
    """ Influence factor by which the modifier changes the property

    :type: float
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

    use_asymmetric: bool
    """ Allow thickness to be assigned asymmetrically

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
