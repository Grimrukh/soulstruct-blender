import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .palette_color import PaletteColor

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class PaletteColors(bpy_prop_collection[PaletteColor], bpy_struct):
    """Collection of palette colors"""

    active: PaletteColor | None
    """ 

    :type: PaletteColor | None
    """

    def new(self) -> PaletteColor:
        """Add a new color to the palette

        :return: The newly created color
        :rtype: PaletteColor
        """
        ...

    def remove(self, color: PaletteColor):
        """Remove a color from the palette

        :param color: The color to remove
        :type color: PaletteColor
        """
        ...

    def clear(self):
        """Remove all colors from the palette"""
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
