import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class VertexGroup(bpy_struct):
    """Group of vertices, used for armature deform and other purposes"""

    index: int
    """ Index number of the vertex group

    :type: int
    """

    lock_weight: bool
    """ Maintain the relative weights for the group

    :type: bool
    """

    name: str
    """ Vertex group name

    :type: str
    """

    def add(
        self,
        index: collections.abc.Iterable[int] | None,
        weight: float | None,
        type: str | None,
    ):
        """Add vertices to the group

                :param index: List of indices
                :type index: collections.abc.Iterable[int] | None
                :param weight: Vertex weight
                :type weight: float | None
                :param type: Vertex assign mode

        REPLACE
        Replace -- Replace.

        ADD
        Add -- Add.

        SUBTRACT
        Subtract -- Subtract.
                :type type: str | None
        """
        ...

    def remove(self, index: collections.abc.Iterable[int] | None):
        """Remove vertices from the group

        :param index: List of indices
        :type index: collections.abc.Iterable[int] | None
        """
        ...

    def weight(self, index: int | None) -> float:
        """Get a vertex weight from the group

        :param index: Index, The index of the vertex
        :type index: int | None
        :return: Vertex weight
        :rtype: float
        """
        ...

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
