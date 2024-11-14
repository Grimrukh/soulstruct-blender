import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .node_geometry_simulation_output_items import NodeGeometrySimulationOutputItems
from .node_internal_socket_template import NodeInternalSocketTemplate
from .node import Node
from .simulation_state_item import SimulationStateItem
from .geometry_node import GeometryNode
from .node_internal import NodeInternal

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class GeometryNodeSimulationOutput(GeometryNode, NodeInternal, Node, bpy_struct):
    """Output data from the simulation zone"""

    active_index: int | None
    """ Index of the active item

    :type: int | None
    """

    active_item: SimulationStateItem | None
    """ Index of the active item

    :type: SimulationStateItem | None
    """

    state_items: NodeGeometrySimulationOutputItems
    """ 

    :type: NodeGeometrySimulationOutputItems
    """

    @classmethod
    def is_registered_node_type(cls) -> bool:
        """True if a registered node type

        :return: Result
        :rtype: bool
        """
        ...

    @classmethod
    def input_template(cls, index: int | None) -> NodeInternalSocketTemplate:
        """Input socket template

        :param index: Index
        :type index: int | None
        :return: result
        :rtype: NodeInternalSocketTemplate
        """
        ...

    @classmethod
    def output_template(cls, index: int | None) -> NodeInternalSocketTemplate:
        """Output socket template

        :param index: Index
        :type index: int | None
        :return: result
        :rtype: NodeInternalSocketTemplate
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
