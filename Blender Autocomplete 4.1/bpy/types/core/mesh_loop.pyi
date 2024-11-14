import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MeshLoop(bpy_struct):
    """Loop in a Mesh data-block"""

    bitangent: mathutils.Vector
    """ Bitangent vector of this vertex for this face (must be computed beforehand using calc_tangents, use it only if really needed, slower access than bitangent_sign)

    :type: mathutils.Vector
    """

    bitangent_sign: float
    """ Sign of the bitangent vector of this vertex for this face (must be computed beforehand using calc_tangents, bitangent = bitangent_sign * cross(normal, tangent))

    :type: float
    """

    edge_index: int
    """ Edge index

    :type: int
    """

    index: int
    """ Index of this loop

    :type: int
    """

    normal: mathutils.Vector
    """ The normal direction of the face corner, taking into account sharp faces, sharp edges, and custom normal data

    :type: mathutils.Vector
    """

    tangent: mathutils.Vector
    """ Local space unit length tangent vector of this vertex for this face (must be computed beforehand using calc_tangents)

    :type: mathutils.Vector
    """

    vertex_index: int
    """ Vertex index

    :type: int
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
