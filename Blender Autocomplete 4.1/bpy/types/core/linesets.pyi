import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .freestyle_line_set import FreestyleLineSet
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Linesets(bpy_prop_collection[FreestyleLineSet], bpy_struct):
    """Line sets for associating lines and style parameters"""

    active: FreestyleLineSet
    """ Active line set being displayed

    :type: FreestyleLineSet
    """

    active_index: int | None
    """ Index of active line set slot

    :type: int | None
    """

    def new(self, name: str | typing.Any) -> FreestyleLineSet:
        """Add a line set to scene render layer Freestyle settings

        :param name: New name for the line set (not unique)
        :type name: str | typing.Any
        :return: Newly created line set
        :rtype: FreestyleLineSet
        """
        ...

    def remove(self, lineset: FreestyleLineSet):
        """Remove a line set from scene render layer Freestyle settings

        :param lineset: Line set to remove
        :type lineset: FreestyleLineSet
        """
        ...

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
