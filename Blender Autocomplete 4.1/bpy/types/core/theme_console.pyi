import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .theme_space_generic import ThemeSpaceGeneric

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ThemeConsole(bpy_struct):
    """Theme settings for the Console"""

    cursor: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    line_error: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    line_info: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    line_input: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    line_output: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    select: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    space: ThemeSpaceGeneric
    """ Settings for space

    :type: ThemeSpaceGeneric
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
