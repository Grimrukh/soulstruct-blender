import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CorrectiveSmoothModifier(Modifier, bpy_struct):
    """Correct distortion caused by deformation"""

    factor: float
    """ Smooth effect factor

    :type: float
    """

    invert_vertex_group: bool
    """ Invert vertex group influence

    :type: bool
    """

    is_bind: bool
    """ 

    :type: bool
    """

    iterations: int
    """ 

    :type: int
    """

    rest_source: str
    """ Select the source of rest positions

    :type: str
    """

    scale: float
    """ Compensate for scale applied by other modifiers

    :type: float
    """

    smooth_type: str
    """ Method used for smoothing

    :type: str
    """

    use_only_smooth: bool
    """ Apply smoothing without reconstructing the surface

    :type: bool
    """

    use_pin_boundary: bool
    """ Excludes boundary vertices from being smoothed

    :type: bool
    """

    vertex_group: str
    """ Name of Vertex Group which determines influence of modifier per point

    :type: str
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
