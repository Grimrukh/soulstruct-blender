import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MeshEdge(bpy_struct):
    """Edge in a Mesh data-block"""

    hide: bool
    """ 

    :type: bool
    """

    index: int
    """ Index of this edge

    :type: int
    """

    is_loose: bool
    """ Edge is not connected to any faces

    :type: bool
    """

    select: bool
    """ 

    :type: bool
    """

    use_edge_sharp: bool
    """ Sharp edge for shading

    :type: bool
    """

    use_freestyle_mark: bool
    """ Edge mark for Freestyle line rendering

    :type: bool
    """

    use_seam: bool
    """ Seam edge for UV unwrapping

    :type: bool
    """

    vertices: bpy_prop_array[int]
    """ Vertex indices

    :type: bpy_prop_array[int]
    """

    key: typing.Any
    """ (readonly)"""

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
