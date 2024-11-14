import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .vertex_group_element import VertexGroupElement

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MeshVertex(bpy_struct):
    """Vertex in a Mesh data-block"""

    co: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    groups: bpy_prop_collection[VertexGroupElement]
    """ Weights for the vertex groups this vertex is member of

    :type: bpy_prop_collection[VertexGroupElement]
    """

    hide: bool
    """ 

    :type: bool
    """

    index: int
    """ Index of this vertex

    :type: int
    """

    normal: mathutils.Vector
    """ Vertex Normal

    :type: mathutils.Vector
    """

    select: bool
    """ 

    :type: bool
    """

    undeformed_co: mathutils.Vector
    """ For meshes with modifiers applied, the coordinate of the vertex with no deforming modifiers applied, as used for generated texture coordinates

    :type: mathutils.Vector
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
