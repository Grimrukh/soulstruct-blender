import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .key_map_item import KeyMapItem
from .bpy_struct import bpy_struct
from .operator_properties import OperatorProperties
from .event import Event

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class KeyMapItems(bpy_prop_collection[KeyMapItem], bpy_struct):
    """Collection of keymap items"""

    def new(
        self,
        idname: str | typing.Any,
        type: str | None,
        value: str | None,
        any: bool | typing.Any | None = False,
        shift: typing.Any | None = 0,
        ctrl: typing.Any | None = 0,
        alt: typing.Any | None = 0,
        oskey: typing.Any | None = 0,
        key_modifier: str | None = "NONE",
        direction: str | None = "ANY",
        repeat: bool | typing.Any | None = False,
        head: bool | typing.Any | None = False,
    ) -> KeyMapItem:
        """new

        :param idname: Operator Identifier
        :type idname: str | typing.Any
        :param type: Type
        :type type: str | None
        :param value: Value
        :type value: str | None
        :param any: Any
        :type any: bool | typing.Any | None
        :param shift: Shift
        :type shift: typing.Any | None
        :param ctrl: Ctrl
        :type ctrl: typing.Any | None
        :param alt: Alt
        :type alt: typing.Any | None
        :param oskey: OS Key
        :type oskey: typing.Any | None
        :param key_modifier: Key Modifier
        :type key_modifier: str | None
        :param direction: Direction
        :type direction: str | None
        :param repeat: Repeat, When set, accept key-repeat events
        :type repeat: bool | typing.Any | None
        :param head: At Head, Force item to be added at start (not end) of key map so that it doesn't get blocked by an existing key map item
        :type head: bool | typing.Any | None
        :return: Item, Added key map item
        :rtype: KeyMapItem
        """
        ...

    def new_modal(
        self,
        propvalue: str | typing.Any,
        type: str | None,
        value: str | None,
        any: bool | typing.Any | None = False,
        shift: typing.Any | None = 0,
        ctrl: typing.Any | None = 0,
        alt: typing.Any | None = 0,
        oskey: typing.Any | None = 0,
        key_modifier: str | None = "NONE",
        direction: str | None = "ANY",
        repeat: bool | typing.Any | None = False,
    ) -> KeyMapItem:
        """new_modal

        :param propvalue: Property Value
        :type propvalue: str | typing.Any
        :param type: Type
        :type type: str | None
        :param value: Value
        :type value: str | None
        :param any: Any
        :type any: bool | typing.Any | None
        :param shift: Shift
        :type shift: typing.Any | None
        :param ctrl: Ctrl
        :type ctrl: typing.Any | None
        :param alt: Alt
        :type alt: typing.Any | None
        :param oskey: OS Key
        :type oskey: typing.Any | None
        :param key_modifier: Key Modifier
        :type key_modifier: str | None
        :param direction: Direction
        :type direction: str | None
        :param repeat: Repeat, When set, accept key-repeat events
        :type repeat: bool | typing.Any | None
        :return: Item, Added key map item
        :rtype: KeyMapItem
        """
        ...

    def new_from_item(
        self, item: KeyMapItem, head: bool | typing.Any | None = False
    ) -> KeyMapItem:
        """new_from_item

        :param item: Item, Item to use as a reference
        :type item: KeyMapItem
        :param head: At Head
        :type head: bool | typing.Any | None
        :return: Item, Added key map item
        :rtype: KeyMapItem
        """
        ...

    def remove(self, item: KeyMapItem):
        """remove

        :param item: Item
        :type item: KeyMapItem
        """
        ...

    def from_id(self, id: int | None) -> KeyMapItem:
        """from_id

        :param id: id, ID of the item
        :type id: int | None
        :return: Item
        :rtype: KeyMapItem
        """
        ...

    def find_from_operator(
        self,
        idname: str | typing.Any,
        properties: OperatorProperties | None = None,
        include: typing.Any | None = {"ACTIONZONE", "KEYBOARD", "MOUSE", "NDOF"},
        exclude: typing.Any | None = {},
    ) -> KeyMapItem:
        """find_from_operator

        :param idname: Operator Identifier
        :type idname: str | typing.Any
        :param properties:
        :type properties: OperatorProperties | None
        :param include: Include
        :type include: typing.Any | None
        :param exclude: Exclude
        :type exclude: typing.Any | None
        :return:
        :rtype: KeyMapItem
        """
        ...

    def match_event(self, event: Event | None) -> KeyMapItem:
        """match_event

        :param event:
        :type event: Event | None
        :return:
        :rtype: KeyMapItem
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
