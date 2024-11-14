import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .enum_property_item import EnumPropertyItem
from .property import Property

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class EnumProperty(Property, bpy_struct):
    """RNA enumeration property definition, to choose from a number of predefined options"""

    default: str
    """ Default value for this enum

    :type: str
    """

    default_flag: set[str]
    """ Default value for this enum

    :type: set[str]
    """

    enum_items: bpy_prop_collection[EnumPropertyItem]
    """ Possible values for the property

    :type: bpy_prop_collection[EnumPropertyItem]
    """

    enum_items_static: bpy_prop_collection[EnumPropertyItem]
    """ Possible values for the property (never calls optional dynamic generation of those)

    :type: bpy_prop_collection[EnumPropertyItem]
    """

    enum_items_static_ui: bpy_prop_collection[EnumPropertyItem]
    """ Possible values for the property (never calls optional dynamic generation of those). Includes UI elements (separators and section headings)

    :type: bpy_prop_collection[EnumPropertyItem]
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
