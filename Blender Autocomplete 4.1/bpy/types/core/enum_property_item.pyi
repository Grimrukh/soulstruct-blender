import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class EnumPropertyItem(bpy_struct):
    """Definition of a choice in an RNA enum property"""

    description: str
    """ Description of the item's purpose

    :type: str
    """

    icon: str
    """ Icon of the item

    :type: str
    """

    identifier: str
    """ Unique name used in the code and scripting

    :type: str
    """

    name: str
    """ Human readable name

    :type: str
    """

    value: int
    """ Value of the item

    :type: int
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
