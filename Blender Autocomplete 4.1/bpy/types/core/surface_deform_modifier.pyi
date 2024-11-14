import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SurfaceDeformModifier(Modifier, bpy_struct):
    falloff: float
    """ Controls how much nearby polygons influence deformation

    :type: float
    """

    invert_vertex_group: bool
    """ Invert vertex group influence

    :type: bool
    """

    is_bound: bool
    """ Whether geometry has been bound to target mesh

    :type: bool
    """

    strength: float
    """ Strength of modifier deformations

    :type: float
    """

    target: Object
    """ Mesh object to deform with

    :type: Object
    """

    use_sparse_bind: bool
    """ Only record binding data for vertices matching the vertex group at the time of bind

    :type: bool
    """

    vertex_group: str
    """ Vertex group name for selecting/weighting the affected areas

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
