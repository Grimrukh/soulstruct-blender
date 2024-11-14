import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .object import Object
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class UVWarpModifier(Modifier, bpy_struct):
    """Add target position to UV coordinates"""

    axis_u: str
    """ Pole axis for rotation

    :type: str
    """

    axis_v: str
    """ Pole axis for rotation

    :type: str
    """

    bone_from: str
    """ Bone defining offset

    :type: str
    """

    bone_to: str
    """ Bone defining offset

    :type: str
    """

    center: bpy_prop_array[float]
    """ Center point for rotate/scale

    :type: bpy_prop_array[float]
    """

    invert_vertex_group: bool
    """ Invert vertex group influence

    :type: bool
    """

    object_from: Object
    """ Object defining offset

    :type: Object
    """

    object_to: Object
    """ Object defining offset

    :type: Object
    """

    offset: bpy_prop_array[float]
    """ 2D Offset for the warp

    :type: bpy_prop_array[float]
    """

    rotation: float
    """ 2D Rotation for the warp

    :type: float
    """

    scale: bpy_prop_array[float]
    """ 2D Scale for the warp

    :type: bpy_prop_array[float]
    """

    uv_layer: str
    """ UV map name

    :type: str
    """

    vertex_group: str
    """ Vertex group name

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
