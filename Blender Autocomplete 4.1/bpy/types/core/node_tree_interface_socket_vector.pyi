import typing
import collections.abc
import mathutils
from .node_tree_interface_socket import NodeTreeInterfaceSocket
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .node_socket import NodeSocket
from .node import Node
from .context import Context
from .ui_layout import UILayout
from .node_tree_interface_item import NodeTreeInterfaceItem

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class NodeTreeInterfaceSocketVector(
    NodeTreeInterfaceSocket, NodeTreeInterfaceItem, bpy_struct
):
    """3D vector socket of a node"""

    default_value: bpy_prop_array[float]
    """ Input value used for unconnected socket

    :type: bpy_prop_array[float]
    """

    max_value: float
    """ Maximum value

    :type: float
    """

    min_value: float
    """ Minimum value

    :type: float
    """

    subtype: str
    """ Subtype of the default value

    :type: str
    """

    def draw(self, context: Context, layout: UILayout):
        """Draw interface socket settings

        :param context:
        :type context: Context
        :param layout: Layout, Layout in the UI
        :type layout: UILayout
        """
        ...

    def init_socket(self, node: Node, socket: NodeSocket, data_path: str | typing.Any):
        """Initialize a node socket instance

        :param node: Node, Node of the socket to initialize
        :type node: Node
        :param socket: Socket, Socket to initialize
        :type socket: NodeSocket
        :param data_path: Data Path, Path to specialized socket data
        :type data_path: str | typing.Any
        """
        ...

    def from_socket(self, node: Node, socket: NodeSocket):
        """Setup template parameters from an existing socket

        :param node: Node, Node of the original socket
        :type node: Node
        :param socket: Socket, Original socket
        :type socket: NodeSocket
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
