import typing
import collections.abc
import mathutils
from .compositor_node_output_file_file_slots import CompositorNodeOutputFileFileSlots
from .image_format_settings import ImageFormatSettings
from .struct import Struct
from .compositor_node_output_file_layer_slots import CompositorNodeOutputFileLayerSlots
from .bpy_struct import bpy_struct
from .node_internal_socket_template import NodeInternalSocketTemplate
from .node import Node
from .compositor_node import CompositorNode
from .node_internal import NodeInternal

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CompositorNodeOutputFile(CompositorNode, NodeInternal, Node, bpy_struct):
    active_input_index: int | None
    """ Active input index in details view list

    :type: int | None
    """

    base_path: str
    """ Base output path for the image

    :type: str
    """

    file_slots: CompositorNodeOutputFileFileSlots
    """ 

    :type: CompositorNodeOutputFileFileSlots
    """

    format: ImageFormatSettings
    """ 

    :type: ImageFormatSettings
    """

    layer_slots: CompositorNodeOutputFileLayerSlots
    """ 

    :type: CompositorNodeOutputFileLayerSlots
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

    def update(self): ...
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
