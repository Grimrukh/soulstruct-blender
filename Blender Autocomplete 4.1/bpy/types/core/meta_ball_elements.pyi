import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .meta_element import MetaElement

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MetaBallElements(bpy_prop_collection[MetaElement], bpy_struct):
    """Collection of metaball elements"""

    active: MetaElement
    """ Last selected element

    :type: MetaElement
    """

    def new(self, type: str | None = "BALL") -> MetaElement:
        """Add a new element to the metaball

        :param type: Type for the new metaball element
        :type type: str | None
        :return: The newly created metaball element
        :rtype: MetaElement
        """
        ...

    def remove(self, element: MetaElement):
        """Remove an element from the metaball

        :param element: The element to remove
        :type element: MetaElement
        """
        ...

    def clear(self):
        """Remove all elements from the metaball"""
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
