import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .line_style_geometry_modifier import LineStyleGeometryModifier
from .line_style_modifier import LineStyleModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class LineStyleGeometryModifier_2DOffset(
    LineStyleGeometryModifier, LineStyleModifier, bpy_struct
):
    """Add two-dimensional offsets to stroke backbone geometry"""

    end: float
    """ Displacement that is applied from the end of the stroke

    :type: float
    """

    expanded: bool
    """ True if the modifier tab is expanded

    :type: bool
    """

    start: float
    """ Displacement that is applied from the beginning of the stroke

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

    x: float
    """ Displacement that is applied to the X coordinates of stroke vertices

    :type: float
    """

    y: float
    """ Displacement that is applied to the Y coordinates of stroke vertices

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
