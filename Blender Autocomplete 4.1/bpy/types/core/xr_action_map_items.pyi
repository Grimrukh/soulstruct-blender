import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .xr_action_map_item import XrActionMapItem
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class XrActionMapItems(bpy_prop_collection[XrActionMapItem], bpy_struct):
    """Collection of XR action map items"""

    def new(
        self, name: str | typing.Any, replace_existing: bool | None
    ) -> XrActionMapItem:
        """new

        :param name: Name of the action map item
        :type name: str | typing.Any
        :param replace_existing: Replace Existing, Replace any existing item with the same name
        :type replace_existing: bool | None
        :return: Item, Added action map item
        :rtype: XrActionMapItem
        """
        ...

    def new_from_item(self, item: XrActionMapItem) -> XrActionMapItem:
        """new_from_item

        :param item: Item, Item to use as a reference
        :type item: XrActionMapItem
        :return: Item, Added action map item
        :rtype: XrActionMapItem
        """
        ...

    def remove(self, item: XrActionMapItem):
        """remove

        :param item: Item
        :type item: XrActionMapItem
        """
        ...

    def find(self, name: str | typing.Any) -> XrActionMapItem:
        """find

        :param name: Name
        :type name: str | typing.Any
        :return: Item, The action map item with the given name
        :rtype: XrActionMapItem
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
