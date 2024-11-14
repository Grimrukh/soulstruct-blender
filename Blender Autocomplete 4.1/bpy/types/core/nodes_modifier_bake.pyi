import typing
import collections.abc
import mathutils
from .struct import Struct
from .nodes_modifier_bake_data_blocks import NodesModifierBakeDataBlocks
from .bpy_struct import bpy_struct
from .node import Node

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class NodesModifierBake(bpy_struct):
    bake_id: int
    """ Identifier for this bake which remains unchanged even when the bake node is renamed, grouped or ungrouped

    :type: int
    """

    bake_mode: str
    """ 

    :type: str
    """

    data_blocks: NodesModifierBakeDataBlocks
    """ 

    :type: NodesModifierBakeDataBlocks
    """

    directory: str
    """ Location on disk where the bake data is stored

    :type: str
    """

    frame_end: int
    """ Frame where the baking ends

    :type: int
    """

    frame_start: int
    """ Frame where the baking starts

    :type: int
    """

    node: Node
    """ Bake node or simulation output node that corresponds to this bake. This node may be deeply nested in the modifier node group. It can be none in some cases like missing linked data blocks

    :type: Node
    """

    use_custom_path: bool
    """ Specify a path where the baked data should be stored manually

    :type: bool
    """

    use_custom_simulation_frame_range: bool
    """ Override the simulation frame range from the scene

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
