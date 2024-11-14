import typing
import collections.abc
import mathutils
from .nodes_modifier_panels import NodesModifierPanels
from .struct import Struct
from .nodes_modifier_bakes import NodesModifierBakes
from .bpy_struct import bpy_struct
from .node_tree import NodeTree
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class NodesModifier(Modifier, bpy_struct):
    bake_directory: str
    """ Location on disk where the bake data is stored

    :type: str
    """

    bakes: NodesModifierBakes
    """ 

    :type: NodesModifierBakes
    """

    node_group: NodeTree
    """ Node group that controls what this modifier does

    :type: NodeTree
    """

    open_bake_data_blocks_panel: bool
    """ 

    :type: bool
    """

    open_bake_panel: bool
    """ 

    :type: bool
    """

    open_manage_panel: bool
    """ 

    :type: bool
    """

    open_named_attributes_panel: bool
    """ 

    :type: bool
    """

    open_output_attributes_panel: bool
    """ 

    :type: bool
    """

    panels: NodesModifierPanels
    """ 

    :type: NodesModifierPanels
    """

    show_group_selector: bool
    """ 

    :type: bool
    """

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
