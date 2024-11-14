import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .index_switch_item import IndexSwitchItem

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class NodeIndexSwitchItems(bpy_prop_collection[IndexSwitchItem], bpy_struct):
    """Collection of index_switch items"""

    def new(self) -> IndexSwitchItem:
        """Add an item at the end

        :return: Item, New item
        :rtype: IndexSwitchItem
        """
        ...

    def remove(self, item: IndexSwitchItem):
        """Remove an item

        :param item: Item, The item to remove
        :type item: IndexSwitchItem
        """
        ...

    def clear(self):
        """Remove all items"""
        ...

    def move(self, from_index: int | None, to_index: int | None):
        """Move an item to another position

        :param from_index: From Index, Index of the item to move
        :type from_index: int | None
        :param to_index: To Index, Target index for the item
        :type to_index: int | None
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
