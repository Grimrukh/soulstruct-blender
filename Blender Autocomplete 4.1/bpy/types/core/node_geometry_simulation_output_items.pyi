import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .simulation_state_item import SimulationStateItem

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class NodeGeometrySimulationOutputItems(
    bpy_prop_collection[SimulationStateItem], bpy_struct
):
    """Collection of simulation items"""

    def new(
        self, socket_type: str | None, name: str | typing.Any
    ) -> SimulationStateItem:
        """Add an item at the end

        :param socket_type: Socket Type, Socket type of the item
        :type socket_type: str | None
        :param name: Name
        :type name: str | typing.Any
        :return: Item, New item
        :rtype: SimulationStateItem
        """
        ...

    def remove(self, item: SimulationStateItem):
        """Remove an item

        :param item: Item, The item to remove
        :type item: SimulationStateItem
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
