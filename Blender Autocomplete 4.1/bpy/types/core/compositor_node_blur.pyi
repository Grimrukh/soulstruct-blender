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


class CompositorNodeBlur(CompositorNode, NodeInternal, Node, bpy_struct):
    aspect_correction: str
    """ Type of aspect correction to use

    :type: str
    """

    factor: float
    """ 

    :type: float
    """

    factor_x: float
    """ 

    :type: float
    """

    factor_y: float
    """ 

    :type: float
    """

    filter_type: str
    """ 

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

    use_bokeh: bool
    """ Use circular filter (slower)

    :type: bool
    """

    use_extended_bounds: bool
    """ Extend bounds of the input image to fully fit blurred image

    :type: bool
    """

    use_gamma_correction: bool
    """ Apply filter on gamma corrected values

    :type: bool
    """

    use_relative: bool
    """ Use relative (percent) values to define blur radius

    :type: bool
    """

    use_variable_size: bool
    """ Support variable blur per pixel when using an image for size input

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
