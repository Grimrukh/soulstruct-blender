import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .f_curve import FCurve
from .bpy_struct import bpy_struct
from .theme_bone_color_set import ThemeBoneColorSet

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ActionGroup(bpy_struct):
    """Groups of F-Curves"""

    channels: bpy_prop_collection[FCurve]
    """ F-Curves in this group

    :type: bpy_prop_collection[FCurve]
    """

    color_set: str
    """ Custom color set to use

    :type: str
    """

    colors: ThemeBoneColorSet
    """ Copy of the colors associated with the group's color set

    :type: ThemeBoneColorSet
    """

    is_custom_color_set: bool
    """ Color set is user-defined instead of a fixed theme color set

    :type: bool
    """

    lock: bool
    """ Action group is locked

    :type: bool
    """

    mute: bool
    """ Action group is muted

    :type: bool
    """

    name: str
    """ 

    :type: str
    """

    select: bool
    """ Action group is selected

    :type: bool
    """

    show_expanded: bool
    """ Action group is expanded except in graph editor

    :type: bool
    """

    show_expanded_graph: bool
    """ Action group is expanded in graph editor

    :type: bool
    """

    use_pin: bool
    """ 

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
