import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .bpy_struct import bpy_struct
from .enum_property_item import EnumPropertyItem
from .property import Property
from .function import Function
from .string_property import StringProperty

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Struct(bpy_struct):
    """RNA structure definition"""

    base: Struct
    """ Struct definition this is derived from

    :type: Struct
    """

    description: str
    """ Description of the Struct's purpose

    :type: str
    """

    functions: bpy_prop_collection[Function]
    """ 

    :type: bpy_prop_collection[Function]
    """

    identifier: str
    """ Unique name used in the code and scripting

    :type: str
    """

    name: str
    """ Human readable name

    :type: str
    """

    name_property: StringProperty
    """ Property that gives the name of the struct

    :type: StringProperty
    """

    nested: Struct
    """ Struct in which this struct is always nested, and to which it logically belongs

    :type: Struct
    """

    properties: bpy_prop_collection[Property]
    """ Properties in the struct

    :type: bpy_prop_collection[Property]
    """

    property_tags: bpy_prop_collection[EnumPropertyItem]
    """ Tags that properties can use to influence behavior

    :type: bpy_prop_collection[EnumPropertyItem]
    """

    translation_context: str
    """ Translation context of the struct's name

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
