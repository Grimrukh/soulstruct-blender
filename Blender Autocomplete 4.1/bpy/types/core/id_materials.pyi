import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .material import Material

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class IDMaterials(bpy_prop_collection[Material], bpy_struct):
    """Collection of materials"""

    def append(self, material: Material | None):
        """Add a new material to the data-block

        :param material: Material to add
        :type material: Material | None
        """
        ...

    def pop(self, index: typing.Any | None = -1) -> Material:
        """Remove a material from the data-block

        :param index: Index of material to remove
        :type index: typing.Any | None
        :return: Material to remove
        :rtype: Material
        """
        ...

    def clear(self):
        """Remove all materials from the data-block"""
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
