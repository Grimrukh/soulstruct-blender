import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .color_ramp_element import ColorRampElement
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ColorRampElements(bpy_prop_collection[ColorRampElement], bpy_struct):
    """Collection of Color Ramp Elements"""

    def new(self, position: float | None) -> ColorRampElement:
        """Add element to Color Ramp

        :param position: Position, Position to add element
        :type position: float | None
        :return: New element
        :rtype: ColorRampElement
        """
        ...

    def remove(self, element: ColorRampElement):
        """Delete element from Color Ramp

        :param element: Element to remove
        :type element: ColorRampElement
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
