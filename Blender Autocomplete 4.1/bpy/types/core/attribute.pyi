import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Attribute(bpy_struct):
    """Geometry attribute"""

    data_type: str
    """ Type of data stored in attribute

    :type: str
    """

    domain: str
    """ Domain of the Attribute

    :type: str
    """

    is_internal: bool
    """ The attribute is meant for internal use by Blender

    :type: bool
    """

    is_required: bool
    """ Whether the attribute can be removed or renamed

    :type: bool
    """

    name: str
    """ Name of the Attribute

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
