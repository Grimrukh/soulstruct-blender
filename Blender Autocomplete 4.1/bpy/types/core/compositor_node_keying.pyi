import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .node_internal_socket_template import NodeInternalSocketTemplate
from .node import Node
from .compositor_node import CompositorNode
from .node_internal import NodeInternal

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CompositorNodeKeying(CompositorNode, NodeInternal, Node, bpy_struct):
    blur_post: int
    """ Matte blur size which applies after clipping and dilate/eroding

    :type: int
    """

    blur_pre: int
    """ Chroma pre-blur size which applies before running keyer

    :type: int
    """

    clip_black: float
    """ Value of non-scaled matte pixel which considers as fully background pixel

    :type: float
    """

    clip_white: float
    """ Value of non-scaled matte pixel which considers as fully foreground pixel

    :type: float
    """

    despill_balance: float
    """ Balance between non-key colors used to detect amount of key color to be removed

    :type: float
    """

    despill_factor: float
    """ Factor of despilling screen color from image

    :type: float
    """

    dilate_distance: int
    """ Distance to grow/shrink the matte

    :type: int
    """

    edge_kernel_radius: int
    """ Radius of kernel used to detect whether pixel belongs to edge

    :type: int
    """

    edge_kernel_tolerance: float
    """ Tolerance to pixels inside kernel which are treating as belonging to the same plane

    :type: float
    """

    feather_distance: int
    """ Distance to grow/shrink the feather

    :type: int
    """

    feather_falloff: str
    """ Falloff type the feather

    :type: str
    """

    screen_balance: float
    """ Balance between two non-primary channels primary channel is comparing against

    :type: float
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
