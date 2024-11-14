import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .theme_space_generic import ThemeSpaceGeneric

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ThemeTextEditor(bpy_struct):
    """Theme settings for the Text Editor"""

    cursor: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    line_numbers: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    line_numbers_background: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    selected_text: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    space: ThemeSpaceGeneric
    """ Settings for space

    :type: ThemeSpaceGeneric
    """

    syntax_builtin: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    syntax_comment: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    syntax_numbers: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    syntax_preprocessor: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    syntax_reserved: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    syntax_special: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    syntax_string: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    syntax_symbols: mathutils.Color
    """ 

    :type: mathutils.Color
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
