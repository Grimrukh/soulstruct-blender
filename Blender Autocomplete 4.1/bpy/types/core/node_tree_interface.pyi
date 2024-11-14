import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .node_tree_interface_socket import NodeTreeInterfaceSocket
from .struct import Struct
from .node_tree_interface_panel import NodeTreeInterfacePanel
from .bpy_struct import bpy_struct
from .node_tree_interface_item import NodeTreeInterfaceItem

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class NodeTreeInterface(bpy_struct):
    """Declaration of sockets and ui panels of a node group"""

    active: NodeTreeInterfaceItem | None
    """ Active item

    :type: NodeTreeInterfaceItem | None
    """

    active_index: int | None
    """ Index of the active item

    :type: int | None
    """

    items_tree: bpy_prop_collection[NodeTreeInterfaceItem]
    """ Items in the node interface

    :type: bpy_prop_collection[NodeTreeInterfaceItem]
    """

    def new_socket(
        self,
        name: str | typing.Any,
        description: str | typing.Any = "",
        in_out: str | None = "INPUT",
        socket_type: str | None = "DEFAULT",
        parent: NodeTreeInterfacePanel | None = None,
    ) -> NodeTreeInterfaceSocket:
        """Add a new socket to the interface

                :param name: Name, Name of the socket
                :type name: str | typing.Any
                :param description: Description, Description of the socket
                :type description: str | typing.Any
                :param in_out: Input/Output Type, Create an input or output socket

        INPUT
        Input -- Generate a input node socket.

        OUTPUT
        Output -- Generate a output node socket.
                :type in_out: str | None
                :param socket_type: Socket Type, Type of socket generated on nodes
                :type socket_type: str | None
                :param parent: Parent, Panel to add the socket in
                :type parent: NodeTreeInterfacePanel | None
                :return: Socket, New socket
                :rtype: NodeTreeInterfaceSocket
        """
        ...

    def new_panel(
        self,
        name: str | typing.Any,
        description: str | typing.Any = "",
        default_closed: bool | typing.Any | None = False,
        parent: NodeTreeInterfacePanel | None = None,
    ) -> NodeTreeInterfacePanel:
        """Add a new panel to the interface

        :param name: Name, Name of the new panel
        :type name: str | typing.Any
        :param description: Description, Description of the panel
        :type description: str | typing.Any
        :param default_closed: Default Closed, Panel is closed by default on new nodes
        :type default_closed: bool | typing.Any | None
        :param parent: Parent, Add panel as a child of the parent panel
        :type parent: NodeTreeInterfacePanel | None
        :return: Panel, New panel
        :rtype: NodeTreeInterfacePanel
        """
        ...

    def copy(self, item: NodeTreeInterfaceItem) -> NodeTreeInterfaceItem:
        """Add a copy of an item to the interface

        :param item: Item, Item to copy
        :type item: NodeTreeInterfaceItem
        :return: Item Copy, Copy of the item
        :rtype: NodeTreeInterfaceItem
        """
        ...

    def remove(
        self,
        item: NodeTreeInterfaceItem,
        move_content_to_parent: bool | typing.Any | None = True,
    ):
        """Remove an item from the interface

        :param item: Item, The item to remove
        :type item: NodeTreeInterfaceItem
        :param move_content_to_parent: Move Content, If the item is a panel, move the contents to the parent instead of deleting it
        :type move_content_to_parent: bool | typing.Any | None
        """
        ...

    def clear(self):
        """Remove all items from the interface"""
        ...

    def move(self, item: NodeTreeInterfaceItem, to_position: int | None):
        """Move an item to another position

        :param item: Item, The item to move
        :type item: NodeTreeInterfaceItem
        :param to_position: To Position, Target position for the item in its current panel
        :type to_position: int | None
        """
        ...

    def move_to_parent(
        self,
        item: NodeTreeInterfaceItem,
        parent: NodeTreeInterfacePanel | None,
        to_position: int | None,
    ):
        """Move an item to a new panel and/or position.

        :param item: Item, The item to move
        :type item: NodeTreeInterfaceItem
        :param parent: Parent, New parent of the item
        :type parent: NodeTreeInterfacePanel | None
        :param to_position: To Position, Target position for the item in the new parent panel
        :type to_position: int | None
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
