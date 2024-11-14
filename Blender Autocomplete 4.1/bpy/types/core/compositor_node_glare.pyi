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


class CompositorNodeGlare(CompositorNode, NodeInternal, Node, bpy_struct):
    angle_offset: float
    """ Streak angle offset

    :type: float
    """

    color_modulation: float
    """ Amount of Color Modulation, modulates colors of streaks and ghosts for a spectral dispersion effect

    :type: float
    """

    fade: float
    """ Streak fade-out factor

    :type: float
    """

    glare_type: str
    """ 

    :type: str
    """

    iterations: int
    """ 

    :type: int
    """

    mix: float
    """ -1 is original image only, 0 is exact 50/50 mix, 1 is processed image only

    :type: float
    """

    quality: str
    """ If not set to high quality, the effect will be applied to a low-res copy of the source image

    :type: str
    """

    size: int
    """ Glow/glare size (not actual size; relative to initial size of bright area of pixels)

    :type: int
    """

    streaks: int
    """ Total number of streaks

    :type: int
    """

    threshold: float
    """ The glare filter will only be applied to pixels brighter than this value

    :type: float
    """

    use_rotate_45: bool
    """ Simple star filter: add 45 degree rotation offset

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
