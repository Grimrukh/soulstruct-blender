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


class CompositorNodeTonemap(CompositorNode, NodeInternal, Node, bpy_struct):
    adaptation: float
    """ If 0, global; if 1, based on pixel intensity

    :type: float
    """

    contrast: float
    """ Set to 0 to use estimate from input image

    :type: float
    """

    correction: float
    """ If 0, same for all channels; if 1, each independent

    :type: float
    """

    gamma: float
    """ If not used, set to 1

    :type: float
    """

    intensity: float
    """ If less than zero, darkens image; otherwise, makes it brighter

    :type: float
    """

    key: float
    """ The value the average luminance is mapped to

    :type: float
    """

    offset: float
    """ Normally always 1, but can be used as an extra control to alter the brightness curve

    :type: float
    """

    tonemap_type: str
    """ 

    :type: str
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
