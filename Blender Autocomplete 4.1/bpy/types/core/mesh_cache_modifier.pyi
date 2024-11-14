import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MeshCacheModifier(Modifier, bpy_struct):
    """Cache Mesh"""

    cache_format: str
    """ 

    :type: str
    """

    deform_mode: str
    """ 

    :type: str
    """

    eval_factor: float
    """ Evaluation time in seconds

    :type: float
    """

    eval_frame: float
    """ The frame to evaluate (starting at 0)

    :type: float
    """

    eval_time: float
    """ Evaluation time in seconds

    :type: float
    """

    factor: float
    """ Influence of the deformation

    :type: float
    """

    filepath: str
    """ Path to external displacements file

    :type: str
    """

    flip_axis: typing.Any
    forward_axis: str
    """ 

    :type: str
    """

    frame_scale: float
    """ Evaluation time in seconds

    :type: float
    """

    frame_start: float
    """ Add this to the start frame

    :type: float
    """

    interpolation: str
    """ 

    :type: str
    """

    invert_vertex_group: bool
    """ Invert vertex group influence

    :type: bool
    """

    play_mode: str
    """ 

    :type: str
    """

    time_mode: str
    """ Method to control playback time

    :type: str
    """

    up_axis: str
    """ 

    :type: str
    """

    vertex_group: str
    """ Name of the Vertex Group which determines the influence of the modifier per point

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
