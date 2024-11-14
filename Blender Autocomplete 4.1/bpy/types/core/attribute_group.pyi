import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .attribute import Attribute
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class AttributeGroup(bpy_prop_collection[Attribute], bpy_struct):
    """Group of geometry attributes"""

    active: Attribute | None
    """ Active attribute

    :type: Attribute | None
    """

    active_color: Attribute | None
    """ Active color attribute for display and editing

    :type: Attribute | None
    """

    active_color_index: int | None
    """ Active color attribute index

    :type: int | None
    """

    active_color_name: str
    """ The name of the active color attribute for display and editing

    :type: str
    """

    active_index: int | None
    """ Active attribute index

    :type: int | None
    """

    default_color_name: str
    """ The name of the default color attribute used as a fallback for rendering

    :type: str
    """

    render_color_index: int
    """ The index of the color attribute used as a fallback for rendering

    :type: int
    """

    def new(
        self, name: str | typing.Any, type: str | None, domain: str | None
    ) -> Attribute:
        """Add attribute to geometry

        :param name: Name, Name of geometry attribute
        :type name: str | typing.Any
        :param type: Type, Attribute type
        :type type: str | None
        :param domain: Domain, Type of element that attribute is stored on
        :type domain: str | None
        :return: New geometry attribute
        :rtype: Attribute
        """
        ...

    def remove(self, attribute: Attribute):
        """Remove attribute from geometry

        :param attribute: Geometry Attribute
        :type attribute: Attribute
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
