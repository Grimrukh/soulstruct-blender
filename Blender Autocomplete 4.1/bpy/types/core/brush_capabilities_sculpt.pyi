import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BrushCapabilitiesSculpt(bpy_struct):
    """Read-only indications of which brush operations are supported by the current sculpt tool"""

    has_accumulate: bool
    """ 

    :type: bool
    """

    has_auto_smooth: bool
    """ 

    :type: bool
    """

    has_color: bool
    """ 

    :type: bool
    """

    has_direction: bool
    """ 

    :type: bool
    """

    has_gravity: bool
    """ 

    :type: bool
    """

    has_height: bool
    """ 

    :type: bool
    """

    has_jitter: bool
    """ 

    :type: bool
    """

    has_normal_weight: bool
    """ 

    :type: bool
    """

    has_persistence: bool
    """ 

    :type: bool
    """

    has_pinch_factor: bool
    """ 

    :type: bool
    """

    has_plane_offset: bool
    """ 

    :type: bool
    """

    has_rake_factor: bool
    """ 

    :type: bool
    """

    has_random_texture_angle: bool
    """ 

    :type: bool
    """

    has_sculpt_plane: bool
    """ 

    :type: bool
    """

    has_secondary_color: bool
    """ 

    :type: bool
    """

    has_smooth_stroke: bool
    """ 

    :type: bool
    """

    has_space_attenuation: bool
    """ 

    :type: bool
    """

    has_strength_pressure: bool
    """ 

    :type: bool
    """

    has_tilt: bool
    """ 

    :type: bool
    """

    has_topology_rake: bool
    """ 

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
