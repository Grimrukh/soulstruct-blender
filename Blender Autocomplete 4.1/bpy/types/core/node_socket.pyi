import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .node import Node
from .context import Context
from .ui_layout import UILayout

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class NodeSocket(bpy_struct):
    """Input or output socket of a node"""

    bl_idname: str
    """ 

    :type: str
    """

    bl_label: str
    """ Label to display for the socket type in the UI

    :type: str
    """

    bl_subtype_label: str
    """ Label to display for the socket subtype in the UI

    :type: str
    """

    default_value: typing.Any
    """ Default value when nothing is plugged in
    """

    description: str
    """ Socket tooltip

    :type: str
    """

    display_shape: str
    """ Socket shape

    :type: str
    """

    enabled: bool
    """ Enable the socket

    :type: bool
    """

    hide: bool
    """ Hide the socket

    :type: bool
    """

    hide_value: bool
    """ Hide the socket input value

    :type: bool
    """

    identifier: str
    """ Unique identifier for mapping sockets

    :type: str
    """

    is_linked: bool
    """ True if the socket is connected

    :type: bool
    """

    is_multi_input: bool
    """ True if the socket can accept multiple ordered input links

    :type: bool
    """

    is_output: bool
    """ True if the socket is an output, otherwise input

    :type: bool
    """

    is_unavailable: bool
    """ True if the socket is unavailable

    :type: bool
    """

    label: str
    """ Custom dynamic defined socket label

    :type: str
    """

    link_limit: int
    """ Max number of links allowed for this socket

    :type: int
    """

    name: str
    """ Socket name

    :type: str
    """

    node: Node
    """ Node owning this socket

    :type: Node
    """

    show_expanded: bool
    """ Socket links are expanded in the user interface

    :type: bool
    """

    type: str
    """ Data type

    :type: str
    """

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
        """Color of the socket icon. Used to draw sockets in places where the socket does not belong to a node, like the node interface panel. Also used to draw node sockets if draw_color is not defined

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
