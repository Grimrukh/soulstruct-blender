import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .line_style_texture_slot import LineStyleTextureSlot

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class LineStyleTextureSlots(bpy_prop_collection[LineStyleTextureSlot], bpy_struct):
    """Collection of texture slots"""

    @classmethod
    def add(cls) -> LineStyleTextureSlot:
        """add

        :return: The newly initialized mtex
        :rtype: LineStyleTextureSlot
        """
        ...

    @classmethod
    def create(cls, index: int | None) -> LineStyleTextureSlot:
        """create

        :param index: Index, Slot index to initialize
        :type index: int | None
        :return: The newly initialized mtex
        :rtype: LineStyleTextureSlot
        """
        ...

    @classmethod
    def clear(cls, index: int | None):
        """clear

        :param index: Index, Slot index to clear
        :type index: int | None
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
