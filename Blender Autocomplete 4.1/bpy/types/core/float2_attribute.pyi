import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .attribute import Attribute
from .struct import Struct
from .bpy_struct import bpy_struct
from .float2_attribute_value import Float2AttributeValue

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Float2Attribute(Attribute, bpy_struct):
    """Geometry attribute that stores floating-point 2D vectors"""

    data: bpy_prop_collection[Float2AttributeValue]
    """ 

    :type: bpy_prop_collection[Float2AttributeValue]
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
