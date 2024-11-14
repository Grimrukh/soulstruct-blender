import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .operator_properties import OperatorProperties

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class KeyMapItem(bpy_struct):
    """Item in a Key Map"""

    active: bool | None
    """ Activate or deactivate item

    :type: bool | None
    """

    alt: int
    """ Alt key pressed, -1 for any state

    :type: int
    """

    alt_ui: bool
    """ Alt key pressed

    :type: bool
    """

    any: bool
    """ Any modifier keys pressed

    :type: bool
    """

    ctrl: int
    """ Control key pressed, -1 for any state

    :type: int
    """

    ctrl_ui: bool
    """ Control key pressed

    :type: bool
    """

    direction: str
    """ The direction (only applies to drag events)

    :type: str
    """

    id: int
    """ ID of the item

    :type: int
    """

    idname: str
    """ Identifier of operator to call on input event

    :type: str
    """

    is_user_defined: bool
    """ Is this keymap item user defined (doesn't just replace a builtin item)

    :type: bool
    """

    is_user_modified: bool
    """ Is this keymap item modified by the user

    :type: bool
    """

    key_modifier: str
    """ Regular key pressed as a modifier

    :type: str
    """

    map_type: str
    """ Type of event mapping

    :type: str
    """

    name: str
    """ Name of operator (translated) to call on input event

    :type: str
    """

    oskey: int
    """ Operating system key pressed, -1 for any state

    :type: int
    """

    oskey_ui: bool
    """ Operating system key pressed

    :type: bool
    """

    properties: OperatorProperties
    """ Properties to set when the operator is called

    :type: OperatorProperties
    """

    propvalue: str
    """ The value this event translates to in a modal keymap

    :type: str
    """

    repeat: bool
    """ Active on key-repeat events (when a key is held)

    :type: bool
    """

    shift: int
    """ Shift key pressed, -1 for any state

    :type: int
    """

    shift_ui: bool
    """ Shift key pressed

    :type: bool
    """

    show_expanded: bool
    """ Show key map event and property details in the user interface

    :type: bool
    """

    type: str
    """ Type of event

    :type: str
    """

    value: str
    """ 

    :type: str
    """

    def compare(self, item: KeyMapItem | None) -> bool:
        """compare

        :param item: Item
        :type item: KeyMapItem | None
        :return: Comparison result
        :rtype: bool
        """
        ...

    def to_string(self, compact: bool | typing.Any | None = False) -> str | typing.Any:
        """to_string

        :param compact: Compact
        :type compact: bool | typing.Any | None
        :return: result
        :rtype: str | typing.Any
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
