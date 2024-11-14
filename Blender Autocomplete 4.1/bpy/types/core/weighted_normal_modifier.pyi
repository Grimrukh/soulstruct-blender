import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class WeightedNormalModifier(Modifier, bpy_struct):
    invert_vertex_group: bool
    """ Invert vertex group influence

    :type: bool
    """

    keep_sharp: bool
    """ Keep sharp edges as computed for default split normals, instead of setting a single weighted normal for each vertex

    :type: bool
    """

    mode: str
    """ Weighted vertex normal mode to use

    :type: str
    """

    thresh: float
    """ Threshold value for different weights to be considered equal

    :type: float
    """

    use_face_influence: bool
    """ Use influence of face for weighting

    :type: bool
    """

    vertex_group: str
    """ Vertex group name for modifying the selected areas

    :type: str
    """

    weight: int
    """ Corrective factor applied to faces' weights, 50 is neutral, lower values increase weight of weak faces, higher values increase weight of strong faces

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
