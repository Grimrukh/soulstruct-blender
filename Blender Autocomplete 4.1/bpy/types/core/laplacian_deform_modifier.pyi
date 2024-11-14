import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class LaplacianDeformModifier(Modifier, bpy_struct):
    """Mesh deform modifier"""

    invert_vertex_group: bool
    """ Invert vertex group influence

    :type: bool
    """

    is_bind: bool
    """ Whether geometry has been bound to anchors

    :type: bool
    """

    iterations: int
    """ 

    :type: int
    """

    vertex_group: str
    """ Name of Vertex Group which determines Anchors

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
