import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ThemeBoneColorSet(bpy_struct):
    """Theme settings for bone color sets"""

    active: mathutils.Color | None
    """ Color used for active bones

    :type: mathutils.Color | None
    """

    normal: mathutils.Color
    """ Color used for the surface of bones

    :type: mathutils.Color
    """

    select: mathutils.Color
    """ Color used for selected bones

    :type: mathutils.Color
    """

    show_colored_constraints: bool
    """ Allow the use of colors indicating constraints/keyed status

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
