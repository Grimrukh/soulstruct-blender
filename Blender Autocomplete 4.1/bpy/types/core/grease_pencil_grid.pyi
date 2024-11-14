import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class GreasePencilGrid(bpy_struct):
    """Settings for grid and canvas in 3D viewport"""

    color: mathutils.Color
    """ Color for grid lines

    :type: mathutils.Color
    """

    lines: int
    """ Number of subdivisions in each side of symmetry line

    :type: int
    """

    offset: mathutils.Vector
    """ Offset of the canvas

    :type: mathutils.Vector
    """

    scale: mathutils.Vector
    """ Grid scale

    :type: mathutils.Vector
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
