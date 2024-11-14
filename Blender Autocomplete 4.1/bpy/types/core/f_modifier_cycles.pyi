import typing
import collections.abc
import mathutils
from .f_modifier import FModifier
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FModifierCycles(FModifier, bpy_struct):
    """Repeat the values of the modified F-Curve"""

    cycles_after: int
    """ Maximum number of cycles to allow after last keyframe (0 = infinite)

    :type: int
    """

    cycles_before: int
    """ Maximum number of cycles to allow before first keyframe (0 = infinite)

    :type: int
    """

    mode_after: str
    """ Cycling mode to use after last keyframe

    :type: str
    """

    mode_before: str
    """ Cycling mode to use before first keyframe

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
