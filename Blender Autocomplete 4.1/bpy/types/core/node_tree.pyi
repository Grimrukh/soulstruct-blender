import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .nodes import Nodes
from .anim_data import AnimData
from .id import ID
from .node_tree_interface import NodeTreeInterface
from .context import Context
from .grease_pencil import GreasePencil
from .node_links import NodeLinks

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class NodeTree(ID, bpy_struct):
    """Node tree consisting of linked nodes used for shading, textures and compositing"""

    animation_data: AnimData
    """ Animation data for this data-block

    :type: AnimData
    """

    bl_description: str
    """ 

    :type: str
    """

    bl_icon: str
    """ The node tree icon

    :type: str
    """

    bl_idname: str
    """ 

    :type: str
    """

    bl_label: str
    """ The node tree label

    :type: str
    """

    grease_pencil: GreasePencil
    """ Grease Pencil data-block

    :type: GreasePencil
    """

    interface: NodeTreeInterface
    """ Interface declaration for this node tree

    :type: NodeTreeInterface
    """

    links: NodeLinks
    """ 

    :type: NodeLinks
    """

    nodes: Nodes
    """ 

    :type: Nodes
    """

    type: str
    """ Node Tree type (deprecated, bl_idname is the actual node tree type identifier)

    :type: str
    """

    view_center: mathutils.Vector
    """ The current location (offset) of the view for this Node Tree

    :type: mathutils.Vector
    """

    def interface_update(self, context: Context):
        """Updated node group interface

        :param context:
        :type context: Context
        """
        ...

    def contains_tree(self, sub_tree: NodeTree) -> bool:
        """Check if the node tree contains another. Used to avoid creating recursive node groups

        :param sub_tree: Node Tree, Node tree for recursive check
        :type sub_tree: NodeTree
        :return: contained
        :rtype: bool
        """
        ...

    @classmethod
    def poll(cls, context: Context) -> bool:
        """Check visibility in the editor

        :param context:
        :type context: Context
        :return:
        :rtype: bool
        """
        ...

    def update(self):
        """Update on editor changes"""
        ...

    @classmethod
    def get_from_context(cls, context: Context):
        """Get a node tree from the context

                :param context:
                :type context: Context
                :return: result_1, Active node tree from context, `NodeTree`

        result_2, ID data-block that owns the node tree, `ID`

        result_3, Original ID data-block selected from the context, `ID`
        """
        ...

    @classmethod
    def valid_socket_type(cls, idname: str | typing.Any) -> bool:
        """Check if the socket type is valid for the node tree

        :param idname: Socket Type, Identifier of the socket type
        :type idname: str | typing.Any
        :return:
        :rtype: bool
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
