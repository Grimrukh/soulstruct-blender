import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .key_map_items import KeyMapItems
from .struct import Struct
from .key_map_item import KeyMapItem
from .bpy_struct import bpy_struct
from .enum_property_item import EnumPropertyItem

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class KeyMap(bpy_struct):
    """Input configuration, including keymaps"""

    bl_owner_id: str
    """ Internal owner

    :type: str
    """

    is_modal: bool
    """ Indicates that a keymap is used for translate modal events for an operator

    :type: bool
    """

    is_user_modified: bool
    """ Keymap is defined by the user

    :type: bool
    """

    keymap_items: KeyMapItems
    """ Items in the keymap, linking an operator to an input event

    :type: KeyMapItems
    """

    modal_event_values: bpy_prop_collection[EnumPropertyItem]
    """ Give access to the possible event values of this modal keymap's items (#KeyMapItem.propvalue), for API introspection

    :type: bpy_prop_collection[EnumPropertyItem]
    """

    name: str
    """ Name of the key map

    :type: str
    """

    region_type: str
    """ Optional region type keymap is associated with

    :type: str
    """

    show_expanded_children: bool
    """ Children expanded in the user interface

    :type: bool
    """

    show_expanded_items: bool
    """ Expanded in the user interface

    :type: bool
    """

    space_type: str
    """ Optional space type keymap is associated with

    :type: str
    """

    def active(self) -> KeyMap:
        """active

        :return: Key Map, Active key map
        :rtype: KeyMap
        """
        ...

    def restore_to_default(self):
        """restore_to_default"""
        ...

    def restore_item_to_default(self, item: KeyMapItem):
        """restore_item_to_default

        :param item: Item
        :type item: KeyMapItem
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
