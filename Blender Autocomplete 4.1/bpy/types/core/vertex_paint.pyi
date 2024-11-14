import typing
import collections.abc
import mathutils
from .struct import Struct
from .paint import Paint
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class VertexPaint(Paint, bpy_struct):
    """Properties of vertex and weight paint mode"""

    radial_symmetry: bpy_prop_array[int]
    """ Number of times to copy strokes across the surface

    :type: bpy_prop_array[int]
    """

    use_group_restrict: bool
    """ Restrict painting to vertices in the group

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
