import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .line_style_geometry_modifier import LineStyleGeometryModifier
from .line_style_modifier import LineStyleModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class LineStyleGeometryModifier_2DTransform(
    LineStyleGeometryModifier, LineStyleModifier, bpy_struct
):
    """Apply two-dimensional scaling and rotation to stroke backbone geometry"""

    angle: float
    """ Rotation angle

    :type: float
    """

    expanded: bool
    """ True if the modifier tab is expanded

    :type: bool
    """

    pivot: str
    """ Pivot of scaling and rotation operations

    :type: str
    """

    pivot_u: float
    """ Pivot in terms of the stroke point parameter u (0 <= u <= 1)

    :type: float
    """

    pivot_x: float
    """ 2D X coordinate of the absolute pivot

    :type: float
    """

    pivot_y: float
    """ 2D Y coordinate of the absolute pivot

    :type: float
    """

    scale_x: float
    """ Scaling factor that is applied along the X axis

    :type: float
    """

    scale_y: float
    """ Scaling factor that is applied along the Y axis

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
