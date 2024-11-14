import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .vertex_group_element import VertexGroupElement

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class LatticePoint(bpy_struct):
    """Point in the lattice grid"""

    co: mathutils.Vector
    """ Original undeformed location used to calculate the strength of the deform effect (edit/animate the Deformed Location instead)

    :type: mathutils.Vector
    """

    co_deform: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    groups: bpy_prop_collection[VertexGroupElement]
    """ Weights for the vertex groups this point is member of

    :type: bpy_prop_collection[VertexGroupElement]
    """

    select: bool
    """ Selection status

    :type: bool
    """

    weight_softbody: float
    """ Softbody goal weight

    :type: float
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
