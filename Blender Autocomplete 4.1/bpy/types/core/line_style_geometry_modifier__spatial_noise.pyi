import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .line_style_geometry_modifier import LineStyleGeometryModifier
from .line_style_modifier import LineStyleModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class LineStyleGeometryModifier_SpatialNoise(
    LineStyleGeometryModifier, LineStyleModifier, bpy_struct
):
    """Add spatial noise to stroke backbone geometry"""

    amplitude: float
    """ Amplitude of the spatial noise

    :type: float
    """

    expanded: bool
    """ True if the modifier tab is expanded

    :type: bool
    """

    octaves: int
    """ Number of octaves (i.e., the amount of detail of the spatial noise)

    :type: int
    """

    scale: float
    """ Scale of the spatial noise

    :type: float
    """

    smooth: bool
    """ If true, the spatial noise is smooth

    :type: bool
    """

    type: str
    """ Type of the modifier

    :type: str
    """

    use: bool
    """ Enable or disable this modifier during stroke rendering

    :type: bool
    """

    use_pure_random: bool
    """ If true, the spatial noise does not show any coherence

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
