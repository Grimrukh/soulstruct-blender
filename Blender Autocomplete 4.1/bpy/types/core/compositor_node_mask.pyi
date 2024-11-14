import typing
import collections.abc
import mathutils
from .mask import Mask
from .struct import Struct
from .bpy_struct import bpy_struct
from .node_internal_socket_template import NodeInternalSocketTemplate
from .node import Node
from .compositor_node import CompositorNode
from .node_internal import NodeInternal

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CompositorNodeMask(CompositorNode, NodeInternal, Node, bpy_struct):
    mask: Mask
    """ 

    :type: Mask
    """

    motion_blur_samples: int
    """ Number of motion blur samples

    :type: int
    """

    motion_blur_shutter: float
    """ Exposure for motion blur as a factor of FPS

    :type: float
    """

    size_source: str
    """ Where to get the mask size from for aspect/size information

    :type: str
    """

    size_x: int
    """ 

    :type: int
    """

    size_y: int
    """ 

    :type: int
    """

    use_feather: bool
    """ Use feather information from the mask

    :type: bool
    """

    use_motion_blur: bool
    """ Use multi-sampled motion blur of the mask

    :type: bool
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
