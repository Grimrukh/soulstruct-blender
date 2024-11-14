import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class WeldModifier(Modifier, bpy_struct):
    """Weld modifier"""

    invert_vertex_group: bool
    """ Invert vertex group influence

    :type: bool
    """

    loose_edges: bool
    """ Collapse edges without faces, cloth sewing edges

    :type: bool
    """

    merge_threshold: float
    """ Limit below which to merge vertices

    :type: float
    """

    mode: str
    """ Mode defines the merge rule

    :type: str
    """

    vertex_group: str
    """ Vertex group name for selecting the affected areas

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
