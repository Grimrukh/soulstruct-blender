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


class CompositorNodeColorCorrection(CompositorNode, NodeInternal, Node, bpy_struct):
    blue: bool
    """ Blue channel active

    :type: bool
    """

    green: bool
    """ Green channel active

    :type: bool
    """

    highlights_contrast: float
    """ Highlights contrast

    :type: float
    """

    highlights_gain: float
    """ Highlights gain

    :type: float
    """

    highlights_gamma: float
    """ Highlights gamma

    :type: float
    """

    highlights_lift: float
    """ Highlights lift

    :type: float
    """

    highlights_saturation: float
    """ Highlights saturation

    :type: float
    """

    master_contrast: float
    """ Master contrast

    :type: float
    """

    master_gain: float
    """ Master gain

    :type: float
    """

    master_gamma: float
    """ Master gamma

    :type: float
    """

    master_lift: float
    """ Master lift

    :type: float
    """

    master_saturation: float
    """ Master saturation

    :type: float
    """

    midtones_contrast: float
    """ Midtones contrast

    :type: float
    """

    midtones_end: float
    """ End of midtones

    :type: float
    """

    midtones_gain: float
    """ Midtones gain

    :type: float
    """

    midtones_gamma: float
    """ Midtones gamma

    :type: float
    """

    midtones_lift: float
    """ Midtones lift

    :type: float
    """

    midtones_saturation: float
    """ Midtones saturation

    :type: float
    """

    midtones_start: float
    """ Start of midtones

    :type: float
    """

    red: bool
    """ Red channel active

    :type: bool
    """

    shadows_contrast: float
    """ Shadows contrast

    :type: float
    """

    shadows_gain: float
    """ Shadows gain

    :type: float
    """

    shadows_gamma: float
    """ Shadows gamma

    :type: float
    """

    shadows_lift: float
    """ Shadows lift

    :type: float
    """

    shadows_saturation: float
    """ Shadows saturation

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
