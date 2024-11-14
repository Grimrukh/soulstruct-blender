import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .node import Node
from .context import Context
from .ui_layout import UILayout
from .node_tree import NodeTree

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class NodeInternal(Node, bpy_struct):
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
