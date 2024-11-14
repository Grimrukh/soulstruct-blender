import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .node_internal_socket_template import NodeInternalSocketTemplate
from .node import Node
from .compositor_node import CompositorNode
from .scene import Scene
from .node_internal import NodeInternal

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CompositorNodeDefocus(CompositorNode, NodeInternal, Node, bpy_struct):
    angle: float
    """ Bokeh shape rotation offset

    :type: float
    """

    blur_max: float
    """ Blur limit, maximum CoC radius

    :type: float
    """

    bokeh: str
    """ 

    :type: str
    """

    f_stop: float
    """ Amount of focal blur, 128 (infinity) is perfect focus, half the value doubles the blur radius

    :type: float
    """

    scene: Scene
    """ Scene from which to select the active camera (render scene if undefined)

    :type: Scene
    """

    threshold: float
    """ CoC radius threshold, prevents background bleed on in-focus midground, 0 is disabled

    :type: float
    """

    use_gamma_correction: bool
    """ Enable gamma correction before and after main process

    :type: bool
    """

    use_preview: bool
    """ Enable low quality mode, useful for preview

    :type: bool
    """

    use_zbuffer: bool
    """ Disable when using an image as input instead of actual z-buffer (auto enabled if node not image based, eg. time node)

    :type: bool
    """

    z_scale: float
    """ Scale the Z input when not using a z-buffer, controls maximum blur designated by the color white or input value 1

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
