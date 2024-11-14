import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class NormalEditModifier(Modifier, bpy_struct):
    """Modifier affecting/generating custom normals"""

    invert_vertex_group: bool
    """ Invert vertex group influence

    :type: bool
    """

    mix_factor: float
    """ How much of generated normals to mix with existing ones

    :type: float
    """

    mix_limit: float
    """ Maximum angle between old and new normals

    :type: float
    """

    mix_mode: str
    """ How to mix generated normals with existing ones

    :type: str
    """

    mode: str
    """ How to affect (generate) normals

    :type: str
    """

    no_polynors_fix: bool
    """ Do not flip polygons when their normals are not consistent with their newly computed custom vertex normals

    :type: bool
    """

    offset: mathutils.Vector
    """ Offset from object's center

    :type: mathutils.Vector
    """

    target: Object
    """ Target object used to affect normals

    :type: Object
    """

    use_direction_parallel: bool
    """ Use same direction for all normals, from origin to target's center (Directional mode only)

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
