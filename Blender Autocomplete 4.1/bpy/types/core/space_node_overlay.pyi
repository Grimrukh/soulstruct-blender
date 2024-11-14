import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SpaceNodeOverlay(bpy_struct):
    """Settings for display of overlays in the Node Editor"""

    preview_shape: str
    """ Preview shape used by the node previews

    :type: str
    """

    show_context_path: bool
    """ Display breadcrumbs for the editor's context

    :type: bool
    """

    show_named_attributes: bool
    """ Show when nodes are using named attributes

    :type: bool
    """

    show_overlays: bool
    """ Display overlays like colored or dashed wires

    :type: bool
    """

    show_previews: bool
    """ Display each node's preview if node is toggled

    :type: bool
    """

    show_timing: bool
    """ Display each node's last execution time

    :type: bool
    """

    show_wire_color: bool
    """ Color node links based on their connected sockets

    :type: bool
    """

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
