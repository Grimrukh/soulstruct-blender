import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MovieTrackingDopesheet(bpy_struct):
    """Match-moving dopesheet data"""

    show_hidden: bool
    """ Include channels from objects/bone that are not visible

    :type: bool
    """

    show_only_selected: bool
    """ Only include channels relating to selected objects and data

    :type: bool
    """

    sort_method: str
    """ Method to be used to sort channels in dopesheet view

    :type: str
    """

    use_invert_sort: bool
    """ Invert sort order of dopesheet channels

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
