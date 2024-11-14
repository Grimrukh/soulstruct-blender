import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .node_internal_socket_template import NodeInternalSocketTemplate
from .node import Node
from .image import Image
from .compositor_node import CompositorNode
from .node_internal import NodeInternal

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CompositorNodeImage(CompositorNode, NodeInternal, Node, bpy_struct):
    frame_duration: int
    """ Number of images of a movie to use

    :type: int
    """

    frame_offset: int
    """ Offset the number of the frame to use in the animation

    :type: int
    """

    frame_start: int
    """ Global starting frame of the movie/sequence, assuming first picture has a #1

    :type: int
    """

    has_layers: bool
    """ True if this image has any named layer

    :type: bool
    """

    has_views: bool
    """ True if this image has multiple views

    :type: bool
    """

    image: Image
    """ 

    :type: Image
    """

    layer: str
    """ 

    :type: str
    """

    use_auto_refresh: bool
    """ Always refresh image on frame changes

    :type: bool
    """

    use_cyclic: bool
    """ Cycle the images in the movie

    :type: bool
    """

    use_straight_alpha_output: bool
    """ Put node output buffer to straight alpha instead of premultiplied

    :type: bool
    """

    view: str
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
