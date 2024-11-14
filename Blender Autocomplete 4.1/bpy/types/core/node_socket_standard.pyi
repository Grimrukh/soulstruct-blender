import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .node_socket import NodeSocket
from .node import Node
from .context import Context
from .ui_layout import UILayout

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class NodeSocketStandard(NodeSocket, bpy_struct):
    links: typing.Any
    """ List of node links from or to this socket.(readonly)"""

    def draw(
        self, context: Context, layout: UILayout, node: Node, text: str | typing.Any
    ):
        """Draw socket

        :param context:
        :type context: Context
        :param layout: Layout, Layout in the UI
        :type layout: UILayout
        :param node: Node, Node the socket belongs to
        :type node: Node
        :param text: Text, Text label to draw alongside properties
        :type text: str | typing.Any
        """
        ...

    def draw_color(self, context: Context, node: Node) -> bpy_prop_array[float]:
        """Color of the socket icon

        :param context:
        :type context: Context
        :param node: Node, Node the socket belongs to
        :type node: Node
        :return: Color
        :rtype: bpy_prop_array[float]
        """
        ...

    @classmethod
    def draw_color_simple(cls) -> bpy_prop_array[float]:
        """Color of the socket icon

        :return: Color
        :rtype: bpy_prop_array[float]
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
