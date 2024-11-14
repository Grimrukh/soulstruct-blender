import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .mesh_loop_color import MeshLoopColor

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MeshLoopColorLayer(bpy_struct):
    """Layer of vertex colors in a Mesh data-block"""

    active: bool | None
    """ Sets the layer as active for display and editing

    :type: bool | None
    """

    active_render: bool | None
    """ Sets the layer as active for rendering

    :type: bool | None
    """

    data: bpy_prop_collection[MeshLoopColor]
    """ 

    :type: bpy_prop_collection[MeshLoopColor]
    """

    name: str
    """ Name of Vertex color layer

    :type: str
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
