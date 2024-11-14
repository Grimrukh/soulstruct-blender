import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MeshSkinVertex(bpy_struct):
    """Per-vertex skin data for use with the Skin modifier"""

    radius: bpy_prop_array[float]
    """ Radius of the skin

    :type: bpy_prop_array[float]
    """

    use_loose: bool
    """ If vertex has multiple adjacent edges, it is hulled to them directly

    :type: bool
    """

    use_root: bool
    """ Vertex is a root for rotation calculations and armature generation, setting this flag does not clear other roots in the same mesh island

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
