import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .action_group import ActionGroup

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ActionGroups(bpy_prop_collection[ActionGroup], bpy_struct):
    """Collection of action groups"""

    def new(self, name: str | typing.Any) -> ActionGroup:
        """Create a new action group and add it to the action

        :param name: New name for the action group
        :type name: str | typing.Any
        :return: Newly created action group
        :rtype: ActionGroup
        """
        ...

    def remove(self, action_group: ActionGroup):
        """Remove action group

        :param action_group: Action group to remove
        :type action_group: ActionGroup
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
