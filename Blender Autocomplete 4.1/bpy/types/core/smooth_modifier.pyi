import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SmoothModifier(Modifier, bpy_struct):
    """Smoothing effect modifier"""

    factor: float
    """ Strength of modifier effect

    :type: float
    """

    invert_vertex_group: bool
    """ Invert vertex group influence

    :type: bool
    """

    iterations: int
    """ 

    :type: int
    """

    use_x: bool
    """ Smooth object along X axis

    :type: bool
    """

    use_y: bool
    """ Smooth object along Y axis

    :type: bool
    """

    use_z: bool
    """ Smooth object along Z axis

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
