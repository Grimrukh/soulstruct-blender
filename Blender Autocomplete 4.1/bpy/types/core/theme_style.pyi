import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .theme_font_style import ThemeFontStyle

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ThemeStyle(bpy_struct):
    """Theme settings for style sets"""

    panel_title: ThemeFontStyle
    """ 

    :type: ThemeFontStyle
    """

    widget: ThemeFontStyle
    """ 

    :type: ThemeFontStyle
    """

    widget_label: ThemeFontStyle
    """ 

    :type: ThemeFontStyle
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
