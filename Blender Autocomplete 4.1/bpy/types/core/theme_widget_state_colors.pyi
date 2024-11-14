import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ThemeWidgetStateColors(bpy_struct):
    """Theme settings for widget state colors"""

    blend: float
    """ 

    :type: float
    """

    inner_anim: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    inner_anim_sel: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    inner_changed: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    inner_changed_sel: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    inner_driven: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    inner_driven_sel: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    inner_key: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    inner_key_sel: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    inner_overridden: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    inner_overridden_sel: mathutils.Color
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
