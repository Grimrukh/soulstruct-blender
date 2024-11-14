import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class NodeGeometryBakeItem(bpy_struct):
    attribute_domain: str
    """ Attribute domain where the attribute is stored in the baked data

    :type: str
    """

    color: bpy_prop_array[float]
    """ Color of the corresponding socket type in the node editor

    :type: bpy_prop_array[float]
    """

    is_attribute: bool
    """ Bake item is an attribute stored on a geometry

    :type: bool
    """

    name: str
    """ 

    :type: str
    """

    socket_type: str
    """ 

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
