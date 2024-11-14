import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .key_map import KeyMap
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class KeyMaps(bpy_prop_collection[KeyMap], bpy_struct):
    """Collection of keymaps"""

    def new(
        self,
        name: str | typing.Any,
        space_type: str | None = "EMPTY",
        region_type: str | None = "WINDOW",
        modal: bool | typing.Any | None = False,
        tool: bool | typing.Any | None = False,
    ) -> KeyMap:
        """Ensure the keymap exists. This will return the one with the given name/space type/region type, or create a new one if it does not exist yet.

        :param name: Name
        :type name: str | typing.Any
        :param space_type: Space Type
        :type space_type: str | None
        :param region_type: Region Type
        :type region_type: str | None
        :param modal: Modal, Keymap for modal operators
        :type modal: bool | typing.Any | None
        :param tool: Tool, Keymap for active tools
        :type tool: bool | typing.Any | None
        :return: Key Map, Added key map
        :rtype: KeyMap
        """
        ...

    def remove(self, keymap: KeyMap):
        """remove

        :param keymap: Key Map, Removed key map
        :type keymap: KeyMap
        """
        ...

    def clear(self):
        """Remove all keymaps."""
        ...

    def find(
        self,
        name: str | typing.Any,
        space_type: str | None = "EMPTY",
        region_type: str | None = "WINDOW",
    ) -> KeyMap:
        """find

        :param name: Name
        :type name: str | typing.Any
        :param space_type: Space Type
        :type space_type: str | None
        :param region_type: Region Type
        :type region_type: str | None
        :return: Key Map, Corresponding key map
        :rtype: KeyMap
        """
        ...

    def find_modal(self, name: str | typing.Any) -> KeyMap:
        """find_modal

        :param name: Operator Name
        :type name: str | typing.Any
        :return: Key Map, Corresponding key map
        :rtype: KeyMap
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
