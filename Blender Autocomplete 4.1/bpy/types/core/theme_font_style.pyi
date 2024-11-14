import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ThemeFontStyle(bpy_struct):
    """Theme settings for Font"""

    character_weight: int
    """ Weight of the characters. 100-900, 400 is normal

    :type: int
    """

    points: float
    """ Font size in points

    :type: float
    """

    shadow: int
    """ Shadow size (0, 3 and 5 supported)

    :type: int
    """

    shadow_alpha: float
    """ 

    :type: float
    """

    shadow_offset_x: int
    """ Shadow offset in pixels

    :type: int
    """

    shadow_offset_y: int
    """ Shadow offset in pixels

    :type: int
    """

    shadow_value: float
    """ Shadow color in gray value

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
