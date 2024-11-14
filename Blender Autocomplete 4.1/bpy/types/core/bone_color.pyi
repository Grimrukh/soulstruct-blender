import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .theme_bone_color_set import ThemeBoneColorSet

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BoneColor(bpy_struct):
    """Theme color or custom color of a bone"""

    custom: ThemeBoneColorSet
    """ The custom bone colors, used when palette is 'CUSTOM'

    :type: ThemeBoneColorSet
    """

    is_custom: bool
    """ A color palette is user-defined, instead of using a theme-defined one

    :type: bool
    """

    palette: str
    """ Color palette to use

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
