import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .line_style_geometry_modifier import LineStyleGeometryModifier
from .line_style_modifier import LineStyleModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class LineStyleGeometryModifier_Blueprint(
    LineStyleGeometryModifier, LineStyleModifier, bpy_struct
):
    """Produce a blueprint using circular, elliptic, and square contour strokes"""

    backbone_length: float
    """ Amount of backbone stretching

    :type: float
    """

    expanded: bool
    """ True if the modifier tab is expanded

    :type: bool
    """

    random_backbone: int
    """ Randomness of the backbone stretching

    :type: int
    """

    random_center: int
    """ Randomness of the center

    :type: int
    """

    random_radius: int
    """ Randomness of the radius

    :type: int
    """

    rounds: int
    """ Number of rounds in contour strokes

    :type: int
    """

    shape: str
    """ Select the shape of blueprint contour strokes

    :type: str
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
