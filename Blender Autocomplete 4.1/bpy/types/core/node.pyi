import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .ui_layout import UILayout
from .struct import Struct
from .bpy_struct import bpy_struct
from .node_outputs import NodeOutputs
from .node_inputs import NodeInputs
from .context import Context
from .node_link import NodeLink
from .node_tree import NodeTree

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Node(bpy_struct):
    """Node in a node tree"""

    attribute_name: str
    """
    
    :type: str
    """

    bl_description: str
    """ 

    :type: str
    """

    bl_height_default: float
    """ 

    :type: float
    """

    bl_height_max: float
    """ 

    :type: float
    """

    bl_height_min: float
    """ 

    :type: float
    """

    bl_icon: str
    """ The node icon

    :type: str
    """

    bl_idname: str
    """ 

    :type: str
    """

    bl_label: str
    """ The node label

    :type: str
    """

    bl_static_type: str
    """ Node type (deprecated, use with care)

    :type: str
    """

    bl_width_default: float
    """ 

    :type: float
    """

    bl_width_max: float
    """ 

    :type: float
    """

    bl_width_min: float
    """ 

    :type: float
    """

    color: mathutils.Color
    """ Custom color of the node body

    :type: mathutils.Color
    """

    dimensions: mathutils.Vector
    """ Absolute bounding box dimensions of the node

    :type: mathutils.Vector
    """

    height: float
    """ Height of the node

    :type: float
    """

    hide: bool
    """ 

    :type: bool
    """

    inputs: NodeInputs
    """ 

    :type: NodeInputs
    """

    internal_links: bpy_prop_collection[NodeLink]
    """ Internal input-to-output connections for muting

    :type: bpy_prop_collection[NodeLink]
    """

    label: str
    """ Optional custom node label

    :type: str
    """

    location: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    mute: bool
    """ 

    :type: bool
    """

    name: str
    """ Unique node identifier

    :type: str
    """

    outputs: NodeOutputs
    """ 

    :type: NodeOutputs
    """

    parent: Node
    """ Parent this node is attached to

    :type: Node
    """

    select: bool
    """ Node selection state

    :type: bool
    """

    show_options: bool
    """ 

    :type: bool
    """

    show_preview: bool
    """ 

    :type: bool
    """

    show_texture: bool
    """ Display node in viewport textured shading mode

    :type: bool
    """

    type: str
    """ Node type (deprecated, use bl_static_type or bl_idname for the actual identifier string)

    :type: str
    """

    use_custom_color: bool
    """ Use custom color for the node

    :type: bool
    """

    width: float
    """ Width of the node

    :type: float
    """

    def socket_value_update(self, context: Context):
        """Update after property changes

        :param context:
        :type context: Context
        """
        ...

    @classmethod
    def is_registered_node_type(cls) -> bool:
        """True if a registered node type

        :return: Result
        :rtype: bool
        """
        ...

    @classmethod
    def poll(cls, node_tree: NodeTree | None) -> bool:
        """If non-null output is returned, the node type can be added to the tree

        :param node_tree: Node Tree
        :type node_tree: NodeTree | None
        :return:
        :rtype: bool
        """
        ...

    def poll_instance(self, node_tree: NodeTree | None) -> bool:
        """If non-null output is returned, the node can be added to the tree

        :param node_tree: Node Tree
        :type node_tree: NodeTree | None
        :return:
        :rtype: bool
        """
        ...

    def update(self):
        """Update on node graph topology changes (adding or removing nodes and links)"""
        ...

    def insert_link(self, link: NodeLink):
        """Handle creation of a link to or from the node

        :param link: Link, Node link that will be inserted
        :type link: NodeLink
        """
        ...

    def init(self, context: Context):
        """Initialize a new instance of this node

        :param context:
        :type context: Context
        """
        ...

    def copy(self, node: Node):
        """Initialize a new instance of this node from an existing node

        :param node: Node, Existing node to copy
        :type node: Node
        """
        ...

    def free(self):
        """Clean up node on removal"""
        ...

    def draw_buttons(self, context: Context, layout: UILayout):
        """Draw node buttons

        :param context:
        :type context: Context
        :param layout: Layout, Layout in the UI
        :type layout: UILayout
        """
        ...

    def draw_buttons_ext(self, context: Context, layout: UILayout):
        """Draw node buttons in the sidebar

        :param context:
        :type context: Context
        :param layout: Layout, Layout in the UI
        :type layout: UILayout
        """
        ...

    def draw_label(self) -> str | typing.Any:
        """Returns a dynamic label string

        :return: Label
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
